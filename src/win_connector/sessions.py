from __future__ import annotations

import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

from win_connector.models import ConnectResult, ConnectionProfile, Protocol, RDPConfig, SSHConfig, SerialConfig, TelnetConfig

logger = logging.getLogger(__name__)


class DependencyError(RuntimeError):
    pass


@dataclass
class SessionWindowHooks:
    append_output: callable
    is_alive: callable


def _require_paramiko():
    try:
        import paramiko  # type: ignore
    except ImportError as exc:
        raise DependencyError("paramiko is required for SSH connections") from exc
    return paramiko


def _require_serial():
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise DependencyError("pyserial is required for serial connections") from exc
    return serial


def open_rdp_external(profile: ConnectionProfile) -> ConnectResult:
    config = profile.protocol_config
    assert isinstance(config, RDPConfig)
    host_spec = config.host if config.port == 3389 else f"{config.host}:{config.port}"
    if os.name == "nt":
        command = ["mstsc", "/v:" + host_spec]
        subprocess.Popen(command)
        return ConnectResult(
            connection_id=profile.id,
            protocol=profile.protocol,
            mode="external",
            message=f"Started mstsc for {host_spec}",
            command=command,
        )
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="unsupported",
        message="RDP external launch is only supported on Windows",
        command=[],
    )


def open_external_terminal(command: list[str], title: str) -> list[str]:
    if os.name == "nt":
        ps_command = [
            "powershell",
            "-NoProfile",
            "-Command",
            f'Start-Process powershell -ArgumentList \'-NoExit\', \'-Command\', "{subprocess.list2cmdline(command)}" -WindowStyle Normal',
        ]
        subprocess.Popen(ps_command)
        return ps_command
    subprocess.Popen(command)
    return command


def connect_ssh_console(profile: ConnectionProfile) -> ConnectResult:
    paramiko = _require_paramiko()
    config = profile.protocol_config
    assert isinstance(config, SSHConfig)

    if config.open_in_external_terminal and os.name == "nt":
        ssh_cmd = ["ssh", "-p", str(config.port)]
        if config.private_key_path:
            ssh_cmd.extend(["-i", config.private_key_path])
        target = f"{config.username}@{config.host}" if config.username else config.host
        ssh_cmd.append(target)
        started = open_external_terminal(ssh_cmd, profile.name)
        return ConnectResult(
            connection_id=profile.id,
            protocol=profile.protocol,
            mode="external",
            message="Started external SSH terminal",
            command=started,
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": config.host,
        "port": config.port,
        "username": config.username or None,
        "password": config.password or None,
        "timeout": config.timeout_seconds,
        "passphrase": config.passphrase or None,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if config.private_key_path:
        kwargs["key_filename"] = config.private_key_path
    client.connect(**kwargs)
    channel = client.invoke_shell()
    _interactive_console_loop(
        output_reader=lambda size: channel.recv(size),
        input_writer=lambda data: channel.send(data),
        alive=lambda: not channel.closed,
        close=lambda: (channel.close(), client.close()),
    )
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="inline",
        message="SSH session completed",
        command=[],
    )


def connect_telnet_console(profile: ConnectionProfile) -> ConnectResult:
    from telnetlib import Telnet

    config = profile.protocol_config
    assert isinstance(config, TelnetConfig)
    session = Telnet(config.host, config.port, config.timeout_seconds)
    if config.username:
        session.write(config.username.encode("utf-8") + b"\n")
    if config.password:
        session.write(config.password.encode("utf-8") + b"\n")
    _interactive_console_loop(
        output_reader=lambda size: session.read_very_eager(),
        input_writer=lambda data: session.write(data.encode("utf-8")),
        alive=lambda: True,
        close=session.close,
    )
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="inline",
        message="Telnet session completed",
        command=[],
    )


def connect_serial_console(profile: ConnectionProfile) -> ConnectResult:
    serial = _require_serial()
    config = profile.protocol_config
    assert isinstance(config, SerialConfig)
    session = serial.Serial(
        port=config.port_name,
        baudrate=config.baudrate,
        bytesize=config.bytesize,
        parity=config.parity,
        stopbits=config.stopbits,
        timeout=config.timeout_seconds,
    )
    _interactive_console_loop(
        output_reader=lambda size: session.read(size),
        input_writer=lambda data: session.write(data.encode("utf-8")),
        alive=lambda: session.is_open,
        close=session.close,
    )
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="inline",
        message="Serial session completed",
        command=[],
    )


def _interactive_console_loop(output_reader, input_writer, alive, close) -> None:
    stop_event = threading.Event()

    def reader() -> None:
        while not stop_event.is_set() and alive():
            try:
                data = output_reader(4096)
            except Exception:
                break
            if not data:
                continue
            if isinstance(data, bytes):
                text = data.decode("utf-8", errors="replace")
            else:
                text = str(data)
            print(text, end="", flush=True)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        while alive():
            line = input()
            if line.strip().lower() in {"exit", "quit"}:
                break
            input_writer(line + "\n")
    except (EOFError, KeyboardInterrupt):
        logger.info("Console session stopped by user")
    finally:
        stop_event.set()
        close()


