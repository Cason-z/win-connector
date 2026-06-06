from __future__ import annotations

import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

from win_connector.i18n import I18N, SUPPORTED_LANGUAGES
from win_connector.launcher import ConnectionLauncher
from win_connector.models import (
    ConnectionTestRequest,
    ConnectionCreateRequest,
    ConnectionProfile,
    ConnectionUpdateRequest,
    DeviceTemplate,
    Protocol,
    RDPConfig,
    SSHConfig,
    SerialConfig,
    TaskExecuteRequest,
    TelnetConfig,
)
from win_connector.service import ConnectionService
from win_connector.sessions import open_external_terminal, start_gui_session_tab
from win_connector.tasks import TaskService
from win_connector.templates import TEMPLATE_PROTOCOL_MAP
from win_connector.theme import PALETTE, apply_theme
from win_connector.config import task_history_path_for


ALL_FILTER = "__all__"


class WinConnectorApp:
    def __init__(self, service: ConnectionService, title: str | None = None, language: str | None = None) -> None:
        self.service = service
        self.launcher = ConnectionLauncher()
        self.task_service = TaskService(task_history_path_for(service.storage.path))
        self.i18n = I18N(language)
        self.title_override = title
        self.root = tk.Tk()
        self.root.geometry("1360x820")
        self.root.minsize(1180, 720)
        apply_theme(self.root)

        self.search_var = tk.StringVar()
        self.protocol_filter_var = tk.StringVar(value=ALL_FILTER)
        self.template_filter_var = tk.StringVar(value=ALL_FILTER)
        self.group_filter_var = tk.StringVar(value=ALL_FILTER)
        self.language_var = tk.StringVar(value=self.i18n.language)
        self.empty_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.task_command_var = tk.StringVar()
        self.task_preset_var = tk.StringVar()
        self.task_timeout_var = tk.StringVar(value="10")
        self.task_target_var = tk.StringVar()
        self.task_summary_var = tk.StringVar()
        self.quick_name_var = tk.StringVar()
        self.quick_protocol_var = tk.StringVar(value=Protocol.SSH.value)
        self.quick_template_var = tk.StringVar(value=DeviceTemplate.LINUX.value)
        self.quick_host_var = tk.StringVar()
        self.quick_port_var = tk.StringVar(value="22")
        self.quick_username_var = tk.StringVar()
        self.quick_password_var = tk.StringVar()
        self.quick_group_var = tk.StringVar(value="default")
        self.quick_tags_var = tk.StringVar()
        self.quick_show_password_var = tk.BooleanVar(value=False)
        self.new_group_var = tk.StringVar()
        self.service_local_port_var = tk.StringVar(value="8080")
        self.service_remote_host_var = tk.StringVar(value="127.0.0.1")
        self.service_remote_port_var = tk.StringVar(value="80")
        self.action_status_var = tk.StringVar()
        self.motion_phase = 0

        self.all_profiles: list[ConnectionProfile] = []
        self.recent_tasks: list[dict[str, str]] = []
        self.manual_groups: set[str] = set()
        self.protocol_filter_map: dict[str, str] = {}
        self.template_filter_map: dict[str, str] = {}
        self.group_filter_map: dict[str, str] = {}
        self.language_label_map: dict[str, str] = {}
        self.task_preset_map: dict[str, str] = {}
        self.quick_protocol_map: dict[str, str] = {}
        self.quick_template_map: dict[str, str] = {}

        self._build()
        self._bind_events()
        self._apply_text()
        self.refresh()
        self._pulse_header()

    def _build(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, style="Root.TFrame", padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        self.header_frame = ttk.Frame(container, style="Header.TFrame", padding=18)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.columnconfigure(0, weight=1)

        self.header_canvas = tk.Canvas(
            self.header_frame,
            height=4,
            bg=PALETTE["panel"],
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.header_canvas.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        brand_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        brand_frame.grid(row=1, column=0, sticky="w")
        self.brand_label = ttk.Label(brand_frame, style="Brand.TLabel")
        self.brand_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ttk.Label(brand_frame, style="Muted.TLabel")
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.language_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        self.language_frame.grid(row=1, column=1, sticky="e")
        self.language_label = ttk.Label(self.language_frame, style="Section.TLabel")
        self.language_label.grid(row=0, column=0, sticky="e", padx=(0, 8))
        self.language_combo = ttk.Combobox(self.language_frame, state="readonly", textvariable=self.language_var, width=12)
        self.language_combo.grid(row=0, column=1, sticky="e")

        self.quick_frame = ttk.LabelFrame(container, style="Glow.TLabelframe", padding=(18, 14))
        self.quick_frame.grid(row=1, column=0, sticky="ew", pady=(14, 14))
        self.quick_frame.columnconfigure(1, weight=1)
        self.quick_frame.columnconfigure(3, weight=1)
        self.quick_frame.columnconfigure(5, weight=1)

        self.quick_title_label = ttk.Label(self.quick_frame, style="Section.TLabel")
        self.quick_title_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        self.quick_name_label = ttk.Label(self.quick_frame)
        self.quick_name_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        self.quick_name_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_name_var)
        self.quick_name_entry.grid(row=1, column=1, sticky="ew", pady=5)

        self.quick_protocol_label = ttk.Label(self.quick_frame)
        self.quick_protocol_label.grid(row=1, column=2, sticky="w", padx=(16, 8), pady=5)
        self.quick_protocol_combo = ttk.Combobox(self.quick_frame, state="readonly", textvariable=self.quick_protocol_var, width=16)
        self.quick_protocol_combo.grid(row=1, column=3, sticky="ew", pady=5)

        self.quick_template_label = ttk.Label(self.quick_frame)
        self.quick_template_label.grid(row=1, column=4, sticky="w", padx=(16, 8), pady=5)
        self.quick_template_combo = ttk.Combobox(self.quick_frame, state="readonly", textvariable=self.quick_template_var, width=18)
        self.quick_template_combo.grid(row=1, column=5, sticky="ew", pady=5)

        self.quick_host_label = ttk.Label(self.quick_frame)
        self.quick_host_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        self.quick_host_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_host_var)
        self.quick_host_entry.grid(row=2, column=1, sticky="ew", pady=5)

        self.quick_port_label = ttk.Label(self.quick_frame)
        self.quick_port_label.grid(row=2, column=2, sticky="w", padx=(16, 8), pady=5)
        self.quick_port_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_port_var, width=10)
        self.quick_port_entry.grid(row=2, column=3, sticky="w", pady=5)

        self.quick_group_label = ttk.Label(self.quick_frame)
        self.quick_group_label.grid(row=2, column=4, sticky="w", padx=(16, 8), pady=5)
        self.quick_group_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_group_var)
        self.quick_group_entry.grid(row=2, column=5, sticky="ew", pady=5)

        self.quick_username_label = ttk.Label(self.quick_frame)
        self.quick_username_label.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=5)
        self.quick_username_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_username_var)
        self.quick_username_entry.grid(row=3, column=1, sticky="ew", pady=5)

        self.quick_password_label = ttk.Label(self.quick_frame)
        self.quick_password_label.grid(row=3, column=2, sticky="w", padx=(16, 8), pady=5)
        self.quick_password_entry = ttk.Entry(self.quick_frame, textvariable=self.quick_password_var, show="*")
        self.quick_password_entry.grid(row=3, column=3, sticky="ew", pady=5)

        self.quick_show_password = ttk.Checkbutton(
            self.quick_frame,
            variable=self.quick_show_password_var,
            command=self._sync_quick_password_visibility,
        )
        self.quick_show_password.grid(row=3, column=4, sticky="w", padx=(16, 8), pady=5)

        self.quick_add_button = ttk.Button(self.quick_frame, style="Accent.TButton", command=self.quick_add_connection)
        self.quick_add_button.grid(row=3, column=5, sticky="e", pady=5)

        self.search_strip = ttk.Frame(self.quick_frame, style="Panel.TFrame")
        self.search_strip.grid(row=4, column=0, columnspan=6, sticky="ew", pady=(12, 0))
        self.search_strip.columnconfigure(1, weight=1)
        self.search_label = ttk.Label(self.search_strip, style="Section.TLabel")
        self.search_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.search_entry = ttk.Entry(self.search_strip, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self.clear_button = ttk.Button(self.search_strip, command=self._clear_filters)
        self.clear_button.grid(row=0, column=2, sticky="e", padx=(12, 0))
        self.search_hint = ttk.Label(self.search_strip, style="Muted.TLabel")
        self.search_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        content = ttk.Frame(container, style="Root.TFrame")
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self.sidebar = ttk.LabelFrame(content, style="Glow.TLabelframe", padding=16)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 14))
        self.sidebar.columnconfigure(0, weight=1)
        self.sidebar.rowconfigure(10, weight=1)

        self.filters_title = ttk.Label(self.sidebar, style="Section.TLabel")
        self.filters_title.grid(row=0, column=0, sticky="w")
        self.protocol_label = ttk.Label(self.sidebar)
        self.protocol_label.grid(row=1, column=0, sticky="w", pady=(14, 4))
        self.protocol_combo = ttk.Combobox(self.sidebar, state="readonly", textvariable=self.protocol_filter_var, width=24)
        self.protocol_combo.grid(row=2, column=0, sticky="ew")
        self.template_label = ttk.Label(self.sidebar)
        self.template_label.grid(row=3, column=0, sticky="w", pady=(14, 4))
        self.template_combo = ttk.Combobox(self.sidebar, state="readonly", textvariable=self.template_filter_var, width=24)
        self.template_combo.grid(row=4, column=0, sticky="ew")
        self.group_label = ttk.Label(self.sidebar)
        self.group_label.grid(row=5, column=0, sticky="w", pady=(14, 4))
        self.group_combo = ttk.Combobox(self.sidebar, state="readonly", textvariable=self.group_filter_var, width=24)
        self.group_combo.grid(row=6, column=0, sticky="ew")
        self.filter_summary = ttk.Label(self.sidebar, style="Muted.TLabel", wraplength=220, justify="left")
        self.filter_summary.grid(row=7, column=0, sticky="ew", pady=(16, 0))

        self.group_add_title = ttk.Label(self.sidebar, style="Section.TLabel")
        self.group_add_title.grid(row=8, column=0, sticky="w", pady=(24, 6))
        group_add = ttk.Frame(self.sidebar, style="Panel.TFrame")
        group_add.grid(row=9, column=0, sticky="ew")
        group_add.columnconfigure(0, weight=1)
        self.new_group_entry = ttk.Entry(group_add, textvariable=self.new_group_var)
        self.new_group_entry.grid(row=0, column=0, sticky="ew")
        self.add_group_button = ttk.Button(group_add, style="Icon.TButton", command=self.add_group)
        self.add_group_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

        self.sessions_title = ttk.Label(self.sidebar, style="Section.TLabel")
        self.sessions_title.grid(row=10, column=0, sticky="w", pady=(24, 6))
        self.session_list = tk.Listbox(
            self.sidebar,
            height=10,
            bg=PALETTE["field"],
            fg=PALETTE["text"],
            selectbackground=PALETTE["selection"],
            selectforeground=PALETTE["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        self.session_list.grid(row=11, column=0, sticky="nsew")

        main_panel = ttk.Frame(content, style="Panel.TFrame", padding=16)
        main_panel.grid(row=0, column=1, sticky="nsew")
        main_panel.columnconfigure(0, weight=1)
        main_panel.rowconfigure(0, weight=1)
        main_panel.rowconfigure(1, weight=0)

        tree_frame = ttk.Frame(main_panel, style="Card.TFrame", padding=10)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("name", "protocol", "endpoint", "group", "template", "tags")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.column("name", width=240, anchor="w")
        self.tree.column("protocol", width=110, anchor="center")
        self.tree.column("endpoint", width=270, anchor="w")
        self.tree.column("group", width=180, anchor="w")
        self.tree.column("template", width=160, anchor="w")
        self.tree.column("tags", width=240, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.terminal_notebook = ttk.Notebook(main_panel)
        self.terminal_notebook.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        main_panel.rowconfigure(1, weight=1)

        self.task_frame = ttk.LabelFrame(main_panel, padding=14)
        self.task_frame.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        self.task_frame.columnconfigure(1, weight=1)
        self.task_frame.columnconfigure(3, weight=1)

        self.task_target_label = ttk.Label(self.task_frame, style="Section.TLabel")
        self.task_target_label.grid(row=0, column=0, sticky="w")
        self.task_target_value = ttk.Label(self.task_frame, textvariable=self.task_target_var, style="Muted.TLabel")
        self.task_target_value.grid(row=0, column=1, columnspan=3, sticky="w", padx=(8, 0))

        self.actions_title_label = ttk.Label(self.task_frame, style="Section.TLabel")
        self.actions_title_label.grid(row=1, column=0, sticky="w", pady=(14, 6))
        actions = ttk.Frame(self.task_frame, style="Panel.TFrame")
        actions.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(14, 6))
        actions.columnconfigure(4, weight=1)
        self.open_terminal_button = ttk.Button(actions, style="Accent.TButton", command=self.open_terminal)
        self.open_terminal_button.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.open_files_button = ttk.Button(actions, command=self.open_files)
        self.open_files_button.grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.copy_command_button = ttk.Button(actions, command=self.copy_launch_command)
        self.copy_command_button.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.action_status_label = ttk.Label(actions, textvariable=self.action_status_var, style="Muted.TLabel")
        self.action_status_label.grid(row=0, column=4, sticky="w")

        self.service_title_label = ttk.Label(self.task_frame, style="Section.TLabel")
        self.service_title_label.grid(row=2, column=0, sticky="w", pady=(8, 6))
        service_row = ttk.Frame(self.task_frame, style="Panel.TFrame")
        service_row.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(8, 6))
        service_row.columnconfigure(1, weight=1)
        service_row.columnconfigure(3, weight=1)
        self.service_local_port_label = ttk.Label(service_row)
        self.service_local_port_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.service_local_port_entry = ttk.Entry(service_row, textvariable=self.service_local_port_var, width=8)
        self.service_local_port_entry.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self.service_remote_host_label = ttk.Label(service_row)
        self.service_remote_host_label.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.service_remote_host_entry = ttk.Entry(service_row, textvariable=self.service_remote_host_var)
        self.service_remote_host_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12))
        self.service_remote_port_label = ttk.Label(service_row)
        self.service_remote_port_label.grid(row=0, column=4, sticky="w", padx=(0, 8))
        self.service_remote_port_entry = ttk.Entry(service_row, textvariable=self.service_remote_port_var, width=8)
        self.service_remote_port_entry.grid(row=0, column=5, sticky="w", padx=(0, 12))
        self.start_tunnel_button = ttk.Button(service_row, command=self.start_tunnel)
        self.start_tunnel_button.grid(row=0, column=6, sticky="e")

        self.task_preset_label = ttk.Label(self.task_frame)
        self.task_preset_label.grid(row=3, column=0, sticky="w", pady=(12, 6))
        self.task_preset_combo = ttk.Combobox(self.task_frame, state="readonly", textvariable=self.task_preset_var)
        self.task_preset_combo.grid(row=3, column=1, sticky="ew", padx=(8, 12), pady=(12, 6))

        self.task_timeout_label = ttk.Label(self.task_frame)
        self.task_timeout_label.grid(row=3, column=2, sticky="e", pady=(12, 6))
        self.task_timeout_entry = ttk.Entry(self.task_frame, textvariable=self.task_timeout_var, width=10)
        self.task_timeout_entry.grid(row=3, column=3, sticky="w", padx=(8, 0), pady=(12, 6))

        self.task_command_label = ttk.Label(self.task_frame)
        self.task_command_label.grid(row=4, column=0, sticky="w", pady=(6, 6))
        self.task_command_entry = ttk.Entry(self.task_frame, textvariable=self.task_command_var)
        self.task_command_entry.grid(row=4, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(6, 6))

        self.task_execute_button = ttk.Button(self.task_frame, style="Accent.TButton", command=self.execute_task)
        self.task_execute_button.grid(row=5, column=3, sticky="e", pady=(8, 8))
        self.task_test_button = ttk.Button(self.task_frame, command=self.test_connection)
        self.task_test_button.grid(row=5, column=2, sticky="e", padx=(0, 8), pady=(8, 8))
        self.task_summary_label = ttk.Label(self.task_frame, textvariable=self.task_summary_var, style="Muted.TLabel")
        self.task_summary_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 8))

        self.task_output = tk.Text(
            self.task_frame,
            height=8,
            bg=PALETTE["field"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["accent"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            relief="flat",
            wrap="word",
        )
        self.task_output.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        self.task_history_label = ttk.Label(self.task_frame, style="Section.TLabel")
        self.task_history_label.grid(row=7, column=0, sticky="w", pady=(0, 6))
        self.task_history_list = tk.Listbox(
            self.task_frame,
            height=5,
            bg=PALETTE["field"],
            fg=PALETTE["text"],
            selectbackground=PALETTE["selection"],
            selectforeground=PALETTE["bg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        self.task_history_list.grid(row=8, column=0, columnspan=4, sticky="ew")

        self.empty_label = ttk.Label(main_panel, style="Empty.TLabel", textvariable=self.empty_var, anchor="center")
        self.empty_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.button_bar = ttk.Frame(main_panel, style="Panel.TFrame")
        self.button_bar.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        self.add_button = ttk.Button(self.button_bar, style="Accent.TButton", command=self.add_connection)
        self.add_button.pack(side="left")
        self.edit_button = ttk.Button(self.button_bar, command=self.edit_connection)
        self.edit_button.pack(side="left", padx=8)
        self.delete_button = ttk.Button(self.button_bar, style="Danger.TButton", command=self.delete_connection)
        self.delete_button.pack(side="left")
        self.connect_button = ttk.Button(self.button_bar, style="Accent.TButton", command=self.connect_connection)
        self.connect_button.pack(side="right")
        self.refresh_button = ttk.Button(self.button_bar, command=self.refresh)
        self.refresh_button.pack(side="right", padx=(0, 8))

        self.status_label = ttk.Label(container, style="Status.TLabel", textvariable=self.status_var, padding=(18, 10))
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(14, 0))

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_args: self.refresh())
        self.protocol_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        self.template_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        self.group_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        self.quick_protocol_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_quick_protocol_change())
        self.quick_template_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_quick_template_change())
        self.language_combo.bind("<<ComboboxSelected>>", lambda _event: self._change_language())
        self.tree.bind("<Double-1>", lambda _event: self.connect_connection())
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._on_selected_profile_changed())
        self.task_preset_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_selected_preset())
        self.task_history_list.bind("<<ListboxSelect>>", lambda _event: self._show_selected_history())
        self.session_list.bind("<Double-1>", lambda _event: self.open_terminal_tab())

    def _apply_text(self) -> None:
        self.root.title(self.title_override or self.i18n.t("app.title"))
        self.brand_label.configure(text=self.i18n.t("app.brand"))
        self.subtitle_label.configure(text=self.i18n.t("app.subtitle"))
        self.language_label.configure(text=self.i18n.t("header.language"))
        self.quick_frame.configure(text=self.i18n.t("quick.panel"))
        self.quick_title_label.configure(text=self.i18n.t("quick.title"))
        self.quick_name_label.configure(text=self.i18n.t("editor.name"))
        self.quick_protocol_label.configure(text=self.i18n.t("editor.protocol_label"))
        self.quick_template_label.configure(text=self.i18n.t("editor.template"))
        self.quick_host_label.configure(text=self.i18n.t("editor.host"))
        self.quick_port_label.configure(text=self.i18n.t("editor.port"))
        self.quick_group_label.configure(text=self.i18n.t("editor.group"))
        self.quick_username_label.configure(text=self.i18n.t("editor.username"))
        self.quick_password_label.configure(text=self.i18n.t("editor.password"))
        self.quick_show_password.configure(text=self.i18n.t("editor.show_password"))
        self.quick_add_button.configure(text=self.i18n.t("quick.add"))
        self.search_label.configure(text=self.i18n.t("header.search"))
        self.search_hint.configure(text=self.i18n.t("header.search_hint"))
        self.clear_button.configure(text=self.i18n.t("header.clear"))
        self.filters_title.configure(text=self.i18n.t("filters.title"))
        self.protocol_label.configure(text=self.i18n.t("filters.protocol"))
        self.template_label.configure(text=self.i18n.t("filters.template"))
        self.group_label.configure(text=self.i18n.t("filters.group"))
        self.filter_summary.configure(text=self.i18n.t("filters.summary"))
        self.group_add_title.configure(text=self.i18n.t("groups.add_title"))
        self.sessions_title.configure(text=self.i18n.t("sessions.title"))
        self.add_group_button.configure(text="+")
        self.add_button.configure(text=self.i18n.t("actions.add"))
        self.edit_button.configure(text=self.i18n.t("actions.edit"))
        self.delete_button.configure(text=self.i18n.t("actions.delete"))
        self.connect_button.configure(text=self.i18n.t("actions.connect"))
        self.refresh_button.configure(text=self.i18n.t("actions.refresh"))
        self.task_frame.configure(text=self.i18n.t("tasks.panel"))
        self.task_target_label.configure(text=self.i18n.t("tasks.target"))
        self.actions_title_label.configure(text=self.i18n.t("actions.panel"))
        self.open_terminal_button.configure(text=self.i18n.t("actions.terminal"))
        self.open_files_button.configure(text=self.i18n.t("actions.files"))
        self.copy_command_button.configure(text=self.i18n.t("actions.copy_command"))
        self.service_title_label.configure(text=self.i18n.t("service.panel"))
        self.service_local_port_label.configure(text=self.i18n.t("service.local_port"))
        self.service_remote_host_label.configure(text=self.i18n.t("service.remote_host"))
        self.service_remote_port_label.configure(text=self.i18n.t("service.remote_port"))
        self.start_tunnel_button.configure(text=self.i18n.t("service.start_tunnel"))
        self.task_preset_label.configure(text=self.i18n.t("tasks.preset"))
        self.task_timeout_label.configure(text=self.i18n.t("tasks.timeout"))
        self.task_command_label.configure(text=self.i18n.t("tasks.command"))
        self.task_execute_button.configure(text=self.i18n.t("actions.execute"))
        self.task_test_button.configure(text=self.i18n.t("actions.test"))
        self.task_history_label.configure(text=self.i18n.t("tasks.history"))
        for column_key in ("name", "protocol", "endpoint", "group", "template", "tags"):
            self.tree.heading(column_key, text=self.i18n.t(f"table.{column_key}"))
        self._refresh_filter_options()
        self._update_status(0, 0)
        self._refresh_task_panel()

    def _change_language(self) -> None:
        selected_label = self.language_var.get()
        selected_language = self.language_label_map.get(selected_label, selected_label)
        self.i18n.set_language(selected_language)
        self.language_var.set(self.i18n.t(f"language.{self.i18n.language}"))
        self._apply_text()
        self.refresh()

    def _refresh_filter_options(self) -> None:
        all_label = self.i18n.t("filters.all")

        protocol_values = [all_label]
        self.protocol_filter_map = {all_label: ALL_FILTER}
        for protocol in Protocol:
            label = self.i18n.protocol_text(protocol)
            protocol_values.append(label)
            self.protocol_filter_map[label] = protocol.value
        current_protocol = self.protocol_filter_map.get(self.protocol_filter_var.get(), self.protocol_filter_var.get())
        self.protocol_combo.configure(values=protocol_values)
        self.protocol_filter_var.set(self._display_from_value(self.protocol_filter_map, current_protocol))

        template_values = [all_label]
        self.template_filter_map = {all_label: ALL_FILTER}
        for template in DeviceTemplate:
            label = self.i18n.template_text(template)
            template_values.append(label)
            self.template_filter_map[label] = template.value
        current_template = self.template_filter_map.get(self.template_filter_var.get(), self.template_filter_var.get())
        self.template_combo.configure(values=template_values)
        self.template_filter_var.set(self._display_from_value(self.template_filter_map, current_template))

        groups = sorted({profile.group for profile in self.all_profiles if profile.group} | self.manual_groups)
        group_values = [all_label] + groups
        self.group_filter_map = {all_label: ALL_FILTER, **{group: group for group in groups}}
        current_group = self.group_filter_map.get(self.group_filter_var.get(), self.group_filter_var.get())
        self.group_combo.configure(values=group_values)
        self.group_filter_var.set(self._display_from_value(self.group_filter_map, current_group))

        self.language_label_map = {self.i18n.t(f"language.{lang}"): lang for lang in SUPPORTED_LANGUAGES}
        self.language_combo.configure(values=list(self.language_label_map.keys()))
        self.language_var.set(self.i18n.t(f"language.{self.i18n.language}"))

        self.quick_protocol_map = {self.i18n.protocol_text(protocol): protocol.value for protocol in Protocol}
        self.quick_protocol_combo.configure(values=list(self.quick_protocol_map.keys()))
        self.quick_protocol_var.set(self._display_from_value(self.quick_protocol_map, self.quick_protocol_var.get()))

        self.quick_template_map = {self.i18n.template_text(template): template.value for template in DeviceTemplate}
        self.quick_template_combo.configure(values=list(self.quick_template_map.keys()))
        self.quick_template_var.set(self._display_from_value(self.quick_template_map, self.quick_template_var.get()))

    def _display_from_value(self, mapping: dict[str, str], value: str) -> str:
        for label, mapped in mapping.items():
            if mapped == value:
                return label
        return next(iter(mapping))

    def refresh(self) -> None:
        self.all_profiles = self.service.list_connections()
        self._refresh_filter_options()

        profiles = self._filtered_profiles()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for profile in profiles:
            self.tree.insert(
                "",
                "end",
                iid=profile.id,
                values=(
                    profile.name,
                    self.i18n.protocol_text(profile.protocol),
                    self._profile_endpoint(profile),
                    profile.group,
                    self.i18n.template_text(profile.device_template),
                    ", ".join(profile.tags),
                ),
            )

        self.session_list.delete(0, "end")
        for profile in profiles:
            self.session_list.insert("end", f"{self.i18n.protocol_text(profile.protocol)}  {profile.name}  {self._profile_endpoint(profile)}")

        self.empty_var.set(self.i18n.t("messages.empty") if not profiles else "")
        self._update_status(len(profiles), len(self.all_profiles))
        self._load_recent_tasks()
        self._on_selected_profile_changed()

    def _filtered_profiles(self) -> list[ConnectionProfile]:
        query = self.search_var.get().strip().lower()
        protocol_filter = self.protocol_filter_map.get(self.protocol_filter_var.get(), self.protocol_filter_var.get())
        template_filter = self.template_filter_map.get(self.template_filter_var.get(), self.template_filter_var.get())
        group_filter = self.group_filter_map.get(self.group_filter_var.get(), self.group_filter_var.get())

        filtered: list[ConnectionProfile] = []
        for profile in self.all_profiles:
            if protocol_filter != ALL_FILTER and profile.protocol.value != protocol_filter:
                continue
            if template_filter != ALL_FILTER and profile.device_template.value != template_filter:
                continue
            if group_filter != ALL_FILTER and profile.group != group_filter:
                continue
            searchable = " ".join(
                [
                    profile.name,
                    profile.group,
                    profile.device_template.value,
                    " ".join(profile.tags),
                    profile.notes,
                    self._profile_endpoint(profile),
                ]
            ).lower()
            if query and query not in searchable:
                continue
            filtered.append(profile)
        return filtered

    def _update_status(self, visible_count: int, total_count: int) -> None:
        self.status_var.set(
            f"{self.i18n.t('status.path')}: {self.service.storage.path}   |   "
            f"{self.i18n.t('status.connections')}: {visible_count}/{total_count}   |   "
            f"{self.i18n.t('status.language')}: {self.i18n.t(f'language.{self.i18n.language}')}"
        )

    def _profile_endpoint(self, profile: ConnectionProfile) -> str:
        config = profile.protocol_config
        if profile.protocol == Protocol.SERIAL:
            return f"{config.port_name} @ {config.baudrate}"
        return f"{config.host}:{config.port}"

    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.protocol_filter_var.set(self._display_from_value(self.protocol_filter_map, ALL_FILTER))
        self.template_filter_var.set(self._display_from_value(self.template_filter_map, ALL_FILTER))
        self.group_filter_var.set(self._display_from_value(self.group_filter_map, ALL_FILTER))
        self.refresh()

    def _on_quick_template_change(self) -> None:
        template_value = self.quick_template_map.get(self.quick_template_var.get(), self.quick_template_var.get())
        self.quick_template_var.set(self._display_from_value(self.quick_template_map, template_value))
        protocol = TEMPLATE_PROTOCOL_MAP[DeviceTemplate(template_value)]
        self.quick_protocol_var.set(self._display_from_value(self.quick_protocol_map, protocol.value))
        self._apply_quick_protocol_defaults(protocol)

    def _on_quick_protocol_change(self) -> None:
        protocol_value = self.quick_protocol_map.get(self.quick_protocol_var.get(), self.quick_protocol_var.get())
        self.quick_protocol_var.set(self._display_from_value(self.quick_protocol_map, protocol_value))
        self._apply_quick_protocol_defaults(Protocol(protocol_value))

    def _apply_quick_protocol_defaults(self, protocol: Protocol) -> None:
        default_ports = {
            Protocol.SSH: "22",
            Protocol.TELNET: "23",
            Protocol.RDP: "3389",
        }
        if protocol in default_ports:
            self.quick_port_var.set(default_ports[protocol])
        elif protocol == Protocol.SERIAL:
            self.quick_port_var.set("9600")

    def _sync_quick_password_visibility(self) -> None:
        self.quick_password_entry.configure(show="" if self.quick_show_password_var.get() else "*")

    def add_group(self) -> None:
        group = self.new_group_var.get().strip()
        if not group:
            return
        self.manual_groups.add(group)
        self.quick_group_var.set(group)
        self.group_filter_var.set(group)
        self.new_group_var.set("")
        self.refresh()

    def quick_add_connection(self) -> None:
        try:
            protocol_value = self.quick_protocol_map.get(self.quick_protocol_var.get(), self.quick_protocol_var.get())
            template_value = self.quick_template_map.get(self.quick_template_var.get(), self.quick_template_var.get())
            protocol = Protocol(protocol_value)
            template = DeviceTemplate(template_value)
            name = self.quick_name_var.get().strip() or self.quick_host_var.get().strip()
            group = self.quick_group_var.get().strip() or "default"
            tags = [tag.strip() for tag in self.quick_tags_var.get().split(",") if tag.strip()]

            if protocol == Protocol.SSH:
                config = SSHConfig(
                    host=self.quick_host_var.get().strip(),
                    port=int(self.quick_port_var.get() or 22),
                    username=self.quick_username_var.get().strip(),
                    password=self.quick_password_var.get(),
                )
            elif protocol == Protocol.TELNET:
                config = TelnetConfig(
                    host=self.quick_host_var.get().strip(),
                    port=int(self.quick_port_var.get() or 23),
                    username=self.quick_username_var.get().strip(),
                    password=self.quick_password_var.get(),
                )
            elif protocol == Protocol.RDP:
                config = RDPConfig(
                    host=self.quick_host_var.get().strip(),
                    port=int(self.quick_port_var.get() or 3389),
                    username=self.quick_username_var.get().strip(),
                )
            else:
                config = SerialConfig(
                    port_name=self.quick_host_var.get().strip() or "COM1",
                    baudrate=int(self.quick_port_var.get() or 9600),
                )

            created = self.service.create_connection(
                ConnectionCreateRequest(
                    name=name,
                    protocol=protocol,
                    group=group,
                    tags=tags,
                    notes="",
                    device_template=template,
                    protocol_config=config,
                )
            )
            self.quick_name_var.set("")
            self.quick_host_var.set("")
            self.quick_password_var.set("")
            self.refresh()
            self.tree.selection_set(created.id)
            self.tree.see(created.id)
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.validation_error"), str(exc), parent=self.root)

    def selected_profile(self) -> ConnectionProfile | None:
        selection = self.tree.selection()
        if selection:
            return self.service.get_connection(selection[0])
        list_selection = self.session_list.curselection()
        if list_selection:
            profiles = self._filtered_profiles()
            if list_selection[0] < len(profiles):
                profile = profiles[list_selection[0]]
                self.tree.selection_set(profile.id)
                return profile
        return None

    def _ssh_target(self, profile: ConnectionProfile) -> str:
        config = profile.protocol_config
        username = getattr(config, "username", "")
        host = getattr(config, "host", "")
        return f"{username}@{host}" if username else host

    def _terminal_command(self, profile: ConnectionProfile) -> list[str]:
        config = profile.protocol_config
        if profile.protocol == Protocol.SSH:
            assert isinstance(config, SSHConfig)
            command = ["ssh", "-p", str(config.port)]
            if config.private_key_path:
                command.extend(["-i", config.private_key_path])
            command.append(self._ssh_target(profile))
            return command
        if profile.protocol == Protocol.RDP:
            assert isinstance(config, RDPConfig)
            host_spec = config.host if config.port == 3389 else f"{config.host}:{config.port}"
            return ["mstsc", "/v:" + host_spec]
        if profile.protocol == Protocol.TELNET:
            assert isinstance(config, TelnetConfig)
            return ["telnet", config.host, str(config.port)]
        if profile.protocol == Protocol.SERIAL:
            assert isinstance(config, SerialConfig)
            return ["mode", config.port_name]
        raise RuntimeError(f"Unsupported protocol: {profile.protocol}")

    def _files_command(self, profile: ConnectionProfile) -> list[str]:
        config = profile.protocol_config
        if profile.protocol != Protocol.SSH:
            raise RuntimeError("File browser is available for SSH profiles through SFTP.")
        assert isinstance(config, SSHConfig)
        command = ["sftp", "-P", str(config.port)]
        if config.private_key_path:
            command.extend(["-i", config.private_key_path])
        command.append(self._ssh_target(profile))
        return command

    def _tunnel_command(self, profile: ConnectionProfile) -> list[str]:
        config = profile.protocol_config
        if profile.protocol != Protocol.SSH:
            raise RuntimeError("Service tunnels require an SSH profile.")
        assert isinstance(config, SSHConfig)
        local_port = int(self.service_local_port_var.get() or "8080")
        remote_host = self.service_remote_host_var.get().strip() or "127.0.0.1"
        remote_port = int(self.service_remote_port_var.get() or "80")
        command = ["ssh", "-N", "-L", f"{local_port}:{remote_host}:{remote_port}", "-p", str(config.port)]
        if config.private_key_path:
            command.extend(["-i", config.private_key_path])
        command.append(self._ssh_target(profile))
        return command

    def _selected_or_message(self) -> ConnectionProfile | None:
        profile = self.selected_profile()
        if profile is None:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return None
        return profile

    def open_terminal(self) -> None:
        self.open_terminal_tab()

    def open_terminal_tab(self) -> None:
        profile = self._selected_or_message()
        if profile is None:
            return
        tab = ttk.Frame(self.terminal_notebook, style="Panel.TFrame")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        title = f"{profile.name} [{profile.protocol.value}]"
        self.terminal_notebook.add(tab, text=title)
        self.terminal_notebook.select(tab)
        start_gui_session_tab(profile, tab)
        self.action_status_var.set(self.i18n.t("actions.started", action=self.i18n.t("actions.terminal")))

    def open_files(self) -> None:
        profile = self._selected_or_message()
        if profile is None:
            return
        try:
            command = self._files_command(profile)
            open_external_terminal(command, f"{profile.name} SFTP")
            self.action_status_var.set(self.i18n.t("actions.started", action=self.i18n.t("actions.files")))
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.connect_error"), str(exc), parent=self.root)

    def copy_launch_command(self) -> None:
        profile = self._selected_or_message()
        if profile is None:
            return
        command = subprocess.list2cmdline(self._terminal_command(profile))
        self.root.clipboard_clear()
        self.root.clipboard_append(command)
        self.action_status_var.set(self.i18n.t("actions.copied"))

    def start_tunnel(self) -> None:
        profile = self._selected_or_message()
        if profile is None:
            return
        try:
            command = self._tunnel_command(profile)
            open_external_terminal(command, f"{profile.name} Tunnel")
            self.action_status_var.set(self.i18n.t("actions.started", action=self.i18n.t("service.start_tunnel")))
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.connect_error"), str(exc), parent=self.root)

    def _on_selected_profile_changed(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            self.task_target_var.set(self.i18n.t("tasks.no_selection"))
        else:
            self.task_target_var.set(f"{profile.name} [{self.i18n.protocol_text(profile.protocol)}]")
        self._refresh_task_panel()

    def _refresh_task_panel(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            self.task_preset_map = {self.i18n.t("tasks.no_presets"): ""}
            self.task_preset_combo.configure(values=list(self.task_preset_map.keys()))
            self.task_preset_var.set(next(iter(self.task_preset_map)))
            self.task_summary_var.set(self.i18n.t("tasks.summary_idle"))
            return
        presets = self.task_service.presets(profile.device_template)
        if presets:
            self.task_preset_map = {
                f"{item['title']} / {item['title_zh']}": str(item["id"])
                for item in presets
            }
        else:
            self.task_preset_map = {self.i18n.t("tasks.no_presets"): ""}
        values = list(self.task_preset_map.keys())
        self.task_preset_combo.configure(values=values)
        if self.task_preset_var.get() not in self.task_preset_map:
            self.task_preset_var.set(values[0])
            self._apply_selected_preset()
        self.task_summary_var.set(self.i18n.t("tasks.summary_ready", template=self.i18n.template_text(profile.device_template)))

    def _apply_selected_preset(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            return
        preset_id = self.task_preset_map.get(self.task_preset_var.get(), "")
        for item in self.task_service.presets(profile.device_template):
            if item["id"] == preset_id:
                self.task_command_var.set(str(item["command"]))
                return

    def _load_recent_tasks(self) -> None:
        records = self.task_service.recent_history(limit=10)
        self.recent_tasks = [record.model_dump(mode="json") for record in records]
        self.task_history_list.delete(0, "end")
        for record in self.recent_tasks:
            summary = f"[{record['kind']}] {record['connection_name']} :: {record['status']}"
            if record.get("command"):
                summary += f" :: {record['command'][:60]}"
            self.task_history_list.insert("end", summary)

    def _show_selected_history(self) -> None:
        selection = self.task_history_list.curselection()
        if not selection:
            return
        record = self.recent_tasks[selection[0]]
        lines = [
            f"{self.i18n.t('tasks.history_kind')}: {record['kind']}",
            f"{self.i18n.t('tasks.history_status')}: {record['status']}",
            f"{self.i18n.t('tasks.history_connection')}: {record['connection_name']}",
            f"{self.i18n.t('tasks.command')}: {record.get('command', '')}",
            f"stdout:\n{record.get('stdout', '')}",
            f"stderr:\n{record.get('stderr', '')}",
        ]
        self._set_task_output("\n".join(lines))

    def _set_task_output(self, text: str) -> None:
        self.task_output.delete("1.0", "end")
        self.task_output.insert("1.0", text.strip() or self.i18n.t("tasks.output_empty"))

    def execute_task(self) -> None:
        profile = self.selected_profile()
        if not profile:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return
        try:
            timeout = float(self.task_timeout_var.get() or "10")
            preset_id = self.task_preset_map.get(self.task_preset_var.get(), "") or None
            result = self.task_service.execute(
                profile,
                TaskExecuteRequest(
                    connection_id=profile.id,
                    command=self.task_command_var.get(),
                    preset_id=preset_id,
                    timeout=timeout,
                ),
            )
            self.task_summary_var.set(
                self.i18n.t("tasks.summary_result", status=result.status, duration=result.duration_ms)
            )
            self._set_task_output(
                f"status: {result.status}\nexit_code: {result.exit_code}\nprotocol: {result.protocol.value}\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )
            self._load_recent_tasks()
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.connect_error"), str(exc))

    def test_connection(self) -> None:
        profile = self.selected_profile()
        if not profile:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return
        try:
            timeout = ConnectionTestRequest(timeout=float(self.task_timeout_var.get() or "5")).timeout
            result = self.task_service.test(profile, timeout=timeout)
            self.task_summary_var.set(
                self.i18n.t("tasks.summary_test", reachable=str(result.reachable), authenticated=str(result.authenticated))
            )
            self._set_task_output(
                f"reachable: {result.reachable}\nauthenticated: {result.authenticated}\nprotocol: {result.protocol.value}\nmessage: {result.message}\nerror: {result.error}"
            )
            self._load_recent_tasks()
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.connect_error"), str(exc))

    def add_connection(self) -> None:
        editor = ConnectionEditor(self.root, self.i18n)
        profile = editor.open()
        if profile:
            self.service.create_connection(profile)
            self.refresh()

    def edit_connection(self) -> None:
        selected = self.selected_profile()
        if not selected:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return
        editor = ConnectionEditor(self.root, self.i18n, selected)
        request = editor.open()
        if request:
            self.service.update_connection(
                selected.id,
                ConnectionUpdateRequest(
                    name=request.name,
                    protocol=request.protocol,
                    group=request.group,
                    tags=request.tags,
                    notes=request.notes,
                    device_template=request.device_template,
                    protocol_config=request.protocol_config,
                ),
            )
            self.refresh()

    def delete_connection(self) -> None:
        selected = self.selected_profile()
        if not selected:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return
        if messagebox.askyesno(
            self.i18n.t("messages.delete_title"),
            self.i18n.t("messages.delete_confirm", name=selected.name),
        ):
            self.service.delete_connection(selected.id)
            self.refresh()

    def connect_connection(self) -> None:
        selected = self.selected_profile()
        if not selected:
            messagebox.showinfo(self.i18n.t("messages.select_title"), self.i18n.t("messages.select_body"))
            return
        try:
            self.launcher.connect(selected, root=self.root)
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.connect_error"), str(exc))

    def run(self) -> None:
        self.root.mainloop()

    def _pulse_header(self) -> None:
        if not self.root.winfo_exists():
            return
        width = max(self.header_canvas.winfo_width(), 1)
        self.header_canvas.delete("pulse")
        offset = (self.motion_phase * 17) % max(width, 1)
        self.header_canvas.create_rectangle(0, 1, width, 3, fill=PALETTE["border"], outline="", tags="pulse")
        self.header_canvas.create_rectangle(offset - 120, 0, offset, 4, fill=PALETTE["accent"], outline="", tags="pulse")
        self.header_canvas.create_rectangle(offset, 0, offset + 36, 4, fill=PALETTE["hot"], outline="", tags="pulse")
        self.motion_phase += 1
        self.root.after(70, self._pulse_header)


class ConnectionEditor:
    def __init__(self, parent: tk.Misc, i18n: I18N, existing: ConnectionProfile | None = None) -> None:
        self.i18n = i18n
        self.existing = existing
        self.window = tk.Toplevel(parent, bg=PALETTE["bg"])
        self.window.title(i18n.t("editor.edit_title") if existing else i18n.t("editor.new_title"))
        self.window.geometry("820x760")
        self.window.minsize(720, 700)
        self.window.transient(parent)
        self.window.grab_set()
        apply_theme(self.window)
        self.result: ConnectionCreateRequest | None = None

        existing_config = existing.protocol_config if existing else None
        self.vars = {
            "name": tk.StringVar(value=existing.name if existing else ""),
            "group": tk.StringVar(value=existing.group if existing else "default"),
            "tags": tk.StringVar(value=",".join(existing.tags) if existing else ""),
            "template": tk.StringVar(value=(existing.device_template.value if existing else DeviceTemplate.LINUX.value)),
            "protocol": tk.StringVar(value=(existing.protocol.value if existing else Protocol.SSH.value)),
            "host": tk.StringVar(value=getattr(existing_config, "host", "")),
            "port": tk.StringVar(value=str(getattr(existing_config, "port", 22))),
            "username": tk.StringVar(value=getattr(existing_config, "username", "")),
            "password": tk.StringVar(value=getattr(existing_config, "password", "")),
            "private_key_path": tk.StringVar(value=getattr(existing_config, "private_key_path", "")),
            "port_name": tk.StringVar(value=getattr(existing_config, "port_name", "COM1")),
            "baudrate": tk.StringVar(value=str(getattr(existing_config, "baudrate", 9600))),
        }

        self.protocol_display_map = {self.i18n.protocol_text(protocol): protocol.value for protocol in Protocol}
        self.template_display_map = {self.i18n.template_text(template): template.value for template in DeviceTemplate}
        self.protocol_selector_var = tk.StringVar(value=self._protocol_label(self.vars["protocol"].get()))
        self.template_selector_var = tk.StringVar(value=self._template_label(self.vars["template"].get()))
        self.show_password_var = tk.BooleanVar(value=False)
        self.protocol_fields: list[ttk.Widget] = []
        self.password_entry: ttk.Entry | None = None
        self.password_toggle: ttk.Checkbutton | None = None

        self._build()
        self._render_protocol_fields()

    def _build(self) -> None:
        frame = ttk.Frame(self.window, style="Root.TFrame", padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        general = ttk.LabelFrame(frame, text=self.i18n.t("editor.general"), padding=14)
        general.grid(row=0, column=0, sticky="ew")
        general.columnconfigure(1, weight=1)
        general.columnconfigure(3, weight=1)

        ttk.Label(general, text=self.i18n.t("editor.general_hint"), style="Muted.TLabel", wraplength=640, justify="left").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )

        self._entry_row(general, 1, 0, self.i18n.t("editor.name"), self.vars["name"])
        self._entry_row(general, 1, 2, self.i18n.t("editor.group"), self.vars["group"])
        self._entry_row(general, 2, 0, self.i18n.t("editor.tags"), self.vars["tags"])
        ttk.Label(general, text=self.i18n.t("editor.tags_hint"), style="Muted.TLabel").grid(row=3, column=1, sticky="w", pady=(2, 0))

        ttk.Label(general, text=self.i18n.t("editor.template")).grid(row=2, column=2, sticky="w", padx=(16, 8))
        self.template_combo = ttk.Combobox(
            general,
            state="readonly",
            textvariable=self.template_selector_var,
            values=list(self.template_display_map.keys()),
        )
        self.template_combo.grid(row=2, column=3, sticky="ew")
        self.template_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_template_change())

        protocol_box = ttk.LabelFrame(frame, text=self.i18n.t("editor.protocol"), padding=14)
        protocol_box.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        protocol_box.columnconfigure(1, weight=1)

        ttk.Label(protocol_box, text=self.i18n.t("editor.protocol_label")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.protocol_combo = ttk.Combobox(
            protocol_box,
            state="readonly",
            textvariable=self.protocol_selector_var,
            values=list(self.protocol_display_map.keys()),
        )
        self.protocol_combo.grid(row=0, column=1, sticky="ew")
        self.protocol_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_protocol_change())

        self.protocol_hint = ttk.Label(protocol_box, style="Muted.TLabel", wraplength=620, justify="left")
        self.protocol_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 12))

        self.protocol_frame = ttk.Frame(protocol_box, style="Panel.TFrame")
        self.protocol_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.protocol_frame.columnconfigure(1, weight=1)

        notes_box = ttk.LabelFrame(frame, text=self.i18n.t("editor.notes"), padding=14)
        notes_box.grid(row=2, column=0, sticky="nsew", pady=(16, 0))
        notes_box.columnconfigure(0, weight=1)
        notes_box.rowconfigure(1, weight=1)

        ttk.Label(notes_box, text=self.i18n.t("editor.notes_hint"), style="Muted.TLabel", wraplength=640, justify="left").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        self.notes_text = tk.Text(
            notes_box,
            height=6,
            bg=PALETTE["field"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["accent"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            relief="flat",
            wrap="word",
        )
        self.notes_text.grid(row=1, column=0, sticky="nsew")
        if self.existing:
            self.notes_text.insert("1.0", self.existing.notes)

        buttons = ttk.Frame(frame, style="Root.TFrame")
        buttons.grid(row=3, column=0, sticky="e", pady=(18, 0))
        ttk.Button(buttons, text=self.i18n.t("editor.save"), style="Accent.TButton", command=self._save).pack(side="left")
        ttk.Button(buttons, text=self.i18n.t("editor.cancel"), command=self.window.destroy).pack(side="left", padx=(8, 0))

    def _entry_row(self, parent: ttk.Widget, row: int, column: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(16 if column else 0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=column + 1, sticky="ew", pady=4)

    def _protocol_label(self, protocol_value: str) -> str:
        return self.i18n.protocol_text(Protocol(protocol_value))

    def _template_label(self, template_value: str) -> str:
        return self.i18n.template_text(DeviceTemplate(template_value))

    def _on_template_change(self) -> None:
        template_value = self.template_display_map[self.template_selector_var.get()]
        self.vars["template"].set(template_value)
        mapped_protocol = TEMPLATE_PROTOCOL_MAP[DeviceTemplate(template_value)].value
        self.vars["protocol"].set(mapped_protocol)
        self.protocol_selector_var.set(self._protocol_label(mapped_protocol))
        self._apply_protocol_defaults(Protocol(mapped_protocol))
        self._render_protocol_fields()

    def _on_protocol_change(self) -> None:
        protocol_value = self.protocol_display_map[self.protocol_selector_var.get()]
        self.vars["protocol"].set(protocol_value)
        self._apply_protocol_defaults(Protocol(protocol_value))
        self._render_protocol_fields()

    def _apply_protocol_defaults(self, protocol: Protocol) -> None:
        if protocol == Protocol.SSH and not self.vars["port"].get():
            self.vars["port"].set("22")
        elif protocol == Protocol.TELNET and not self.vars["port"].get():
            self.vars["port"].set("23")
        elif protocol == Protocol.RDP and not self.vars["port"].get():
            self.vars["port"].set("3389")
        elif protocol == Protocol.SERIAL and not self.vars["baudrate"].get():
            self.vars["baudrate"].set("9600")

    def _render_protocol_fields(self) -> None:
        for widget in self.protocol_fields:
            widget.destroy()
        self.protocol_fields.clear()
        self.password_entry = None
        self.password_toggle = None

        protocol = Protocol(self.vars["protocol"].get())
        self.protocol_hint.configure(text=self.i18n.t(f"editor.protocol_hint.{protocol.value}"))

        fields: list[tuple[str, str]] = [
            (self.i18n.t("editor.host"), "host"),
            (self.i18n.t("editor.port"), "port"),
        ]
        if protocol == Protocol.SSH:
            fields.append((self.i18n.t("editor.private_key"), "private_key_path"))
        elif protocol == Protocol.SERIAL:
            fields = [
                (self.i18n.t("editor.port_name"), "port_name"),
                (self.i18n.t("editor.baudrate"), "baudrate"),
            ]
        elif protocol == Protocol.RDP:
            fields = [
                (self.i18n.t("editor.host"), "host"),
                (self.i18n.t("editor.port"), "port"),
                (self.i18n.t("editor.username"), "username"),
            ]

        for row, (label_text, key) in enumerate(fields):
            label = ttk.Label(self.protocol_frame, text=label_text)
            entry = ttk.Entry(self.protocol_frame, textvariable=self.vars[key])
            label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            self.protocol_fields.extend([label, entry])

        if protocol in {Protocol.SSH, Protocol.TELNET}:
            row = len(fields)
            credentials = ttk.LabelFrame(self.protocol_frame, text=self.i18n.t("editor.credentials"), padding=12)
            credentials.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
            credentials.columnconfigure(1, weight=1)
            hint = ttk.Label(
                credentials,
                text=self.i18n.t("editor.credentials_hint"),
                style="Muted.TLabel",
                wraplength=560,
                justify="left",
            )
            hint.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
            username_label = ttk.Label(credentials, text=self.i18n.t("editor.username"))
            username_entry = ttk.Entry(credentials, textvariable=self.vars["username"])
            password_label = ttk.Label(credentials, text=self.i18n.t("editor.password"))
            self.password_entry = ttk.Entry(credentials, textvariable=self.vars["password"], show="*")
            self.password_toggle = ttk.Checkbutton(
                credentials,
                text=self.i18n.t("editor.show_password"),
                variable=self.show_password_var,
                command=self._sync_password_visibility,
            )
            username_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
            username_entry.grid(row=1, column=1, sticky="ew", pady=6)
            password_label.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
            self.password_entry.grid(row=2, column=1, sticky="ew", pady=6)
            self.password_toggle.grid(row=3, column=1, sticky="w", pady=(2, 0))
            self.protocol_fields.extend(
                [
                    credentials,
                    hint,
                    username_label,
                    username_entry,
                    password_label,
                    self.password_entry,
                    self.password_toggle,
                ]
            )
            self._sync_password_visibility()

    def _sync_password_visibility(self) -> None:
        if self.password_entry is not None:
            self.password_entry.configure(show="" if self.show_password_var.get() else "*")

    def _save(self) -> None:
        try:
            protocol = Protocol(self.vars["protocol"].get())
            template = DeviceTemplate(self.vars["template"].get())
            notes = self.notes_text.get("1.0", "end").strip()
            if protocol == Protocol.SSH:
                config = SSHConfig(
                    host=self.vars["host"].get(),
                    port=int(self.vars["port"].get() or 22),
                    username=self.vars["username"].get(),
                    password=self.vars["password"].get(),
                    private_key_path=self.vars["private_key_path"].get(),
                )
            elif protocol == Protocol.TELNET:
                config = TelnetConfig(
                    host=self.vars["host"].get(),
                    port=int(self.vars["port"].get() or 23),
                    username=self.vars["username"].get(),
                    password=self.vars["password"].get(),
                )
            elif protocol == Protocol.SERIAL:
                config = SerialConfig(
                    port_name=self.vars["port_name"].get(),
                    baudrate=int(self.vars["baudrate"].get() or 9600),
                )
            else:
                config = RDPConfig(
                    host=self.vars["host"].get(),
                    port=int(self.vars["port"].get() or 3389),
                    username=self.vars["username"].get(),
                )
            self.result = ConnectionCreateRequest(
                name=self.vars["name"].get(),
                protocol=protocol,
                group=self.vars["group"].get(),
                tags=[tag.strip() for tag in self.vars["tags"].get().split(",") if tag.strip()],
                notes=notes,
                device_template=template,
                protocol_config=config,
            )
            self.window.destroy()
        except Exception as exc:
            messagebox.showerror(self.i18n.t("messages.validation_error"), str(exc), parent=self.window)

    def open(self) -> ConnectionCreateRequest | None:
        self.window.wait_window()
        return self.result
