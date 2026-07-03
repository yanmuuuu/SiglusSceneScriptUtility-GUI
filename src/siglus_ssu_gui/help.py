from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .markdown_view import render_markdown_to_text
from .scroll import VerticalScrollArea, bind_text_scroll
from .theme import BG_PANEL, FG, ui_font

DOCS_GUI_DIR_NAME = Path("docs") / "gui"

PANEL_HELP_DOCS: dict[str, str] = {
    "extract": "提取.md",
    "compile": "编译.md",
    "analyze": "分析.md",
    "textmap": "文本映射.md",
    "tutorial": "场景教程.md",
    "g00": "图片g00.md",
    "browser": "资源浏览.md",
    "sound": "音频.md",
    "video": "视频.md",
    "db": "数据库.md",
    "koe": "语音收集.md",
    "patch": "引擎补丁.md",
    "exec": "执行标签.md",
    "init": "初始化.md",
    "test": "回编测试.md",
    "lsp": "语言服务器.md",
}

MANUAL_SECTIONS: list[tuple[str, str]] = [
    ("总览", "操作手册.md"),
    ("完整汉化工作流", "常用工作流.md"),
    ("全局选项", "全局选项.md"),
    ("故障排除", "故障排除.md"),
    ("提取", "提取.md"),
    ("编译", "编译.md"),
    ("分析", "分析.md"),
    ("文本映射", "文本映射.md"),
    ("场景教程", "场景教程.md"),
    ("图片 g00", "图片g00.md"),
    ("资源浏览", "资源浏览.md"),
    ("音频", "音频.md"),
    ("视频", "视频.md"),
    ("数据库", "数据库.md"),
    ("语音收集", "语音收集.md"),
    ("引擎补丁", "引擎补丁.md"),
    ("执行标签", "执行标签.md"),
    ("初始化", "初始化.md"),
    ("回编测试", "回编测试.md"),
    ("语言服务器", "语言服务器.md"),
]


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def docs_gui_dir() -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / DOCS_GUI_DIR_NAME  # type: ignore[attr-defined]
        if bundled.is_dir():
            return bundled
    local = project_root() / DOCS_GUI_DIR_NAME
    return local


def instructions_path() -> Path | None:
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.extend(
            [
                Path(sys._MEIPASS) / "instructions.md",  # type: ignore[attr-defined]
                project_root() / "instructions.md",
            ]
        )
    else:
        candidates.append(project_root() / "instructions.md")
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_doc_text(filename: str) -> str:
    path = docs_gui_dir() / filename
    if not path.is_file():
        return f"未找到教程文件：{path}\n\n请确认 docs/gui/ 目录完整。"
    return path.read_text(encoding="utf-8")


def open_external_file(path: Path) -> None:
    if not path.is_file():
        messagebox.showerror("打开文件", f"文件不存在：\n{path}")
        return
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError as exc:
        messagebox.showerror("打开文件", str(exc))


class HelpTextView(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        scroll = VerticalScrollArea(self, bg=BG_PANEL, padding=(4, 4))
        scroll.pack(fill=tk.BOTH, expand=True)
        self._text = tk.Text(
            scroll.body,
            wrap=tk.WORD,
            font=ui_font(11),
            bg=BG_PANEL,
            fg=FG,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            highlightthickness=0,
        )
        self._text.pack(fill=tk.BOTH, expand=True)
        bind_text_scroll(self._text)

    def set_content(self, text: str) -> None:
        render_markdown_to_text(self._text, text)


class HelpPopup(tk.Toplevel):
    def __init__(self, master: tk.Misc, *, title: str, filename: str) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("720x560")
        self.minsize(520, 360)
        self.transient(master)
        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text=title, style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="关闭", command=self.destroy).pack(side=tk.RIGHT)
        body = ttk.Frame(self, padding=(12, 0, 12, 12))
        body.pack(fill=tk.BOTH, expand=True)
        view = HelpTextView(body)
        view.pack(fill=tk.BOTH, expand=True)
        view.set_content(load_doc_text(filename))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(50, self.lift)


def show_help_popup(master: tk.Misc, filename: str, *, title: str = "使用教程") -> None:
    HelpPopup(master, title=title, filename=filename)


def show_panel_help(master: tk.Misc, panel_key: str) -> None:
    filename = PANEL_HELP_DOCS.get(panel_key)
    if not filename:
        messagebox.showinfo("教程", "此功能暂无教程。")
        return
    from .panels import PANEL_LABELS

    show_help_popup(master, filename, title=f"{PANEL_LABELS.get(panel_key, panel_key)} · 教程")


def open_instructions_external() -> None:
    path = instructions_path()
    if path is None:
        messagebox.showerror(
            "打开操作指南",
            "未找到 instructions.md。\n\n请从项目根目录查看，或访问仓库在线文档。",
        )
        return
    open_external_file(path)
