from __future__ import annotations

from win_connector.models import (
    ConnectionCreateRequest,
    DeviceTemplate,
    Protocol,
    RDPConfig,
    SSHConfig,
    SerialConfig,
    TelnetConfig,
    WebConfig,
)


TEMPLATE_PROTOCOL_MAP: dict[DeviceTemplate, Protocol] = {
    DeviceTemplate.LINUX: Protocol.SSH,
    DeviceTemplate.CISCO_IOS: Protocol.TELNET,
    DeviceTemplate.H3C: Protocol.TELNET,
    DeviceTemplate.HUAWEI: Protocol.TELNET,
    DeviceTemplate.JUNIPER: Protocol.SSH,
    DeviceTemplate.FIREWALL_GENERIC: Protocol.SSH,
    DeviceTemplate.SERIAL_CONSOLE: Protocol.SERIAL,
    DeviceTemplate.WEB_APP: Protocol.WEB,
}


def build_template_request(
    template: DeviceTemplate,
    name: str,
    host: str = "",
    port_name: str = "COM1",
    username: str = "",
    password: str = "",
    group: str = "default",
    tags: list[str] | None = None,
    notes: str = "",
) -> ConnectionCreateRequest:
    tags = tags or [template.value]
    protocol = TEMPLATE_PROTOCOL_MAP[template]

    if protocol == Protocol.SSH:
        config = SSHConfig(host=host or "127.0.0.1", username=username, password=password)
    elif protocol == Protocol.TELNET:
        config = TelnetConfig(host=host or "127.0.0.1", username=username, password=password)
    elif protocol == Protocol.SERIAL:
        config = SerialConfig(port_name=port_name)
    elif protocol == Protocol.RDP:
        config = RDPConfig(host=host or "127.0.0.1", username=username)
    else:
        config = WebConfig(url=host or "http://127.0.0.1", username=username, password=password)

    return ConnectionCreateRequest(
        name=name,
        protocol=protocol,
        group=group,
        tags=tags,
        notes=notes,
        device_template=template,
        protocol_config=config,
    )

