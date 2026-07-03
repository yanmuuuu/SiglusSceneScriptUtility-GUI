"""ttk 主题与字体（Windows 优先，其他平台回退系统默认）。"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

_UI = "Segoe UI" if sys.platform == "win32" else "TkDefaultFont"
_MONO = "Consolas" if sys.platform == "win32" else "Courier"


def apply_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    for name in ("vista", "xpnative", "clam"):
        if name in style.theme_names():
            style.theme_use(name)
            break

    style.configure(".", font=(_UI, 10))
    style.configure("Title.TLabel", font=(_UI, 15, "bold"))
    style.configure("Hint.TLabel", font=(_UI, 9), foreground="#4a5568")
    style.configure("NavHeading.TLabel", font=(_UI, 9, "bold"), foreground="#64748b")
    style.configure("Nav.TButton", padding=(8, 6), anchor=tk.W)
    style.configure("NavSelected.TButton", padding=(8, 6), anchor=tk.W)
    style.map(
        "NavSelected.TButton",
        background=[("active", "#dbeafe"), ("!active", "#eff6ff")],
    )
    style.configure("Section.TLabelframe", padding=(12, 8))
    style.configure("Section.TLabelframe.Label", font=(_UI, 10, "bold"))
    style.configure("Status.TLabel", font=(_UI, 9))
    style.configure("Action.TButton", padding=(12, 6))
    return style


def mono_font(size: int = 10) -> tuple[str, int]:
    return (_MONO, size)
