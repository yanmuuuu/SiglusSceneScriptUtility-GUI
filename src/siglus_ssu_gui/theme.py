"""ttk 主题与字体（FModel / Adonis Dark 风格，Windows 高 DPI 优化）。"""

from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any

_UI = "Segoe UI" if sys.platform == "win32" else "TkDefaultFont"
_MONO = "Cascadia Mono" if sys.platform == "win32" else "Courier"
_MONO_FALLBACK = "Consolas" if sys.platform == "win32" else "Courier"

# FModel / Adonis Dark 层次
BG = "#18181b"
BG_NAV = "#131316"
BG_PANEL = "#1f1f23"
BG_CARD = "#26262c"
BG_INPUT = "#2f2f36"
BG_ELEVATED = "#3a3a42"
BG_LOG = "#111113"
FG = "#f4f4f6"
FG_SECONDARY = "#d8d8de"
FG_MUTED = "#9aa3b2"
ACCENT = "#206bd4"
ACCENT_HOVER = "#2f7fe8"
ACCENT_SOFT = "#1a3158"
ACCENT_FG = "#ffffff"
BORDER = "#3a3a44"
BORDER_FOCUS = "#4f8fd4"
SELECT_BG = "#264f78"
# 资源列表：黑底白字（避免 Windows 下 Listbox 白底 + 浅色字看不清）
LIST_BG = "#141418"
LIST_FG = "#ffffff"
LIST_HEADER_BG = BG_ELEVATED
LIST_HEADER_FG = "#e8e8ec"
SASH = "#32323a"
SCROLL_THUMB = "#4a4a54"
SCROLL_TRACK = "#1a1a1e"

_BASE_SIZE = 11
_TITLE_SIZE = 20
_HINT_SIZE = 10


def prepare_display() -> None:
    """在创建 Tk 窗口前调用，避免 Windows 高 DPI 下文字发糊。"""
    if sys.platform != "win32":
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _mono_family() -> str:
    try:
        families = set(tkfont.families())
        if _MONO in families:
            return _MONO
    except tk.TclError:
        pass
    return _MONO_FALLBACK


def ui_font(size: int | None = None, *, bold: bool = False) -> tuple[str, int, str] | tuple[str, int]:
    sz = size or _BASE_SIZE
    if bold:
        return (_UI, sz, "bold")
    return (_UI, sz)


def mono_font(size: int = 11) -> tuple[str, int]:
    return (_mono_family(), size)


def make_entry(parent: tk.Misc, textvariable: tk.StringVar) -> tk.Entry:
    """原生 Entry 在 Windows 上通常比 ttk 更清晰。"""
    return tk.Entry(
        parent,
        textvariable=textvariable,
        font=ui_font(_BASE_SIZE),
        bg=BG_INPUT,
        fg=FG,
        insertbackground=FG,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=BORDER_FOCUS,
    )


