from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from win_connector.i18n import default_language
from win_connector.logging_utils import setup_logging
from win_connector.config import task_history_path_for
from win_connector.models import (
    ConnectionTestRequest,
    ConnectionCreateRequest,
    DeviceTemplate,
    Protocol,
    RDPConfig,
    SSHConfig,
    SerialConfig,
    TaskExecuteRequest,
    TelnetConfig,
)
from win_connector.service import ConnectionService
from win_connector.storage import JSONStorage
from win_connector.tasks import TaskService
from win_connector.templates import build_template_request
from win_connector.launcher import ConnectionLauncher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="win-connector", description="Windows multi-protocol connection manager")
    parser.add_argument("--storage", type=Path, default=None, help="Path to JSON storage file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("id")
    show_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id")
    delete_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    connect_parser = subparsers.add_parser("connect")
    connect_parser.add_argument("id")
    connect_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("id")
    execute_parser.add_argument("--command", dest="command_text", default="")
    execute_parser.add_argument("--preset", default="")
    execute_parser.add_argument("--timeout", type=float, default=10.0)
    execute_parser.add_argument("--mode", default="single")
    execute_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("id")
    test_parser.add_argument("--timeout", type=float, default=5.0)
    test_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    tasks_parser = subparsers.add_parser("tasks")
    tasks_parser.add_argument("--limit", type=int, default=20)
    tasks_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    gui_parser = subparsers.add_parser("gui")
    gui_parser.add_argument("--title", default=None)
    gui_parser.add_argument("--lang", choices=["zh-CN", "en-US"], default=default_language())

    api_parser = subparsers.add_parser("serve-api")
    api_parser.add_argument("--host", default="127.0.0.1")
    api_parser.add_argument("--port", type=int, default=8000)

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--protocol", choices=[p.value for p in Protocol])
    add_parser.add_argument("--template", choices=[t.value for t in DeviceTemplate])
    add_parser.add_argument("--group", default="default")
    add_parser.add_argument("--tags", default="")
    add_parser.add_argument("--notes", default="")
    add_parser.add_argument("--host", default="")
    add_parser.add_argument("--port", type=int)
    add_parser.add_argument("--username", default="")
    add_parser.add_argument("--password", default="")
    add_parser.add_argument("--private-key-path", default="")
    add_parser.add_argument("--port-name", default="COM1")
    add_parser.add_argument("--baudrate", type=int, default=9600)
    add_parser.add_argument("--json", action="store_true", help="Return structured JSON output")

    return parser


def emit(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if isinstance(data, list):
        for item in data:
            print(f"{item['id']}  {item['name']}  {item['protocol']}  {item['group']}  {','.join(item['tags'])}")
        return
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_request_from_args(args) -> ConnectionCreateRequest:
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    if args.template:
        return build_template_request(
            template=DeviceTemplate(args.template),
            name=args.name,
            host=args.host,
            port_name=args.port_name,
            username=args.username,
            password=args.password,
            group=args.group,
            tags=tags or None,
            notes=args.notes,
        )
    if not args.protocol:
        raise ValueError("Either --protocol or --template is required")
    protocol = Protocol(args.protocol)
    if protocol == Protocol.SSH:
        config = SSHConfig(
            host=args.host,
            port=args.port or 22,
            username=args.username,
            password=args.password,
            private_key_path=args.private_key_path,
        )
    elif protocol == Protocol.TELNET:
        config = TelnetConfig(
            host=args.host,
            port=args.port or 23,
            username=args.username,
            password=args.password,
        )
    elif protocol == Protocol.SERIAL:
        config = SerialConfig(port_name=args.port_name, baudrate=args.baudrate)
    else:
        config = RDPConfig(host=args.host, port=args.port or 3389, username=args.username)
    return ConnectionCreateRequest(
        name=args.name,
        protocol=protocol,
        group=args.group,
        tags=tags,
        notes=args.notes,
        device_template=DeviceTemplate(args.template) if args.template else _default_template(protocol),
        protocol_config=config,
    )


def _default_template(protocol: Protocol) -> DeviceTemplate:
    if protocol == Protocol.SSH:
        return DeviceTemplate.LINUX
    if protocol == Protocol.TELNET:
        return DeviceTemplate.CISCO_IOS
    if protocol == Protocol.SERIAL:
        return DeviceTemplate.SERIAL_CONSOLE
    return DeviceTemplate.FIREWALL_GENERIC


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = JSONStorage(args.storage)
    service = ConnectionService(storage)
    launcher = ConnectionLauncher()
    task_service = TaskService(task_history_path_for(storage.path))

    try:
        if args.command == "list":
            emit([profile.model_dump(mode="json") for profile in service.list_connections()], args.json)
            return 0
        if args.command == "show":
            emit(service.get_connection(args.id).model_dump(mode="json"), True if args.json else False)
            return 0
        if args.command == "delete":
            service.delete_connection(args.id)
            emit({"status": "deleted", "id": args.id}, args.json or True)
            return 0
        if args.command == "add":
            profile = service.create_connection(build_request_from_args(args))
            emit(profile.model_dump(mode="json"), args.json or True)
            return 0
        if args.command == "connect":
            result = launcher.connect(service.get_connection(args.id))
            emit(result.model_dump(mode="json"), args.json or True)
            return 0
        if args.command == "execute":
            result = task_service.execute(
                service.get_connection(args.id),
                TaskExecuteRequest(
                    connection_id=args.id,
                    command=args.command_text,
                    preset_id=args.preset or None,
                    timeout=args.timeout,
                    mode=args.mode,
                ),
            )
            emit(result.model_dump(mode="json"), args.json or True)
            return 0 if result.status == "success" else 1
        if args.command == "test":
            result = task_service.test(
                service.get_connection(args.id),
                timeout=ConnectionTestRequest(timeout=args.timeout).timeout,
            )
            emit(result.model_dump(mode="json"), args.json or True)
            return 0 if result.reachable else 1
        if args.command == "tasks":
            emit([record.model_dump(mode="json") for record in task_service.recent_history(limit=args.limit)], args.json or True)
            return 0
        if args.command == "serve-api":
            try:
                import uvicorn
            except ImportError as exc:
                raise RuntimeError("uvicorn is required for serve-api") from exc
            from win_connector.api import create_app

            app = create_app(storage.path)
            uvicorn.run(app, host=args.host, port=args.port)
            return 0
        if args.command == "gui":
            from win_connector.gui import WinConnectorApp

            app = WinConnectorApp(service, title=args.title, language=args.lang)
            app.run()
            return 0
    except Exception as exc:
        emit({"status": "error", "error": str(exc)}, True)
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
