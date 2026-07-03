from __future__ import annotations

import queue
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Literal, NamedTuple

from .scroll import bind_listbox_scroll, bind_text_scroll
from .theme import (
    ACCENT,
    BG,
    BG_INPUT,
    BG_LOG,
    BG_PANEL,
    BORDER,
    FG,
    FG_MUTED,
    FG_SECONDARY,
    SELECT_BG,
    make_entry,
    mono_font,
    ui_font,
)

PathMode = Literal["file", "dir", "save", "file_or_dir", "save_or_dir"]

G00_FILETYPES = [
    ("G00 图片", "*.g00"),
    ("所有文件", "*.*"),
]
IMAGE_FILETYPES = [
    ("图片", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
    ("JSON 布局", "*.json;*.jsonc"),
    ("所有文件", "*.*"),
]
AUDIO_FILETYPES = [
    ("音频", "*.ovk;*.owp;*.nwa;*.ogg"),
    ("所有文件", "*.*"),
]
VIDEO_FILETYPES = [
    ("视频", "*.omv;*.ogv"),
    ("所有文件", "*.*"),
]
DBS_FILETYPES = [
    ("数据库", "*.dbs"),
    ("所有文件", "*.*"),
]
PCK_FILETYPES = [
    ("PCK 文件", "*.pck"),
    ("所有文件", "*.*"),
]
DAT_FILETYPES = [
    ("DAT 文件", "*.dat"),
    ("所有文件", "*.*"),
]

_last_browse_dir: str | None = None
_LOG_MAX_CHARS = 400_000


def _remember_path(path: str) -> None:
    global _last_browse_dir
    p = Path(path)
    target = p if p.is_dir() else p.parent
    if target.is_dir():
        _last_browse_dir = str(target)


def _initial_dir() -> str | None:
    return _last_browse_dir


class Section(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(master, text=title, style="Section.TLabelframe", padding=(16, 12))
        self.body = ttk.Frame(self, style="SectionBody.TFrame")
        self.body.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)


class CollapsibleSection(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, *, start_open: bool = False) -> None:
        super().__init__(master)
        self._open = start_open
        self._title = title
        self._toggle = ttk.Button(self, text=self._label(), command=self._flip, width=24)
        self._toggle.pack(anchor=tk.W, pady=(4, 2))
        self.body = ttk.LabelFrame(self, text=title, style="Section.TLabelframe", padding=(12, 8))
        if start_open:
            self.body.pack(fill=tk.X, pady=2)

    def _label(self) -> str:
        return f"{'▼' if self._open else '▶'} {self._title}"

    def _flip(self) -> None:
        self._open = not self._open
        self._toggle.configure(text=self._label())
        if self._open:
            self.body.pack(fill=tk.X, pady=2)
        else:
            self.body.pack_forget()


class PathRow(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        label: str,
        *,
        mode: PathMode = "file",
        filetypes: list[tuple[str, str]] | None = None,
        hint: str = "",
    ) -> None:
        super().__init__(master)
        self.mode = mode
        self.filetypes = filetypes or [("所有文件", "*.*")]
        head = ttk.Frame(self)
        head.pack(fill=tk.X)
        self._label = ttk.Label(head, text=label, width=12, style="Field.TLabel")
        self._label.pack(side=tk.LEFT, anchor=tk.W)
        self.var = tk.StringVar()
        make_entry(head, self.var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8), ipady=4
        )
        browse_box = ttk.Frame(head)
        browse_box.pack(side=tk.LEFT)
        self._file_btn = ttk.Button(
            browse_box, text="文件", style="Secondary.TButton", command=self._browse_file, width=6
        )
        self._dir_btn = ttk.Button(
            browse_box, text="文件夹", style="Secondary.TButton", command=self._browse_dir, width=7
        )
        self._save_btn = ttk.Button(
            browse_box, text="另存为", style="Secondary.TButton", command=self._browse_save, width=7
        )
        self._hint_label: ttk.Label | None = None
        if hint:
            self._hint_label = ttk.Label(self, text=hint, style="Hint.TLabel", wraplength=600)
            self._hint_label.pack(anchor=tk.W, padx=(14, 0), pady=(4, 0))
        self.set_mode(mode)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)

    def set_mode(
        self,
        mode: PathMode,
        *,
        filetypes: list[tuple[str, str]] | None = None,
    ) -> None:
        self.mode = mode
        if filetypes is not None:
            self.filetypes = filetypes
        for btn in (self._file_btn, self._dir_btn, self._save_btn):
            btn.pack_forget()
        if mode == "file":
            self._file_btn.pack(side=tk.LEFT)
        elif mode == "dir":
            self._dir_btn.pack(side=tk.LEFT)
        elif mode == "save":
            self._save_btn.pack(side=tk.LEFT)
        elif mode == "file_or_dir":
            self._file_btn.pack(side=tk.LEFT)
            self._dir_btn.pack(side=tk.LEFT, padx=(4, 0))
        elif mode == "save_or_dir":
            self._save_btn.pack(side=tk.LEFT)
            self._dir_btn.pack(side=tk.LEFT, padx=(4, 0))

    def set_hint(self, hint: str) -> None:
        if self._hint_label is not None:
            self._hint_label.configure(text=hint)

    def set_label(self, label: str) -> None:
        self._label.configure(text=label)

    def _browse_file(self) -> None:
        initial = _initial_dir()
        kw = {"initialdir": initial} if initial else {}
        path = filedialog.askopenfilename(filetypes=self.filetypes, **kw)
        if path:
            self.var.set(path)
            _remember_path(path)

    def _browse_dir(self) -> None:
        initial = _initial_dir()
        kw = {"initialdir": initial} if initial else {}
        path = filedialog.askdirectory(**kw)
        if path:
            self.var.set(path)
            _remember_path(path)

    def _browse_save(self) -> None:
        initial = _initial_dir()
        kw = {"initialdir": initial} if initial else {}
        path = filedialog.asksaveasfilename(filetypes=self.filetypes, **kw)
        if path:
            self.var.set(path)
            _remember_path(path)

    def validate_exists(self, *, required: bool = True, as_dir: bool | None = None) -> str | None:
        value = self.get()
        if not value:
            if required:
                return "请填写路径"
            return None
        p = Path(value)
        if as_dir is True and not p.is_dir():
            return f"找不到文件夹：{value}"
        if as_dir is False and not p.is_file():
            return f"找不到文件：{value}"
        if as_dir is None and not p.exists():
            return f"路径不存在：{value}"
        return None