def start_gui_session_window(profile: ConnectionProfile, root) -> ConnectResult:
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Toplevel(root)
    window.title(f"{profile.name} [{profile.protocol.value}]")
    window.geometry("900x600")

    text = tk.Text(window, wrap="word")
    text.pack(fill="both", expand=True, padx=8, pady=8)
    entry = ttk.Entry(window)
    entry.pack(fill="x", padx=8, pady=(0, 8))

    state = {"close": lambda: None}

    def append_output(payload: str) -> None:
        text.after(0, lambda: (text.insert("end", payload), text.see("end")))

    try:
        if profile.protocol == Protocol.SSH:
            state["close"] = _start_gui_ssh(profile, append_output, entry)
        elif profile.protocol == Protocol.TELNET:
            state["close"] = _start_gui_telnet(profile, append_output, entry)
        elif profile.protocol == Protocol.SERIAL:
            state["close"] = _start_gui_serial(profile, append_output, entry)
        elif profile.protocol == Protocol.RDP:
            result = open_rdp_external(profile)
            append_output(result.message + "\n")
            return result
        else:
            raise RuntimeError(f"Unsupported protocol: {profile.protocol}")
    except Exception as exc:
        messagebox.showerror("Connection Error", str(exc))
        window.destroy()
        raise

    def submit(_event=None) -> None:
        value = entry.get()
        if not value:
            return
        sender = getattr(entry, "_session_sender", None)
        if sender is not None:
            sender(value + "\n")
        entry.delete(0, "end")

    entry.bind("<Return>", submit)

    def on_close() -> None:
        state["close"]()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="gui",
        message="Session window opened",
        command=[],
    )


def start_gui_session_tab(profile: ConnectionProfile, parent) -> ConnectResult:
    import tkinter as tk
    from tkinter import messagebox, ttk

    text = tk.Text(parent, wrap="word", bg="#050b13", fg="#dff8ff", insertbackground="#22d3ee", relief="flat")
    text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    entry = ttk.Entry(parent)
    entry.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    state = {"close": lambda: None}

    def append_output(payload: str) -> None:
        text.after(0, lambda: (text.insert("end", payload), text.see("end")))

    try:
        if profile.protocol == Protocol.SSH:
            state["close"] = _start_gui_ssh(profile, append_output, entry)
        elif profile.protocol == Protocol.TELNET:
            state["close"] = _start_gui_telnet(profile, append_output, entry)
        elif profile.protocol == Protocol.SERIAL:
            state["close"] = _start_gui_serial(profile, append_output, entry)
        elif profile.protocol == Protocol.RDP:
            result = open_rdp_external(profile)
            append_output(result.message + "\n")
            return result
        else:
            raise RuntimeError(f"Unsupported protocol: {profile.protocol}")
    except Exception as exc:
        messagebox.showerror("Connection Error", str(exc))
        raise

    def submit(_event=None) -> None:
        value = entry.get()
        if not value:
            return
        sender = getattr(entry, "_session_sender", None)
        if sender is not None:
            sender(value + "\n")
        entry.delete(0, "end")

    entry.bind("<Return>", submit)
    parent._session_close = state["close"]
    return ConnectResult(
        connection_id=profile.id,
        protocol=profile.protocol,
        mode="gui-tab",
        message="Session tab opened",
        command=[],
    )


def _start_gui_ssh(profile: ConnectionProfile, append_output, entry):
    paramiko = _require_paramiko()
    config = profile.protocol_config
    assert isinstance(config, SSHConfig)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": config.host,
        "port": config.port,
        "username": config.username or None,
        "password": config.password or None,
        "timeout": config.timeout_seconds,
        "passphrase": config.passphrase or None,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if config.private_key_path:
        kwargs["key_filename"] = config.private_key_path
    client.connect(**kwargs)
    channel = client.invoke_shell()

    def reader() -> None:
        while not channel.closed:
            data = channel.recv(4096)
            if not data:
                continue
            append_output(data.decode("utf-8", errors="replace"))

    threading.Thread(target=reader, daemon=True).start()
    entry._session_sender = lambda value: channel.send(value)
    return lambda: (channel.close(), client.close())


def _start_gui_telnet(profile: ConnectionProfile, append_output, entry):
    from telnetlib import Telnet

    config = profile.protocol_config
    assert isinstance(config, TelnetConfig)
    session = Telnet(config.host, config.port, config.timeout_seconds)

    if config.username:
        session.write(config.username.encode("utf-8") + b"\n")
    if config.password:
        session.write(config.password.encode("utf-8") + b"\n")

    def reader() -> None:
        while True:
            try:
                data = session.read_very_eager()
            except EOFError:
                break
            if data:
                append_output(data.decode("utf-8", errors="replace"))

    threading.Thread(target=reader, daemon=True).start()
    entry._session_sender = lambda value: session.write(value.encode("utf-8"))
    return session.close


def _start_gui_serial(profile: ConnectionProfile, append_output, entry):
    serial = _require_serial()
    config = profile.protocol_config
    assert isinstance(config, SerialConfig)
    session = serial.Serial(
        port=config.port_name,
        baudrate=config.baudrate,
        bytesize=config.bytesize,
        parity=config.parity,
        stopbits=config.stopbits,
        timeout=config.timeout_seconds,
    )

    def reader() -> None:
        while session.is_open:
            data = session.read(4096)
            if data:
                append_output(data.decode("utf-8", errors="replace"))

    threading.Thread(target=reader, daemon=True).start()
    entry._session_sender = lambda value: session.write(value.encode("utf-8"))
    return session.close
