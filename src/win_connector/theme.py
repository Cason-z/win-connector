from __future__ import annotations

import tkinter as tk
from tkinter import font, ttk


PALETTE = {
    "bg": "#111827",
    "panel": "#182233",
    "panel_alt": "#223047",
    "field": "#0f1724",
    "text": "#f3f7fb",
    "muted": "#a9b7c8",
    "accent": "#2eaadc",
    "accent_hover": "#3dbde9",
    "green": "#38b97c",
    "border": "#33435d",
    "danger": "#d85858",
    "danger_hover": "#e66a6a",
    "selection": "#284764",
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
    style.configure("TLabel", background=PALETTE["panel"], foreground=PALETTE["text"])
    style.configure("Muted.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Brand.TLabel", background=PALETTE["panel"], foreground=PALETTE["text"], font=("Segoe UI Semibold", 20, "bold"))
    style.configure("Section.TLabel", background=PALETTE["panel"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 10, "bold"))
    style.configure("Status.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Empty.TLabel", background=PALETTE["panel_alt"], foreground=PALETTE["muted"])
    style.configure("TLabelframe", background=PALETTE["panel"], foreground=PALETTE["accent"], bordercolor=PALETTE["border"], relief="solid")
    style.configure("TLabelframe.Label", background=PALETTE["panel"], foreground=PALETTE["accent"], font=("Segoe UI Semibold", 10, "bold"))
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
    style.configure("Danger.TButton", background=PALETTE["danger"], foreground=PALETTE["text"], bordercolor=PALETTE["danger"])
    style.map("Danger.TButton", background=[("active", PALETTE["danger_hover"])])
    style.configure("Treeview", background=PALETTE["field"], fieldbackground=PALETTE["field"], foreground=PALETTE["text"], bordercolor=PALETTE["border"], rowheight=30)
    style.configure("Treeview.Heading", background=PALETTE["panel_alt"], foreground=PALETTE["text"], relief="flat", font=("Segoe UI Semibold", 10, "bold"))
    style.map("Treeview", background=[("selected", PALETTE["selection"])], foreground=[("selected", PALETTE["text"])])
    style.configure("Vertical.TScrollbar", background=PALETTE["panel"], troughcolor=PALETTE["bg"], bordercolor=PALETTE["border"], arrowcolor=PALETTE["accent"])
    return style
