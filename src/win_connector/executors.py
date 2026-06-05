from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from telnetlib import Telnet

from win_connector.models import (
    ConnectionProfile,
    Protocol,
    RDPConfig,
    SSHConfig,
    SerialConfig,
    TaskExecutionResult,
    TaskTestResult,
    TelnetConfig,
    utc_now,
)
from win_connector.presets import preset_by_id
from win_connector.sessions import DependencyError, _require_paramiko, _require_serial


@dataclass(frozen=True)
class ResolvedTask:
    command: str
    mode: str
    preset_id: str | None


def resolve_command(command: str, preset_id: str | None, mode: str = "single") -> ResolvedTask:
    if command.strip():
        return ResolvedTask(command=command, mode=mode, preset_id=preset_id)
    if preset_id:
        preset = preset_by_id(preset_id)
        if preset is None:
            raise ValueError(f"Unknown preset_id: {preset_id}")
        return ResolvedTask(command=preset.command, mode=mode, preset_id=preset.id)
    raise ValueError("Either command or preset_id is required")


def execute_task(profile: ConnectionProfile, command: str, timeout: float = 10.0, mode: str = "single", preset_id: str | None = None) -> TaskExecutionResult:
    started = time.perf_counter()
    resolved = resolve_command(command, preset_id, mode)
    try:
        if profile.protocol == Protocol.SSH:
            result = _execute_ssh(profile, resolved.command, timeout, resolved.mode)
        elif profile.protocol == Protocol.TELNET:
            result = _execute_telnet(profile, resolved.command, timeout, resolved.mode)
        elif profile.protocol == Protocol.SERIAL:
            result = _execute_serial(profile, resolved.command, timeout, resolved.mode)
        elif profile.protocol == Protocol.RDP:
            result = TaskExecutionResult(
                status="unsupported",
                protocol=profile.protocol,
                connection_id=profile.id,
                command=resolved.command,
                mode=resolved.mode,
                preset_id=resolved.preset_id,
                stdout="",
                stderr="RDP does not support remote command execution in this connector.",
                exit_code=None,
                duration_ms=0,
                started_at=utc_now(),
                message="unsupported_remote_execution",
            )
        else:
            raise RuntimeError(f"Unsupported protocol: {profile.protocol}")
    except DependencyError as exc:
        result = TaskExecutionResult(
            status="error",
            protocol=profile.protocol,
            connection_id=profile.id,
            command=resolved.command,
            mode=resolved.mode,
            preset_id=resolved.preset_id,
            stdout="",
            stderr=str(exc),
            exit_code=None,
            duration_ms=0,
            started_at=utc_now(),
            message="dependency_error",
        )
    except Exception as exc:
        result = TaskExecutionResult(
            status="error",
            protocol=profile.protocol,
            connection_id=profile.id,
            command=resolved.command,
            mode=resolved.mode,
            preset_id=resolved.preset_id,
            stdout="",
            stderr=str(exc),
            exit_code=1,
            duration_ms=0,
            started_at=utc_now(),
            message="execution_error",
        )
    duration_ms = int((time.perf_counter() - started) * 1000)
    return result.model_copy(update={"duration_ms": duration_ms})


def test_connection(profile: ConnectionProfile, timeout: float = 5.0) -> TaskTestResult:
    try:
        if profile.protocol == Protocol.SSH:
            _test_ssh(profile, timeout)
            return TaskTestResult(connection_id=profile.id, protocol=profile.protocol, reachable=True, authenticated=True, error="", message="SSH login succeeded")
        if profile.protocol == Protocol.TELNET:
            _test_telnet(profile, timeout)
            return TaskTestResult(connection_id=profile.id, protocol=profile.protocol, reachable=True, authenticated=True, error="", message="Telnet session opened")
        if profile.protocol == Protocol.SERIAL:
            _test_serial(profile)
            return TaskTestResult(connection_id=profile.id, protocol=profile.protocol, reachable=True, authenticated=True, error="", message="Serial port opened")
        if profile.protocol == Protocol.RDP:
            _test_rdp(profile, timeout)
            return TaskTestResult(connection_id=profile.id, protocol=profile.protocol, reachable=True, authenticated=False, error="", message="RDP port reachable; authentication is not verified")
    except Exception as exc:
        return TaskTestResult(
            connection_id=profile.id,
            protocol=profile.protocol,
            reachable=False,
            authenticated=False,
            error=type(exc).__name__,
            message=str(exc),
        )
    raise RuntimeError(f"Unsupported protocol: {profile.protocol}")


