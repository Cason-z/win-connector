from __future__ import annotations

import tkinter as tk
from tkinter import font, ttk


PALETTE = {
    "bg": "#070b14",
    "panel": "#0f1726",
    "panel_alt": "#142033",
    "text": "#e9f7ff",
    "muted": "#8ba7c4",
    "cyan": "#4ef2ff",
    "blue": "#3d7cff",
    "violet": "#8f6bff",
    "border": "#204164",
    "danger": "#ff6b8a",
    "selection": "#16385e",
}


def apply_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=PALETTE["bg"])
    root.option_add("*TCombobox*Listbox*Background", PALETTE["panel"])
    root.option_add("*TCombobox*Listbox*Foreground", PALETTE["text"])
    root.option_add("*TCombobox*Listbox*selectBackground", PALETTE["selection"])
    root.option_add("*TCombobox*Listbox*selectForeground", PALETTE["text"])

    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10)
    text_font = font.nametofont("TkTextFont")
    text_font.configure(family="Segoe UI", size=10)
    heading_font = font.nametofont("TkHeadingFont")
    heading_font.configure(family="Segoe UI Semibold", size=10)

    style.configure(".", background=PALETTE["bg"], foreground=PALETTE["text"], fieldbackground=PALETTE["panel"])
    style.configure("Root.TFrame", background=PALETTE["bg"])
    style.configure("Panel.TFrame", background=PALETTE["panel"])
    style.configure("Card.TFrame", background=PALETTE["panel_alt"], relief="flat")
    style.configure("Header.TFrame", background=PALETTE["panel"])
    style.configure("TLabel", background=PALETTE["panel"], foreground=PALETTE["text"])
    style.configure("Muted.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Brand.TLabel", background=PALETTE["panel"], foreground=PALETTE["cyan"], font=("Consolas", 19, "bold"))
    style.configure("Section.TLabel", background=PALETTE["panel"], foreground=PALETTE["violet"], font=("Segoe UI Semibold", 10, "bold"))
    style.configure("Status.TLabel", background=PALETTE["panel"], foreground=PALETTE["muted"])
    style.configure("Empty.TLabel", background=PALETTE["panel_alt"], foreground=PALETTE["muted"])
    style.configure("TLabelframe", background=PALETTE["panel"], foreground=PALETTE["cyan"], bordercolor=PALETTE["border"], relief="solid")
    style.configure("TLabelframe.Label", background=PALETTE["panel"], foreground=PALETTE["cyan"])
    style.configure("TEntry", foreground=PALETTE["text"], fieldbackground=PALETTE["panel"], insertcolor=PALETTE["cyan"], bordercolor=PALETTE["border"])
    style.map("TEntry", fieldbackground=[("readonly", PALETTE["panel"])])
    style.configure("TCombobox", foreground=PALETTE["text"], fieldbackground=PALETTE["panel"], background=PALETTE["panel"], arrowcolor=PALETTE["cyan"], bordercolor=PALETTE["border"])
    style.configure("TButton", padding=(14, 8), background=PALETTE["panel_alt"], foreground=PALETTE["text"], bordercolor=PALETTE["border"])
    style.map("TButton", background=[("active", PALETTE["selection"])], foreground=[("disabled", PALETTE["muted"])])
    style.configure("Accent.TButton", background=PALETTE["blue"], foreground=PALETTE["text"], bordercolor=PALETTE["blue"])
    style.map("Accent.TButton", background=[("active", PALETTE["violet"])])
    style.configure("Danger.TButton", background=PALETTE["danger"], foreground=PALETTE["text"], bordercolor=PALETTE["danger"])
    style.map("Danger.TButton", background=[("active", "#ff8da7")])
    style.configure("Treeview", background=PALETTE["panel"], fieldbackground=PALETTE["panel"], foreground=PALETTE["text"], bordercolor=PALETTE["border"], rowheight=28)
    style.configure("Treeview.Heading", background=PALETTE["panel_alt"], foreground=PALETTE["cyan"], relief="flat", font=("Segoe UI Semibold", 10, "bold"))
    style.map("Treeview", background=[("selected", PALETTE["selection"])], foreground=[("selected", PALETTE["text"])])
    style.configure("Vertical.TScrollbar", background=PALETTE["panel"], troughcolor=PALETTE["bg"], bordercolor=PALETTE["border"], arrowcolor=PALETTE["cyan"])
    return style
