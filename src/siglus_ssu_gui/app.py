from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import UPSTREAM_VERSION, __version__
from .const_check import const_available
from .panels import PANEL_HINTS, PANEL_LABELS, PANEL_NAV_GROUPS, PANEL_ORDER, PANELS, BasePanel, LspPanel
from .process_util import kill_process_tree, popen_group_kwargs
from .runner import CliRunner
from .theme import apply_theme
from .widgets import LogPanel

_NAV_GROUPS = PANEL_NAV_GROUPS


class MainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SiglusSceneScriptUtility")
        self.minsize(960, 680)
        self.geometry("1040x760")
        apply_theme(self)

        self._output_hint: Path | None = None
        self._lsp_proc: subprocess.Popen[str] | None = None
        self._lsp_reader: threading.Thread | None = None
        self._shutting_down = False

        self._runner = CliRunner(self._on_log_line, self._on_task_done)
        self._panel_classes = dict(PANELS)
        self._panels: dict[str, BasePanel] = {}
        self._nav_buttons: dict[str, ttk.Button] = {}
        self._current_key = ""

        self._build_ui()
        self._show_panel(PANEL_ORDER[0])
        self.after(200, self._check_const)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Control-Return>", lambda _e: self._run())
        self.bind("<Control-l>", lambda _e: self._log.clear())

    def _build_ui(self) -> None:
        outer = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True)

        nav_outer = ttk.Frame(outer, padding=(8, 10))
        outer.add(nav_outer, weight=0)
        ttk.Label(nav_outer, text="Siglus SSU", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(nav_outer, text="图形工具", style="Hint.TLabel").pack(anchor=tk.W, pady=(0, 10))

        nav_canvas = tk.Canvas(nav_outer, width=168, highlightthickness=0, borderwidth=0)
        nav_scroll = ttk.Scrollbar(nav_outer, orient=tk.VERTICAL, command=nav_canvas.yview)
        self._nav_frame = ttk.Frame(nav_canvas)
        self._nav_frame.bind(
            "<Configure>",
            lambda _e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")),
        )
        nav_canvas.create_window((0, 0), window=self._nav_frame, anchor=tk.NW)
        nav_canvas.configure(yscrollcommand=nav_scroll.set)
        nav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nav_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for group, keys in _NAV_GROUPS:
            ttk.Label(self._nav_frame, text=group, style="NavHeading.TLabel").pack(
                anchor=tk.W, pady=(10, 4), padx=4
            )
            for key in keys:
                btn = ttk.Button(
                    self._nav_frame,
                    text=PANEL_LABELS[key],
                    style="Nav.TButton",
                    command=lambda k=key: self._show_panel(k),
                )
                btn.pack(fill=tk.X, padx=2, pady=1)
                self._nav_buttons[key] = btn

        right_pane = ttk.Panedwindow(outer, orient=tk.VERTICAL)
        outer.add(right_pane, weight=1)

        work = ttk.Frame(right_pane, padding=(12, 10))
        right_pane.add(work, weight=3)

        header = ttk.Frame(work)
        header.pack(fill=tk.X)
        self._title = ttk.Label(header, text="", style="Title.TLabel")
        self._title.pack(anchor=tk.W)
        self._hint = ttk.Label(header, text="", style="Hint.TLabel", wraplength=720)
        self._hint.pack(anchor=tk.W, pady=(4, 8))

        panel_scroll = tk.Canvas(work, highlightthickness=0, borderwidth=0)
        panel_scroll.pack(fill=tk.BOTH, expand=True)
        self._panel_host = ttk.Frame(panel_scroll, padding=(0, 4))
        self._panel_window = panel_scroll.create_window((0, 0), window=self._panel_host, anchor=tk.NW)

        def _on_panel_configure(_event: tk.Event) -> None:
            panel_scroll.configure(scrollregion=panel_scroll.bbox("all"))
            panel_scroll.itemconfigure(self._panel_window, width=panel_scroll.winfo_width())

        self._panel_host.bind("<Configure>", _on_panel_configure)
        panel_scroll.bind("<Configure>", _on_panel_configure)

        actions = ttk.Frame(work)
        actions.pack(fill=tk.X, pady=(10, 4))
        self._run_btn = ttk.Button(
            actions, text="开始执行", style="Action.TButton", command=self._run
        )
        self._run_btn.pack(side=tk.LEFT)
        self._stop_btn = ttk.Button(actions, text="停止", command=self._stop, state=tk.DISABLED)
        self._stop_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._open_btn = ttk.Button(actions, text="打开输出目录", command=self._open_output)
        self._open_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._progress = ttk.Progressbar(actions, mode="indeterminate", length=140)
        self._progress.pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Label(actions, text="Ctrl+Enter 执行", style="Hint.TLabel").pack(side=tk.RIGHT)

        log_frame = ttk.Frame(right_pane, padding=(12, 0, 12, 8))
        right_pane.add(log_frame, weight=2)
        self._log = LogPanel(log_frame)
        self._log.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(self, padding=(12, 6))
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self._legacy = tk.BooleanVar(value=False)
        ttk.Checkbutton(footer, text="纯 Python 模式（--legacy）", variable=self._legacy).pack(
            side=tk.LEFT
        )
        ttk.Label(footer, text="常量配置").pack(side=tk.LEFT, padx=(20, 4))
        self._profile = ttk.Combobox(footer, values=["0", "1", "2"], width=3, state="readonly")
        self._profile.current(0)
        self._profile.pack(side=tk.LEFT)
        ttk.Label(
            footer,
            text=f"GUI v{__version__}  ·  CLI v{UPSTREAM_VERSION}",
            style="Hint.TLabel",
        ).pack(side=tk.RIGHT)

        self._status = ttk.Label(
            self, text="就绪", relief=tk.SUNKEN, anchor=tk.W, padding=(10, 4), style="Status.TLabel"
        )
        self._status.pack(fill=tk.X, side=tk.BOTTOM)

    def _ensure_panel(self, key: str) -> BasePanel:
        if key not in self._panels:
            self._panels[key] = self._panel_classes[key](self._panel_host)
        return self._panels[key]

    def _show_panel(self, key: str) -> None:
        self._current_key = key
        for k, btn in self._nav_buttons.items():
            btn.configure(style="NavSelected.TButton" if k == key else "Nav.TButton")
        panel = self._ensure_panel(key)
        for k, p in self._panels.items():
            if k == key:
                p.pack(fill=tk.BOTH, expand=True)
            else:
                p.pack_forget()
        self._title.configure(text=PANEL_LABELS[key])
        self._hint.configure(text=PANEL_HINTS.get(key, ""))
        is_lsp = key == "lsp"
        self._run_btn.configure(text="启动 LSP" if is_lsp else "开始执行")
        self._stop_btn.configure(
            state=tk.NORMAL if is_lsp and self._lsp_proc and self._lsp_proc.poll() is None else tk.DISABLED
        )

    def _global_argv(self) -> list[str]:
        argv: list[str] = []
        if self._legacy.get():
            argv.append("--legacy")
        profile = self._profile.get()
        if profile and profile != "0":
            argv.extend(["--const-profile", profile])
        return argv

    def _run(self) -> None:
        if self._current_key == "lsp":
            self._start_lsp()
            return
        if self._runner.is_running:
            return
        panel = self._ensure_panel(self._current_key)
        result = panel.build_command()
        if isinstance(result, str):
            messagebox.showerror("无法执行", result)
            return
        argv, hint = result
        self._output_hint = hint
        full = self._global_argv() + argv
        self._set_running(True)
        self._status.configure(text="运行中…")
        try:
            self._runner.run(full)
        except RuntimeError as exc:
            self._set_running(False)
            messagebox.showerror("错误", str(exc))

    def _start_lsp(self) -> None:
        if self._lsp_proc and self._lsp_proc.poll() is None:
            messagebox.showinfo("LSP", "语言服务器已在运行")
            return
        panel = self._ensure_panel("lsp")
        assert isinstance(panel, LspPanel)
        result = panel.build_command()
        if isinstance(result, str):
            messagebox.showerror("无法执行", result)
            return
        argv, _ = result
        cmd = CliRunner.resolve_executable() + self._global_argv() + argv
        self._log.append(f"$ {' '.join(cmd)}\n")
        self._lsp_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            **popen_group_kwargs(),
        )
        self._status.configure(text=f"LSP 运行中 (PID {self._lsp_proc.pid})")
        self._stop_btn.configure(state=tk.NORMAL)
        self._log.append("语言服务器已启动。请在编辑器中配置 stdio LSP。\n")

        proc = self._lsp_proc

        def _drain() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                self._on_log_line(line)

        self._lsp_reader = threading.Thread(target=_drain, daemon=True)
        self._lsp_reader.start()

    def _stop_lsp(self) -> None:
        if self._lsp_proc is None or self._lsp_proc.poll() is not None:
            return
        pid = self._lsp_proc.pid
        kill_process_tree(pid)
        try:
            self._lsp_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            kill_process_tree(pid)
        self._lsp_proc = None

    def _stop(self) -> None:
        if self._lsp_proc and self._lsp_proc.poll() is None:
            self._stop_lsp()
            self._log.append("语言服务器已停止。\n")
            self._status.configure(text="就绪")
            self._stop_btn.configure(state=tk.DISABLED)
            return
        if not self._runner.is_running:
            return
        self._runner.stop()
        self._set_running(False)
        self._status.configure(text="已停止")
        self._log.append("\n[任务已停止]\n")

    def _on_log_line(self, line: str) -> None:
        self._log.append(line)

    def _on_task_done(self, code: int) -> None:
        def _finish() -> None:
            if self._shutting_down:
                return
            self._set_running(False)
            self._log.mark_scroll()
            if code == 0:
                self._status.configure(text="完成")
                if self._current_key == "tutorial":
                    messagebox.showinfo(
                        "场景教程",
                        "已生成剧情图 JSON。请打开输出目录中的 tutorial_viewer.html 查看。",
                    )
            else:
                self._status.configure(text=f"失败（退出码 {code}）")

        self.after(0, _finish)

    def _set_running(self, running: bool) -> None:
        self._run_btn.configure(state=tk.DISABLED if running else tk.NORMAL)
        self._stop_btn.configure(state=tk.NORMAL if running else tk.DISABLED)
        if running:
            self._progress.start(12)
        else:
            self._progress.stop()

    def _open_output(self) -> None:
        path = self._output_hint
        if path is None:
            messagebox.showinfo("打开输出目录", "尚无输出路径。请先成功执行一次任务。")
            return
        target = path if path.is_dir() else path.parent
        if not target.exists():
            messagebox.showerror("打开输出目录", f"目录不存在：{target}")
            return
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
        else:
            subprocess.run(["xdg-open", str(target)], check=False)

    def _cleanup_processes(self) -> None:
        self._shutting_down = True
        self._runner.stop()
        self._stop_lsp()

    def _on_close(self) -> None:
        running = self._runner.is_running or (
            self._lsp_proc is not None and self._lsp_proc.poll() is None
        )
        if running and not messagebox.askyesno(
            "确认退出",
            "任务仍在运行。\n\n关闭窗口将终止当前解析/编译任务。是否退出？",
        ):
            return
        self._cleanup_processes()
        self.destroy()

    def _check_const(self) -> None:
        if const_available():
            return
        if messagebox.askyesno(
            "缺少运行时常量",
            "未找到有效的 const.py。\n\n是否现在运行「初始化」下载常量文件？",
        ):
            self._show_panel("init")


def main() -> None:
    app = MainApp()
    app.mainloop()
