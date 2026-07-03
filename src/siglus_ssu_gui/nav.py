"""侧栏导航项（FModel 风格：左侧色条 + 选中高亮）。"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from .theme import ACCENT, BG_NAV


class NavItem(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        text: str,
        *,
        command: Callable[[], None],
    ) -> None:
        super().__init__(master, style="Nav.TFrame")
        self._accent = tk.Frame(self, width=3, bg=BG_NAV, highlightthickness=0)
        self._accent.pack(side=tk.LEFT, fill=tk.Y)
        inner = ttk.Frame(self, style="Nav.TFrame")
        inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn = ttk.Button(
            inner,
            text=text,
            style="Nav.TButton",
            command=command,
        )
        self._btn.pack(fill=tk.X, padx=(0, 4), pady=2)

    def set_selected(self, selected: bool) -> None:
        self._accent.configure(bg=ACCENT if selected else BG_NAV)
        self._btn.configure(style="NavSelected.TButton" if selected else "Nav.TButton")


class NavGroup(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(master, style="Nav.TFrame")
        ttk.Label(self, text=title, style="NavHeading.TLabel").pack(
            anchor=tk.W, padx=(8, 4), pady=(14, 6)
        )
        tk.Frame(self, height=1, bg="#2a2a30").pack(fill=tk.X, padx=8, pady=(0, 4))
        self.body = ttk.Frame(self, style="Nav.TFrame")
        self.body.pack(fill=tk.X)