class TextRow(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, *, hint: str = "") -> None:
        super().__init__(master)
        head = ttk.Frame(self)
        head.pack(fill=tk.X)
        ttk.Label(head, text=label, width=12, style="Field.TLabel").pack(side=tk.LEFT, anchor=tk.W)
        self.var = tk.StringVar()
        make_entry(head, self.var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), ipady=4
        )
        if hint:
            ttk.Label(self, text=hint, style="Hint.TLabel", wraplength=600).pack(
                anchor=tk.W, padx=(14, 0), pady=(4, 0)
            )

    def get(self) -> str:
        return self.var.get().strip()


class AngouRow(PathRow):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(
            master,
            "密钥来源",
            mode="file_or_dir",
            hint="可选。游戏根目录、angou=明文、key=十六进制；提取失败时再填。",
        )

    def append_argv(self, argv: list[str]) -> None:
        value = self.get()
        if value:
            argv.extend(["--angou", value])


class FileListRow(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        label: str,
        *,
        filetypes: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(master)
        self.filetypes = filetypes or [("所有文件", "*.*")]
        ttk.Label(self, text=label, style="Field.TLabel").pack(anchor=tk.W, pady=(0, 4))
        box = ttk.Frame(self)
        box.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(
            box,
            height=4,
            selectmode=tk.EXTENDED,
            font=mono_font(11),
            bg=BG_INPUT,
            fg=FG,
            selectbackground=SELECT_BG,
            selectforeground=FG,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        scroll = ttk.Scrollbar(box, orient=tk.VERTICAL, style="Thin.Vertical.TScrollbar", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        bind_listbox_scroll(self.listbox)
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btns, text="添加文件", style="Secondary.TButton", command=self._add).pack(
            side=tk.LEFT
        )
        ttk.Button(btns, text="移除选中", style="Secondary.TButton", command=self._remove).pack(
            side=tk.LEFT, padx=6
        )

    def _add(self) -> None:
        initial = _initial_dir()
        kw = {"initialdir": initial, "filetypes": self.filetypes} if initial else {"filetypes": self.filetypes}
        paths = filedialog.askopenfilenames(**kw)
        for p in paths:
            self.listbox.insert(tk.END, p)
            _remember_path(p)

    def _remove(self) -> None:
        for idx in reversed(self.listbox.curselection()):
            self.listbox.delete(idx)

    def paths(self) -> list[str]:
        return [self.listbox.get(i) for i in range(self.listbox.size())]

    def validate(self, *, required: bool = True) -> str | None:
        if required and self.listbox.size() == 0:
            return "请至少添加一个文件"
        return None


class LogPanel(ttk.Frame):
    """批量刷新日志，避免每行触发一次 UI 更新。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._pending_scroll = False

        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(header, text="运行日志", style="LogTitle.TLabel").pack(side=tk.LEFT)
        ttk.Button(header, text="清空", style="Secondary.TButton", command=self.clear, width=8).pack(
            side=tk.RIGHT
        )
        ttk.Label(header, text="右键可复制", style="Hint.TLabel").pack(side=tk.RIGHT, padx=10)

        box = ttk.Frame(self)
        box.pack(fill=tk.BOTH, expand=True)
        self.text = tk.Text(
            box,
            height=12,
            wrap=tk.NONE,
            font=mono_font(11),
            bg=BG_LOG,
            fg=FG_SECONDARY,
            insertbackground=FG,
            relief=tk.FLAT,
            padx=10,
            pady=8,
            spacing1=1,
            spacing3=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        scroll_y = ttk.Scrollbar(box, orient=tk.VERTICAL, style="Thin.Vertical.TScrollbar", command=self.text.yview)
        scroll_x = ttk.Scrollbar(box, orient=tk.HORIZONTAL, style="Thin.Horizontal.TScrollbar", command=self.text.xview)
        self.text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)

        bind_text_scroll(self.text)

        self.text.bind("<Key>", lambda _e: "break")
        menu = tk.Menu(self.text, tearoff=0)
        menu.add_command(label="复制", command=self._copy_selection)
        menu.add_command(label="全选", command=self._select_all)
        self.text.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

        self._poll()

    def _poll(self) -> None:
        chunks: list[str] = []
        try:
            while True:
                item = self._queue.get_nowait()
                if item is None:
                    self._pending_scroll = True
                else:
                    chunks.append(item)
        except queue.Empty:
            pass
        if chunks:
            self.text.insert(tk.END, "".join(chunks))
            self._trim()
            self._pending_scroll = True
        if self._pending_scroll:
            self.text.see(tk.END)
            self._pending_scroll = False
        self.after(80, self._poll)

    def _trim(self) -> None:
        if int(self.text.index("end-1c").split(".")[0]) > 8000:
            self.text.delete("1.0", "4000.0")
        content = self.text.get("1.0", tk.END)
        if len(content) > _LOG_MAX_CHARS:
            self.text.delete("1.0", f"1.0+{len(content) - _LOG_MAX_CHARS}c")

    def append(self, chunk: str) -> None:
        self._queue.put(chunk)

    def mark_scroll(self) -> None:
        self._queue.put(None)

    def clear(self) -> None:
        self.text.delete("1.0", tk.END)

    def _copy_selection(self) -> None:
        try:
            text = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)

    def _select_all(self) -> None:
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)


def labeled_combo(
    parent: tk.Misc,
    label: str,
    values: list[str],
    *,
    command: Callable[[], None] | None = None,
) -> ttk.Combobox:
    row = ttk.Frame(parent)
    row.pack(fill=tk.X, pady=4)
    ttk.Label(row, text=label, width=12, style="Field.TLabel").pack(side=tk.LEFT, anchor=tk.W)
    combo = ttk.Combobox(row, values=values, state="readonly", font=ui_font())
    combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
    if values:
        combo.current(0)
    if command:
        combo.bind("<<ComboboxSelected>>", lambda _e: command())
    return combo


def labeled_radio(
    parent: tk.Misc,
    label: str,
    options: list[tuple[str, str]],
    *,
    command: Callable[[], None] | None = None,
) -> tk.StringVar:
    box = ttk.LabelFrame(parent, text=label, style="Section.TLabelframe", padding=(14, 10))
    box.pack(fill=tk.X, pady=8)
    var = tk.StringVar(value=options[0][0])
    for value, text in options:
        ttk.Radiobutton(
            box,
            text=text,
            value=value,
            variable=var,
            command=command,
            style="Option.TRadiobutton",
        ).pack(anchor=tk.W, pady=2, padx=2)
    return var


class CheckOption(NamedTuple):
    var: tk.BooleanVar
    widget: ttk.Checkbutton

    def get(self) -> bool:
        return bool(self.var.get())

    def pack(self, **kwargs) -> None:
        self.widget.pack(**kwargs)

    def pack_forget(self) -> None:
        self.widget.pack_forget()


def labeled_check(
    parent: tk.Misc, text: str, *, default: bool = False, in_section: bool = True
) -> CheckOption:
    var = tk.BooleanVar(value=default)
    style = "Option.TCheckbutton" if in_section else "TCheckbutton"
    widget = ttk.Checkbutton(parent, text=text, variable=var, style=style)
    widget.pack(anchor=tk.W, pady=3, padx=2)
    return CheckOption(var=var, widget=widget)
