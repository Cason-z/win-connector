from __future__ import annotations

import tkinter as tk
from tkinter import font, ttk


PALETTE = {
    "bg": "#080d16",
    "panel": "#111a28",
    "panel_alt": "#162338",
    "field": "#07111f",
    "text": "#eef7ff",
    "muted": "#8ea4bc",
    "accent": "#22d3ee",
    "accent_hover": "#67e8f9",
    "hot": "#f472b6",
    "green": "#38d39f",
    "border": "#27415f",
    "danger": "#fb7185",
    "danger_hover": "#fda4af",
    "selection": "#0f766e",
}


def apply_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=PALETTE["bg"])
    root.option_add("*TCombobox*Listbox*Background", PALETTE["field"])
    root.option_add("*TCombobox*Listbox*Foreground", PALETTE["text"])
    root.option_add("*TCombobox*Listbox*selectBackground", PALETTE["selection"])
    root.option_add("*TCombobox*Listbox*selectForeground", PALETTE["text"])

    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10)
    text_font = font.nametofont("TkTextFont")
    text_font.configure(family="Segoe UI", size=10)
    heading_font = font.nametofont("TkHeadingFont")
    heading_font.configure(family="Segoe UI Semibold", size=10)

    style.configure(".", background=PALETTE["bg"], foreground=PALETTE["text"], fieldbackground=PALETTE["field"])
    style.configure("Root.TFrame", background=PALETTE["bg"])
    style.configure("Panel.TFrame", background=PALETTE["panel"])
    style.configure("Card.TFrame", background=PALETTE["panel_alt"], relief="flat")
    style.configure("Header.TFrame", background=PALETTE["panel"])
    style.configure("Nav.TFrame", background=PALETTE["panel_alt"])
    style.configure("TLabel", background=PALETTE["panel"], foreground=PALETTE["text"])
    style.configure("Muted.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Brand.TLabel", background=PALETTE["panel"], foreground=PALETTE["text"], font=("Segoe UI Semibold", 22, "bold"))
    style.configure("Section.TLabel", background=PALETTE["panel"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 10, "bold"))
    style.configure("Status.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Empty.TLabel", background=PALETTE["panel_alt"], foreground=PALETTE["muted"])
    style.configure("TLabelframe", background=PALETTE["panel"], foreground=PALETTE["accent"], bordercolor=PALETTE["border"], relief="solid")
    style.configure("TLabelframe.Label", background=PALETTE["panel"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 10, "bold"))
    style.configure("Glow.TLabelframe", background=PALETTE["panel"], foreground=PALETTE["accent"], bordercolor=PALETTE["accent"], lightcolor=PALETTE["accent"], darkcolor=PALETTE["border"], relief="solid")
    style.configure("Glow.TLabelframe.Label", background=PALETTE["panel"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 10, "bold"))
    style.configure("TEntry", foreground=PALETTE["text"], fieldbackground=PALETTE["field"], insertcolor=PALETTE["accent"], bordercolor=PALETTE["border"], lightcolor=PALETTE["border"], darkcolor=PALETTE["border"], padding=(8, 6))
    style.map("TEntry", fieldbackground=[("readonly", PALETTE["field"])], bordercolor=[("focus", PALETTE["accent"])])
    style.configure("TCombobox", foreground=PALETTE["text"], fieldbackground=PALETTE["field"], background=PALETTE["field"], arrowcolor=PALETTE["accent"], bordercolor=PALETTE["border"], padding=(8, 6))
    style.map("TCombobox", bordercolor=[("focus", PALETTE["accent"])])
    style.configure("TCheckbutton", background=PALETTE["panel"], foreground=PALETTE["muted"], focuscolor=PALETTE["panel"])
    style.map("TCheckbutton", foreground=[("active", PALETTE["text"])], background=[("active", PALETTE["panel"])])
    style.configure("TButton", padding=(14, 8), background=PALETTE["panel_alt"], foreground=PALETTE["text"], bordercolor=PALETTE["border"])
    style.map("TButton", background=[("active", PALETTE["selection"])], foreground=[("disabled", PALETTE["muted"])])
    style.configure("Accent.TButton", background=PALETTE["accent"], foreground=PALETTE["text"], bordercolor=PALETTE["accent"])
    style.map("Accent.TButton", background=[("active", PALETTE["accent_hover"])])
    style.configure("Icon.TButton", padding=(10, 6), background=PALETTE["panel_alt"], foreground=PALETTE["accent"], bordercolor=PALETTE["border"], font=("Segoe UI Semibold", 11, "bold"))
    style.map("Icon.TButton", background=[("active", PALETTE["selection"])], foreground=[("active", PALETTE["accent_hover"])])
    style.configure("Danger.TButton", background=PALETTE["danger"], foreground=PALETTE["text"], bordercolor=PALETTE["danger"])
    style.map("Danger.TButton", background=[("active", PALETTE["danger_hover"])])
    style.configure("Treeview", background=PALETTE["field"], fieldbackground=PALETTE["field"], foreground=PALETTE["text"], bordercolor=PALETTE["border"], rowheight=30)
    style.configure("Treeview.Heading", background=PALETTE["panel_alt"], foreground=PALETTE["text"], relief="flat", font=("Segoe UI Semibold", 10, "bold"))
    style.map("Treeview", background=[("selected", PALETTE["selection"])], foreground=[("selected", PALETTE["text"])])
    style.configure("Vertical.TScrollbar", background=PALETTE["panel"], troughcolor=PALETTE["bg"], bordercolor=PALETTE["border"], arrowcolor=PALETTE["accent"])
    return style
