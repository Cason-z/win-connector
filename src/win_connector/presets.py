from __future__ import annotations

from dataclasses import dataclass

from win_connector.models import DeviceTemplate


@dataclass(frozen=True)
class CommandPreset:
    id: str
    title: str
    title_zh: str
    command: str
    templates: tuple[DeviceTemplate, ...]


COMMAND_PRESETS: tuple[CommandPreset, ...] = (
    CommandPreset(
        id="linux_uname",
        title="Show System",
        title_zh="查看系统信息",
        command="uname -a",
        templates=(DeviceTemplate.LINUX, DeviceTemplate.FIREWALL_GENERIC, DeviceTemplate.JUNIPER),
    ),
    CommandPreset(
        id="linux_ip_brief",
        title="Show Interfaces",
        title_zh="查看接口信息",
        command="ip -brief address",
        templates=(DeviceTemplate.LINUX,),
    ),
    CommandPreset(
        id="cisco_show_version",
        title="Show Version",
        title_zh="查看版本信息",
        command="show version",
        templates=(DeviceTemplate.CISCO_IOS,),
    ),
    CommandPreset(
        id="cisco_ip_int_brief",
        title="Show IP Interface Brief",
        title_zh="查看接口摘要",
        command="show ip int brief",
        templates=(DeviceTemplate.CISCO_IOS,),
    ),
    CommandPreset(
        id="huawei_display_version",
        title="Display Version",
        title_zh="查看版本信息",
        command="display version",
        templates=(DeviceTemplate.HUAWEI,),
    ),
    CommandPreset(
        id="h3c_display_version",
        title="Display Version",
        title_zh="查看版本信息",
        command="display version",
        templates=(DeviceTemplate.H3C,),
    ),
    CommandPreset(
        id="juniper_show_version",
        title="Show Version",
        title_zh="查看版本信息",
        command="show version",
        templates=(DeviceTemplate.JUNIPER,),
    ),
    CommandPreset(
        id="serial_show_version",
        title="Console Version Check",
        title_zh="串口版本巡检",
        command="show version",
        templates=(DeviceTemplate.SERIAL_CONSOLE,),
    ),
)


def presets_for_template(template: DeviceTemplate) -> list[CommandPreset]:
    return [preset for preset in COMMAND_PRESETS if template in preset.templates]


def preset_by_id(preset_id: str) -> CommandPreset | None:
    for preset in COMMAND_PRESETS:
        if preset.id == preset_id:
            return preset
    return None
