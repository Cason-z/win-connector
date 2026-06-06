from __future__ import annotations

import locale

from win_connector.models import DeviceTemplate, Protocol


SUPPORTED_LANGUAGES = ("en-US", "zh-CN")


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en-US": {
        "app.title": "Win Connector",
        "app.brand": "Win Connector",
        "app.subtitle": "Profile-first command bridge for SSH, Telnet, Serial and RDP.",
        "header.language": "Language",
        "header.search": "Search",
        "header.search_hint": "Filter profiles by name, host, group, template or tags",
        "header.clear": "Clear",
        "quick.panel": "Quick Profile",
        "quick.title": "Create a connection without leaving the dashboard",
        "quick.add": "Add Profile",
        "groups.add_title": "Add Group",
        "filters.title": "Groups & Filters",
        "filters.protocol": "Protocol",
        "filters.template": "Template",
        "filters.group": "Group",
        "filters.all": "All",
        "filters.summary": "Profiles stay grouped by environment, customer or device role.",
        "table.name": "Name",
        "table.protocol": "Protocol",
        "table.endpoint": "Host / Port",
        "table.group": "Group",
        "table.template": "Template",
        "table.tags": "Tags",
        "actions.add": "Advanced",
        "actions.edit": "Edit",
        "actions.delete": "Delete",
        "actions.connect": "Connect",
        "actions.refresh": "Refresh",
        "actions.execute": "Execute",
        "actions.test": "Test",
        "actions.close": "Close",
        "status.ready": "Ready",
        "status.path": "Storage",
        "status.connections": "Profiles",
        "status.language": "Language",
        "messages.select_title": "Select Connection",
        "messages.select_body": "Select a connection first.",
        "messages.delete_title": "Delete Connection",
        "messages.delete_confirm": "Delete {name}?",
        "messages.connect_error": "Connection Error",
        "messages.validation_error": "Validation Error",
        "messages.empty": "No profiles match the current filter.",
        "tasks.panel": "Command Console",
        "tasks.target": "Target",
        "tasks.preset": "Preset",
        "tasks.timeout": "Timeout",
        "tasks.command": "Command",
        "tasks.history": "Recent Tasks",
        "tasks.no_selection": "No profile selected",
        "tasks.no_presets": "No preset",
        "tasks.output_empty": "No output.",
        "tasks.summary_idle": "Select a profile to test or execute a command.",
        "tasks.summary_ready": "Template: {template}",
        "tasks.summary_result": "Execution finished: {status} / {duration} ms",
        "tasks.summary_test": "Test result: reachable={reachable}, authenticated={authenticated}",
        "tasks.history_kind": "Kind",
        "tasks.history_status": "Status",
        "tasks.history_connection": "Connection",
        "editor.new_title": "Create Connection",
        "editor.edit_title": "Edit Connection",
        "editor.general": "Profile Overview",
        "editor.general_hint": "Use concise names and group paths so operators can scan quickly.",
        "editor.protocol": "Protocol Details",
        "editor.credentials": "Credentials",
        "editor.protocol_hint.ssh": "SSH supports password or key-based login.",
        "editor.protocol_hint.telnet": "Telnet is intended for legacy devices and lab access.",
        "editor.protocol_hint.serial": "Serial mode is ideal for break-fix and out-of-band console work.",
        "editor.protocol_hint.rdp": "RDP launches the Windows client through mstsc.",
        "editor.credentials_hint": "Stored locally in the JSON profile. Leave blank to avoid saving a password.",
        "editor.notes": "Operator Notes",
        "editor.notes_hint": "Capture change windows, caveats or escalation hints.",
        "editor.name": "Name",
        "editor.group": "Group",
        "editor.tags": "Tags",
        "editor.tags_hint": "Comma separated, for example core,prod,oob",
        "editor.template": "Template",
        "editor.protocol_label": "Protocol",
        "editor.host": "Host",
        "editor.port": "Port",
        "editor.username": "Username",
        "editor.password": "Password",
        "editor.show_password": "Show password",
        "editor.private_key": "Private Key",
        "editor.port_name": "COM Port",
        "editor.baudrate": "Baudrate",
        "editor.save": "Save",
        "editor.cancel": "Cancel",
        "language.en-US": "English",
        "language.zh-CN": "Simplified Chinese",
    },
    "zh-CN": {
        "app.title": "Win Connector",
        "app.brand": "Win Connector",
        "app.subtitle": "面向 SSH、Telnet、串口和 RDP 的配置档连接控制台。",
        "header.language": "语言",
        "header.search": "搜索",
        "header.search_hint": "按名称、主机、分组、模板或标签过滤配置档",
        "header.clear": "清空",
        "quick.panel": "快速配置",
        "quick.title": "不用离开主界面，直接创建连接配置",
        "quick.add": "添加配置",
        "groups.add_title": "添加分组",
        "filters.title": "分组与筛选",
        "filters.protocol": "协议",
        "filters.template": "模板",
        "filters.group": "分组",
        "filters.all": "全部",
        "filters.summary": "按环境、客户或设备角色组织连接配置。",
        "table.name": "名称",
        "table.protocol": "协议",
        "table.endpoint": "主机 / 端口",
        "table.group": "分组",
        "table.template": "模板",
        "table.tags": "标签",
        "actions.add": "高级",
        "actions.edit": "编辑",
        "actions.delete": "删除",
        "actions.connect": "连接",
        "actions.refresh": "刷新",
        "actions.execute": "执行",
        "actions.test": "测试",
        "actions.close": "关闭",
        "status.ready": "就绪",
        "status.path": "存储路径",
        "status.connections": "配置数",
        "status.language": "语言",
        "messages.select_title": "请选择连接",
        "messages.select_body": "请先选择一条连接配置。",
        "messages.delete_title": "删除连接",
        "messages.delete_confirm": "确认删除 {name}？",
        "messages.connect_error": "连接错误",
        "messages.validation_error": "校验错误",
        "messages.empty": "当前筛选条件下没有匹配的配置。",
        "tasks.panel": "命令控制台",
        "tasks.target": "目标",
        "tasks.preset": "预设",
        "tasks.timeout": "超时",
        "tasks.command": "命令",
        "tasks.history": "最近任务",
        "tasks.no_selection": "未选择配置",
        "tasks.no_presets": "无预设",
        "tasks.output_empty": "暂无输出。",
        "tasks.summary_idle": "选择配置后可以测试或执行命令。",
        "tasks.summary_ready": "模板：{template}",
        "tasks.summary_result": "执行完成：{status} / {duration} ms",
        "tasks.summary_test": "测试结果：reachable={reachable}, authenticated={authenticated}",
        "tasks.history_kind": "类型",
        "tasks.history_status": "状态",
        "tasks.history_connection": "连接",
        "editor.new_title": "新建连接",
        "editor.edit_title": "编辑连接",
        "editor.general": "连接概览",
        "editor.general_hint": "名称和分组尽量简洁，方便快速识别。",
        "editor.protocol": "协议详情",
        "editor.credentials": "登录凭据",
        "editor.protocol_hint.ssh": "SSH 支持密码或私钥登录。",
        "editor.protocol_hint.telnet": "Telnet 适用于旧设备或实验环境。",
        "editor.protocol_hint.serial": "串口模式适合故障处理和带外控制台。",
        "editor.protocol_hint.rdp": "RDP 会调用 Windows mstsc 客户端。",
        "editor.credentials_hint": "凭据保存在本地 JSON 配置中；留空则不保存密码。",
        "editor.notes": "运维备注",
        "editor.notes_hint": "记录变更窗口、注意事项或升级提示。",
        "editor.name": "名称",
        "editor.group": "分组",
        "editor.tags": "标签",
        "editor.tags_hint": "用英文逗号分隔，例如 core,prod,oob",
        "editor.template": "模板",
        "editor.protocol_label": "协议",
        "editor.host": "主机",
        "editor.port": "端口",
        "editor.username": "用户名",
        "editor.password": "密码",
        "editor.show_password": "显示密码",
        "editor.private_key": "私钥路径",
        "editor.port_name": "串口号",
        "editor.baudrate": "波特率",
        "editor.save": "保存",
        "editor.cancel": "取消",
        "language.en-US": "English",
        "language.zh-CN": "简体中文",
    },
}


