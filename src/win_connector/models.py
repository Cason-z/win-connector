from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Protocol(str, Enum):
    SSH = "ssh"
    TELNET = "telnet"
    SERIAL = "serial"
    RDP = "rdp"
    WEB = "web"


class DeviceTemplate(str, Enum):
    LINUX = "linux"
    CISCO_IOS = "cisco_ios"
    H3C = "h3c"
    HUAWEI = "huawei"
    JUNIPER = "juniper"
    FIREWALL_GENERIC = "firewall_generic"
    SERIAL_CONSOLE = "serial_console"
    WEB_APP = "web_app"


class SSHConfig(BaseModel):
    protocol: Literal["ssh"] = "ssh"
    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    private_key_path: str = ""
    passphrase: str = ""
    timeout_seconds: int = 10
    open_in_external_terminal: bool = False


class TelnetConfig(BaseModel):
    protocol: Literal["telnet"] = "telnet"
    host: str
    port: int = 23
    username: str = ""
    password: str = ""
    timeout_seconds: int = 10


class SerialConfig(BaseModel):
    protocol: Literal["serial"] = "serial"
    port_name: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout_seconds: float = 1.0


class RDPConfig(BaseModel):
    protocol: Literal["rdp"] = "rdp"
    host: str
    port: int = 3389
    username: str = ""
    screen_mode: str = "windowed"


class WebConfig(BaseModel):
    protocol: Literal["web"] = "web"
    url: str
    username: str = ""
    password: str = ""
    browser: str = "default"


ProtocolConfig = Annotated[
    SSHConfig | TelnetConfig | SerialConfig | RDPConfig | WebConfig,
    Field(discriminator="protocol"),
]


class ConnectionProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    protocol: Protocol
    group: str = "default"
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    device_template: DeviceTemplate = DeviceTemplate.LINUX
    protocol_config: ProtocolConfig
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)

    def model_post_init(self, __context: object) -> None:
        if self.protocol != self.protocol_config.protocol:
            raise ValueError("protocol must match protocol_config.protocol")


class ConnectionCreateRequest(BaseModel):
    name: str
    protocol: Protocol
    group: str = "default"
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    device_template: DeviceTemplate = DeviceTemplate.LINUX
    protocol_config: ProtocolConfig


class ConnectionUpdateRequest(BaseModel):
    name: str | None = None
    protocol: Protocol | None = None
    group: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    device_template: DeviceTemplate | None = None
    protocol_config: ProtocolConfig | None = None


class HealthResponse(BaseModel):
    status: str
    storage_path: str


class ConnectResult(BaseModel):
    connection_id: str
    protocol: Protocol
    mode: str
    message: str
    command: list[str] = Field(default_factory=list)


class TaskExecuteRequest(BaseModel):
    connection_id: str
    command: str = ""
    timeout: float = 10.0
    mode: str = "single"
    preset_id: str | None = None


class TaskExecutionResult(BaseModel):
    status: str
    protocol: Protocol
    connection_id: str
    command: str
    mode: str = "single"
    preset_id: str | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = 0
    started_at: str = Field(default_factory=utc_now)
    message: str = ""


class ConnectionTestRequest(BaseModel):
    timeout: float = 5.0


class TaskTestResult(BaseModel):
    connection_id: str
    protocol: Protocol
    reachable: bool
    authenticated: bool
    error: str = ""
    message: str = ""


class TaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: Literal["execute", "test"]
    connection_id: str
    connection_name: str
    protocol: Protocol
    device_template: DeviceTemplate
    command: str = ""
    preset_id: str | None = None
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = 0
    reachable: bool | None = None
    authenticated: bool | None = None
    created_at: str = Field(default_factory=utc_now)
    message: str = ""

    @classmethod
    def from_execution(cls, profile: ConnectionProfile, result: TaskExecutionResult) -> "TaskRecord":
        return cls(
            kind="execute",
            connection_id=profile.id,
            connection_name=profile.name,
            protocol=profile.protocol,
            device_template=profile.device_template,
            command=result.command,
            preset_id=result.preset_id,
            status=result.status,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
            created_at=result.started_at,
            message=result.message,
        )

    @classmethod
    def from_test(cls, profile: ConnectionProfile, result: TaskTestResult) -> "TaskRecord":
        return cls(
            kind="test",
            connection_id=profile.id,
            connection_name=profile.name,
            protocol=profile.protocol,
            device_template=profile.device_template,
            status="success" if result.reachable else "error",
            stdout="",
            stderr="" if result.reachable else result.message,
            exit_code=None,
            duration_ms=0,
            reachable=result.reachable,
            authenticated=result.authenticated,
            message=result.message,
        )
