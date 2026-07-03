from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Literal

PathMode = Literal["file", "dir", "save", "either"]


class PathRow(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        label: str,
        *,
        mode: PathMode = "file",
        filetypes: list[tuple[str, str]] | None = None,
        width: int = 56,
    ) -> None:
        super().__init__(master)
        self.mode = mode
        self.filetypes = filetypes or [("所有文件", "*.*")]
        ttk.Label(self, text=label, width=14).pack(side=tk.LEFT, anchor=tk.W)
        self.var = tk.StringVar()
        ttk.Entry(self, textvariable=self.var, width=width).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4)
        )
        ttk.Button(self, text="浏览…", command=self._browse).pack(side=tk.LEFT)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)

    def _browse(self) -> None:
        if self.mode == "dir":
            path = filedialog.askdirectory()
        elif self.mode == "save":
            path = filedialog.asksaveasfilename(filetypes=self.filetypes)
        elif self.mode == "either":
            path = filedialog.askopenfilename(filetypes=self.filetypes)
            if not path:
                path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename(filetypes=self.filetypes)
        if path:
            self.var.set(path)

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
    def __init__(self, master: tk.Misc, label: str, *, width: int = 56) -> None:
        super().__init__(master)
        ttk.Label(self, text=label, width=14).pack(side=tk.LEFT, anchor=tk.W)
        self.var = tk.StringVar()
        ttk.Entry(self, textvariable=self.var, width=width).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0)
        )

    def get(self) -> str:
        return self.var.get().strip()


class AngouRow(PathRow):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, "密钥来源", mode="either", width=48)

    def append_argv(self, argv: list[str]) -> None:
        value = self.get()
        if value:
            argv.extend(["--angou", value])


class FileListRow(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str) -> None:
        super().__init__(master)
        ttk.Label(self, text=label).pack(anchor=tk.W)
        box = ttk.Frame(self)
        box.pack(fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(box, height=4, selectmode=tk.EXTENDED)
        scroll = ttk.Scrollbar(box, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btns, text="添加文件…", command=self._add).pack(side=tk.LEFT)
        ttk.Button(btns, text="移除选中", command=self._remove).pack(side=tk.LEFT, padx=6)

    def _add(self) -> None:
        paths = filedialog.askopenfilenames()
        for p in paths:
            self.listbox.insert(tk.END, p)

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
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        ttk.Label(header, text="运行日志").pack(side=tk.LEFT)
        ttk.Button(header, text="清空", command=self.clear).pack(side=tk.RIGHT)
        self.text = tk.Text(self, height=14, wrap=tk.WORD, font=("Consolas", 10))
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set, state=tk.DISABLED)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def append(self, chunk: str) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, chunk)
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)


def labeled_combo(
    parent: tk.Misc,
    label: str,
    values: list[str],
    *,
    width: int = 40,
) -> ttk.Combobox:
    row = ttk.Frame(parent)
    row.pack(fill=tk.X, pady=2)
    ttk.Label(row, text=label, width=14).pack(side=tk.LEFT, anchor=tk.W)
    combo = ttk.Combobox(row, values=values, state="readonly", width=width)
    combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
    if values:
        combo.current(0)
    return combo


def labeled_radio(
    parent: tk.Misc,
    label: str,
    options: list[tuple[str, str]],
    *,
    command: Callable[[], None] | None = None,
) -> tk.StringVar:
    box = ttk.LabelFrame(parent, text=label, padding=6)
    box.pack(fill=tk.X, pady=4)
    var = tk.StringVar(value=options[0][0])
    for value, text in options:
        ttk.Radiobutton(box, text=text, value=value, variable=var, command=command).pack(
            anchor=tk.W
        )
    return var


from typing import NamedTuple


class CheckOption(NamedTuple):
    var: tk.BooleanVar
    widget: ttk.Checkbutton

    def get(self) -> bool:
        return bool(self.var.get())

    def pack(self, **kwargs) -> None:
        self.widget.pack(**kwargs)

    def pack_forget(self) -> None:
        self.widget.pack_forget()


def labeled_check(parent: tk.Misc, text: str, *, default: bool = False) -> CheckOption:
    var = tk.BooleanVar(value=default)
    widget = ttk.Checkbutton(parent, text=text, variable=var)
    widget.pack(anchor=tk.W, pady=1)
    return CheckOption(var=var, widget=widget)