def _execute_ssh(profile: ConnectionProfile, command: str, timeout: float, mode: str) -> TaskExecutionResult:
    paramiko = _require_paramiko()
    config = profile.protocol_config
    assert isinstance(config, SSHConfig)
    started_at = utc_now()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": config.host,
        "port": config.port,
        "username": config.username or None,
        "password": config.password or None,
        "timeout": timeout or config.timeout_seconds,
        "passphrase": config.passphrase or None,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if config.private_key_path:
        kwargs["key_filename"] = config.private_key_path
    try:
        client.connect(**kwargs)
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        _ = stdin
        stdout_text = stdout.read().decode("utf-8", errors="replace")
        stderr_text = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        status = "success" if exit_code == 0 else "error"
        return TaskExecutionResult(
            status=status,
            protocol=profile.protocol,
            connection_id=profile.id,
            command=command,
            mode=mode,
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=exit_code,
            duration_ms=0,
            started_at=started_at,
            message="ssh_exec_completed",
        )
    finally:
        client.close()


def _execute_telnet(profile: ConnectionProfile, command: str, timeout: float, mode: str) -> TaskExecutionResult:
    config = profile.protocol_config
    assert isinstance(config, TelnetConfig)
    started_at = utc_now()
    with Telnet(config.host, config.port, timeout) as session:
        session.write((config.username + "\n").encode("utf-8")) if config.username else None
        session.write((config.password + "\n").encode("utf-8")) if config.password else None
        banner = _read_telnet_until_quiet(session, timeout=1.0, idle_window=0.3)
        session.write((command + "\n").encode("utf-8"))
        output = _read_telnet_until_quiet(session, timeout=timeout, idle_window=0.6)
    return TaskExecutionResult(
        status="success",
        protocol=profile.protocol,
        connection_id=profile.id,
        command=command,
        mode=mode,
        stdout=(banner + output).strip(),
        stderr="",
        exit_code=0,
        duration_ms=0,
        started_at=started_at,
        message="telnet_command_completed",
    )


def _execute_serial(profile: ConnectionProfile, command: str, timeout: float, mode: str) -> TaskExecutionResult:
    serial = _require_serial()
    config = profile.protocol_config
    assert isinstance(config, SerialConfig)
    started_at = utc_now()
    session = serial.Serial(
        port=config.port_name,
        baudrate=config.baudrate,
        bytesize=config.bytesize,
        parity=config.parity,
        stopbits=config.stopbits,
        timeout=min(timeout, max(config.timeout_seconds, 0.1)),
        write_timeout=timeout,
    )
    try:
        session.reset_input_buffer()
        session.write((command + "\n").encode("utf-8"))
        session.flush()
        output = _read_serial_until_timeout(session, timeout)
    finally:
        session.close()
    return TaskExecutionResult(
        status="success",
        protocol=profile.protocol,
        connection_id=profile.id,
        command=command,
        mode=mode,
        stdout=output.strip(),
        stderr="",
        exit_code=0,
        duration_ms=0,
        started_at=started_at,
        message="serial_command_completed",
    )


def _read_telnet_until_quiet(session: Telnet, timeout: float, idle_window: float) -> str:
    deadline = time.monotonic() + timeout
    last_data = time.monotonic()
    chunks: list[bytes] = []
    while time.monotonic() < deadline:
        data = session.read_very_eager()
        if data:
            chunks.append(data)
            last_data = time.monotonic()
            continue
        if time.monotonic() - last_data >= idle_window:
            break
        time.sleep(0.1)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _read_serial_until_timeout(session, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    chunks: list[bytes] = []
    while time.monotonic() < deadline:
        waiting = getattr(session, "in_waiting", 0)
        if waiting:
            chunks.append(session.read(waiting))
            continue
        chunk = session.read(1024)
        if chunk:
            chunks.append(chunk)
            continue
        time.sleep(0.05)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _test_ssh(profile: ConnectionProfile, timeout: float) -> None:
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
        "timeout": timeout or config.timeout_seconds,
        "passphrase": config.passphrase or None,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if config.private_key_path:
        kwargs["key_filename"] = config.private_key_path
    try:
        client.connect(**kwargs)
    finally:
        client.close()


def _test_telnet(profile: ConnectionProfile, timeout: float) -> None:
    config = profile.protocol_config
    assert isinstance(config, TelnetConfig)
    with Telnet(config.host, config.port, timeout) as session:
        if config.username:
            session.write((config.username + "\n").encode("utf-8"))
        if config.password:
            session.write((config.password + "\n").encode("utf-8"))
        _read_telnet_until_quiet(session, timeout=min(timeout, 1.5), idle_window=0.3)


def _test_serial(profile: ConnectionProfile) -> None:
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
    session.close()


def _test_rdp(profile: ConnectionProfile, timeout: float) -> None:
    config = profile.protocol_config
    assert isinstance(config, RDPConfig)
    with socket.create_connection((config.host, config.port), timeout=timeout):
        return