def make_listbox(parent: tk.Misc, **kwargs: Any) -> tk.Listbox:
    """原生 Listbox，固定黑底白字，避免 Windows 主题导致白底浅字。"""
    opts: dict[str, Any] = {
        "bg": LIST_BG,
        "fg": LIST_FG,
        "selectbackground": SELECT_BG,
        "selectforeground": LIST_FG,
        "activestyle": "none",
        "highlightthickness": 0,
        "borderwidth": 0,
        "relief": tk.FLAT,
        "font": ui_font(10),
        "exportselection": False,
    }
    opts.update(kwargs)
    lb = tk.Listbox(parent, **opts)
    # 部分 Windows 主题会在创建后覆盖颜色，再设一次确保生效
    lb.configure(
        bg=LIST_BG,
        fg=LIST_FG,
        selectbackground=SELECT_BG,
        selectforeground=LIST_FG,
    )
    return lb


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=BG)
    root.option_add("*Font", ui_font(_BASE_SIZE))
    root.option_add("*Menu*Font", ui_font(_BASE_SIZE))
    root.option_add("*TCombobox*Listbox*Font", ui_font(_BASE_SIZE))
    root.option_add("*Listbox*background", LIST_BG)
    root.option_add("*Listbox*foreground", LIST_FG)
    root.option_add("*Listbox*selectBackground", SELECT_BG)
    root.option_add("*Listbox*selectForeground", LIST_FG)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        ".",
        background=BG,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
        bordercolor=BORDER,
    )
    style.configure("TFrame", background=BG)
    style.configure("Nav.TFrame", background=BG_NAV)
    style.configure("Footer.TFrame", background=BG_NAV)

    style.configure("TLabel", background=BG, foreground=FG)
    style.configure(
        "Title.TLabel",
        font=ui_font(_TITLE_SIZE, bold=True),
        foreground=FG,
        background=BG,
    )
    style.configure(
        "Subtitle.TLabel",
        font=ui_font(_BASE_SIZE),
        foreground=FG_SECONDARY,
        background=BG,
    )
    style.configure(
        "Hint.TLabel",
        font=ui_font(_HINT_SIZE),
        foreground=FG_MUTED,
        background=BG,
    )
    style.configure(
        "Field.TLabel",
        font=ui_font(_BASE_SIZE),
        foreground=FG_SECONDARY,
        background=BG_CARD,
    )
    style.configure(
        "NavBrand.TLabel",
        font=ui_font(17, bold=True),
        foreground=FG,
        background=BG_NAV,
    )
    style.configure(
        "NavSub.TLabel",
        font=ui_font(_HINT_SIZE),
        foreground=FG_MUTED,
        background=BG_NAV,
    )
    style.configure(
        "NavHeading.TLabel",
        font=ui_font(_HINT_SIZE, bold=True),
        foreground=FG_MUTED,
        background=BG_NAV,
    )

    style.configure(
        "Nav.TButton",
        padding=(14, 9),
        anchor=tk.W,
        font=ui_font(_BASE_SIZE),
        background=BG_NAV,
        foreground=FG_SECONDARY,
        borderwidth=0,
        focuscolor=BG_NAV,
    )
    style.map(
        "Nav.TButton",
        background=[("active", BG_ELEVATED), ("!active", BG_NAV)],
        foreground=[("active", FG), ("!active", FG_SECONDARY)],
    )
    style.configure(
        "NavSelected.TButton",
        padding=(14, 9),
        anchor=tk.W,
        font=ui_font(_BASE_SIZE, bold=True),
        background=ACCENT_SOFT,
        foreground=ACCENT_FG,
        borderwidth=0,
        focuscolor=ACCENT_SOFT,
    )
    style.map(
        "NavSelected.TButton",
        background=[("active", ACCENT_SOFT), ("!active", ACCENT_SOFT)],
        foreground=[("active", ACCENT_FG), ("!active", ACCENT_FG)],
    )

    style.configure(
        "TButton",
        font=ui_font(_BASE_SIZE),
        background=BG_ELEVATED,
        foreground=FG,
        padding=(14, 7),
        borderwidth=0,
        relief=tk.FLAT,
    )
    style.map(
        "TButton",
        background=[("active", BG_INPUT), ("disabled", BG_PANEL)],
        foreground=[("disabled", FG_MUTED)],
    )
    style.configure(
        "Secondary.TButton",
        font=ui_font(_HINT_SIZE),
        background=BG_CARD,
        foreground=FG_SECONDARY,
        padding=(12, 6),
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", BG_ELEVATED), ("!active", BG_CARD)],
        foreground=[("active", FG), ("!active", FG_SECONDARY)],
    )
    style.configure(
        "Action.TButton",
        font=ui_font(_BASE_SIZE, bold=True),
        padding=(18, 9),
        background=ACCENT,
        foreground=ACCENT_FG,
        borderwidth=0,
    )
    style.map(
        "Action.TButton",
        background=[("active", ACCENT_HOVER), ("disabled", BG_PANEL)],
        foreground=[("active", ACCENT_FG), ("disabled", FG_MUTED)],
    )

    style.configure(
        "TEntry",
        font=ui_font(_BASE_SIZE),
        fieldbackground=BG_INPUT,
        foreground=FG,
        insertcolor=FG,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=(8, 5),
    )
    style.configure(
        "TCombobox",
        font=ui_font(_BASE_SIZE),
        fieldbackground=BG_INPUT,
        foreground=FG,
        arrowcolor=FG_SECONDARY,
        bordercolor=BORDER,
        padding=(8, 5),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        foreground=[("readonly", FG)],
    )

    style.configure(
        "Section.TLabelframe",
        background=BG_CARD,
        bordercolor=BORDER,
        relief=tk.FLAT,
        borderwidth=1,
        padding=(16, 12),
    )
    style.configure(
        "Section.TLabelframe.Label",
        font=ui_font(_BASE_SIZE, bold=True),
        foreground=FG,
        background=BG_CARD,
    )
    style.configure("SectionBody.TFrame", background=BG_PANEL)

    style.configure(
        "TCheckbutton",
        background=BG,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
        focuscolor=BG,
    )
    style.configure(
        "TRadiobutton",
        background=BG,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
        focuscolor=BG,
    )
    style.configure(
        "Option.TCheckbutton",
        background=BG_CARD,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
        focuscolor=BG_CARD,
    )
    style.configure(
        "Option.TRadiobutton",
        background=BG_CARD,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
        focuscolor=BG_CARD,
    )

    style.configure(
        "LogTitle.TLabel",
        font=ui_font(12, bold=True),
        foreground=FG,
        background=BG,
    )
    style.configure(
        "Footer.TCheckbutton",
        background=BG_NAV,
        foreground=FG_SECONDARY,
        font=ui_font(_BASE_SIZE),
        focuscolor=BG_NAV,
    )
    style.configure(
        "Status.TLabel",
        font=ui_font(_HINT_SIZE),
        background=BG_NAV,
        foreground=FG_SECONDARY,
        relief=tk.FLAT,
    )
    style.configure("TPanedwindow", background=BG, sashwidth=6, sashrelief=tk.FLAT)
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=BG_INPUT,
        background=ACCENT,
        bordercolor=BORDER,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=6,
    )
    style.configure(
        "TScrollbar",
        background=SCROLL_THUMB,
        troughcolor=SCROLL_TRACK,
        bordercolor=SCROLL_TRACK,
        arrowcolor=FG_MUTED,
        width=12,
    )
    style.configure(
        "Thin.Vertical.TScrollbar",
        background=SCROLL_THUMB,
        troughcolor=SCROLL_TRACK,
        bordercolor=SCROLL_TRACK,
        arrowsize=10,
        width=8,
    )
    style.configure(
        "Thin.Horizontal.TScrollbar",
        background=SCROLL_THUMB,
        troughcolor=SCROLL_TRACK,
        bordercolor=SCROLL_TRACK,
        arrowsize=10,
        width=8,
    )
    style.configure(
        "Treeview",
        background=BG_CARD,
        foreground=FG,
        fieldbackground=BG_CARD,
        bordercolor=BORDER,
        lightcolor=BG_CARD,
        darkcolor=BG_CARD,
        rowheight=26,
        font=ui_font(_BASE_SIZE),
    )
    style.configure(
        "Treeview.Heading",
        background=BG_ELEVATED,
        foreground=FG_SECONDARY,
        bordercolor=BORDER,
        relief=tk.FLAT,
        font=ui_font(_BASE_SIZE, bold=True),
    )
    style.map(
        "Treeview",
        background=[("selected", SELECT_BG), ("!selected", BG_CARD)],
        foreground=[("selected", FG), ("!selected", FG)],
    )
    # 资源浏览列表：强制黑底白字（Windows 默认 Treeview 正文区常为白底）
    style.configure(
        "Browser.Treeview",
        background=LIST_BG,
        foreground=LIST_FG,
        fieldbackground=LIST_BG,
        bordercolor=BORDER,
        lightcolor=LIST_BG,
        darkcolor=LIST_BG,
        rowheight=26,
        font=ui_font(_BASE_SIZE),
    )
    style.configure(
        "Browser.Treeview.Heading",
        background=LIST_HEADER_BG,
        foreground=LIST_HEADER_FG,
        bordercolor=BORDER,
        relief=tk.FLAT,
        font=ui_font(_BASE_SIZE, bold=True),
    )
    style.map(
        "Browser.Treeview",
        background=[("selected", SELECT_BG), ("!selected", LIST_BG)],
        foreground=[("selected", LIST_FG), ("!selected", LIST_FG)],
        fieldbackground=[("selected", SELECT_BG), ("!selected", LIST_BG)],
    )
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure(
        "Panel.TLabel",
        background=BG_PANEL,
        foreground=FG_SECONDARY,
        font=ui_font(_BASE_SIZE),
    )
    style.configure(
        "PanelHint.TLabel",
        background=BG_PANEL,
        foreground=FG_SECONDARY,
        font=ui_font(_HINT_SIZE),
    )
    style.configure(
        "PanelCaption.TLabel",
        background=BG_CARD,
        foreground=FG,
        font=ui_font(_BASE_SIZE),
    )
    return style
