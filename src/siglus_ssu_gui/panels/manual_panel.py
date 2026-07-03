from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..help import (
    MANUAL_SECTIONS,
    HelpTextView,
    load_doc_text,
    open_instructions_external,
)
from .base import BasePanel


class ManualPanel(BasePanel):
    """内嵌操作手册：章节列表 + 正文。"""

    TITLE = "操作手册"
    HELP_DOC = ""

    def _build(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="选择左侧章节阅读 Markdown 教程（标题、表格、代码块已格式化显示）。汉化请优先阅读「完整汉化工作流」。",
            wraplength=640,
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(0, 8))

        actions = ttk.Frame(parent)
        actions.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(
            actions,
            text="打开 instructions.md（完整操作指南）",
            style="Secondary.TButton",
            command=open_instructions_external,
        ).pack(side=tk.LEFT)

        split = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True)

        nav_frame = ttk.Frame(split, padding=(0, 4))
        split.add(nav_frame, weight=0)
        ttk.Label(nav_frame, text="章节", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 4))
        self._list = tk.Listbox(
            nav_frame,
            width=22,
            height=18,
            exportselection=False,
            highlightthickness=0,
            activestyle=tk.NONE,
        )
        scroll = ttk.Scrollbar(nav_frame, orient=tk.VERTICAL, command=self._list.yview)
        self._list.configure(yscrollcommand=scroll.set)
        self._list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        for label, _file in MANUAL_SECTIONS:
            self._list.insert(tk.END, label)

        content_frame = ttk.Frame(split, padding=(8, 0, 0, 0))
        split.add(content_frame, weight=1)
        self._view = HelpTextView(content_frame)
        self._view.pack(fill=tk.BOTH, expand=True)

        self._list.bind("<<ListboxSelect>>", self._on_select)
        self._list.selection_set(0)
        self._list.event_generate("<<ListboxSelect>>")
        self.after_idle(lambda: split.sashpos(0, 200))

    def _on_select(self, _event: tk.Event | None = None) -> None:
        sel = self._list.curselection()
        if not sel:
            return
        _label, filename = MANUAL_SECTIONS[sel[0]]
        self._view.set_content(load_doc_text(filename))

    def _build_command(self) -> tuple[list[str], None] | str:
        return "操作手册为只读页面，无需执行命令。"
