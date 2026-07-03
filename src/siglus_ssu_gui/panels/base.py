from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import tkinter as tk
from tkinter import ttk

from ..help import show_help_popup


class BasePanel(ttk.Frame, ABC):
    TITLE = ""
    HELP_DOC = ""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=10)
        self._output_hint: Path | None = None
        help_doc = getattr(self.__class__, "HELP_DOC", "")
        if help_doc:
            bar = ttk.Frame(self)
            bar.pack(fill=tk.X, pady=(0, 8))
            ttk.Button(
                bar,
                text="教程",
                style="Secondary.TButton",
                width=8,
                command=lambda: show_help_popup(
                    self.winfo_toplevel(),
                    help_doc,
                    title=f"{self.TITLE} · 教程",
                ),
            ).pack(side=tk.RIGHT)
        self._body = ttk.Frame(self, style="SectionBody.TFrame")
        self._body.pack(fill=tk.BOTH, expand=True)
        self._build(self._body)

    @abstractmethod
    def _build(self, parent: ttk.Frame) -> None:
        raise NotImplementedError

    def build_command(self) -> tuple[list[str], Path | None] | str:
        """返回 (CLI 参数列表, 输出目录提示) 或错误信息字符串。"""
        self._output_hint = None
        return self._build_command()

    @abstractmethod
    def _build_command(self) -> tuple[list[str], Path | None] | str:
        raise NotImplementedError

    def output_hint(self) -> Path | None:
        return self._output_hint

    @staticmethod
    def _hint_from_path(value: str, *, as_dir: bool = False) -> Path | None:
        if not value:
            return None
        p = Path(value)
        if as_dir:
            return p if p.is_dir() else p.parent
        if p.is_dir():
            return p
        return p.parent