PROTOCOL_TEXT = {
    "en-US": {
        Protocol.SSH: "SSH",
        Protocol.TELNET: "Telnet",
        Protocol.SERIAL: "Serial",
        Protocol.RDP: "RDP",
    },
    "zh-CN": {
        Protocol.SSH: "SSH",
        Protocol.TELNET: "Telnet",
        Protocol.SERIAL: "串口",
        Protocol.RDP: "远程桌面",
    },
}


TEMPLATE_TEXT = {
    "en-US": {
        DeviceTemplate.LINUX: "Linux",
        DeviceTemplate.CISCO_IOS: "Cisco IOS",
        DeviceTemplate.H3C: "H3C",
        DeviceTemplate.HUAWEI: "Huawei",
        DeviceTemplate.JUNIPER: "Juniper",
        DeviceTemplate.FIREWALL_GENERIC: "Firewall",
        DeviceTemplate.SERIAL_CONSOLE: "Serial Console",
    },
    "zh-CN": {
        DeviceTemplate.LINUX: "Linux",
        DeviceTemplate.CISCO_IOS: "Cisco IOS",
        DeviceTemplate.H3C: "H3C",
        DeviceTemplate.HUAWEI: "华为",
        DeviceTemplate.JUNIPER: "Juniper",
        DeviceTemplate.FIREWALL_GENERIC: "通用防火墙",
        DeviceTemplate.SERIAL_CONSOLE: "串口控制台",
    },
}


def normalize_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    if language:
        lowered = language.lower()
        if lowered.startswith("zh"):
            return "zh-CN"
        if lowered.startswith("en"):
            return "en-US"
    return "en-US"


def default_language() -> str:
    locale_info = locale.getlocale()
    system_locale = locale_info[0] if locale_info else None
    return normalize_language(system_locale)


class I18N:
    def __init__(self, language: str | None = None) -> None:
        self.language = normalize_language(language)

    def set_language(self, language: str) -> None:
        self.language = normalize_language(language)

    def t(self, key: str, **kwargs: object) -> str:
        template = TRANSLATIONS.get(self.language, TRANSLATIONS["en-US"]).get(key)
        if template is None:
            template = TRANSLATIONS["en-US"].get(key, key)
        return template.format(**kwargs)

    def protocol_text(self, protocol: Protocol) -> str:
        return PROTOCOL_TEXT.get(self.language, PROTOCOL_TEXT["en-US"])[protocol]

    def template_text(self, template: DeviceTemplate) -> str:
        return TEMPLATE_TEXT.get(self.language, TEMPLATE_TEXT["en-US"])[template]
