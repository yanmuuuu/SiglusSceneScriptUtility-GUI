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
from .panels.browser_panel import BrowserPanel
from .nav import NavGroup, NavItem
from .process_util import kill_process_tree, popen_group_kwargs
from .runner import CliRunner, _cli_subprocess_env
from .scroll import VerticalScrollArea
from .theme import BG, BG_NAV, BG_PANEL, BORDER, apply_theme, prepare_display
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
        self._nav_buttons: dict[str, NavItem] = {}
        self._current_key = ""

        self._build_ui()
        self._show_panel(PANEL_ORDER[0])
        self.after(200, self._check_const)
        if sys.platform == "win32":
            self.after(500, self._prefetch_ffmpeg)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Control-Return>", lambda _e: self._run())
        self.bind("<Control-l>", lambda _e: self._log.clear())

    def _build_ui(self) -> None:
        outer = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True)

        nav_outer = ttk.Frame(outer, padding=(12, 14), style="Nav.TFrame")
        outer.add(nav_outer, weight=0)
        ttk.Label(nav_outer, text="Siglus SSU", style="NavBrand.TLabel").pack(anchor=tk.W, padx=4)
        ttk.Label(nav_outer, text="图形工具", style="NavSub.TLabel").pack(anchor=tk.W, padx=4, pady=(2, 10))
        tk.Frame(nav_outer, height=1, bg=BORDER).pack(fill=tk.X, padx=4, pady=(0, 6))

        self._nav_scroll = VerticalScrollArea(
            nav_outer, bg=BG_NAV, body_style="Nav.TFrame", padding=(0, 4)
        )
        self._nav_scroll.pack(fill=tk.BOTH, expand=True)
        nav_body = self._nav_scroll.body

        for group, keys in _NAV_GROUPS:
            grp = NavGroup(nav_body, group)
            grp.pack(fill=tk.X)
            for key in keys:
                item = NavItem(
                    grp.body,
                    PANEL_LABELS[key],
                    command=lambda k=key: self._show_panel(k),
                )
                item.pack(fill=tk.X, padx=4, pady=1)
                self._nav_buttons[key] = item

        self._nav_scroll.refresh_bindings()
        self.after_idle(lambda: outer.sashpos(0, 220))

        right_pane = ttk.Panedwindow(outer, orient=tk.VERTICAL)
        outer.add(right_pane, weight=1)

        work = ttk.Frame(right_pane, padding=(18, 16))
        right_pane.add(work, weight=3)

        header = ttk.Frame(work)
        header.pack(fill=tk.X, pady=(0, 8))
        self._title = ttk.Label(header, text="", style="Title.TLabel")
        self._title.pack(anchor=tk.W)
        self._hint = ttk.Label(header, text="", style="Subtitle.TLabel", wraplength=780)
        self._hint.pack(anchor=tk.W, pady=(8, 6))
        tk.Frame(header, height=1, bg=BORDER).pack(fill=tk.X, pady=(10, 6))

        self._panel_scroll = VerticalScrollArea(
            work, bg=BG_PANEL, body_style="SectionBody.TFrame", padding=(6, 8)
        )
        self._panel_scroll.pack(fill=tk.BOTH, expand=True)
        self._panel_host = self._panel_scroll.body

        actions = ttk.Frame(work)
        actions.pack(fill=tk.X, pady=(12, 6))
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

        log_frame = ttk.Frame(right_pane, padding=(16, 4, 16, 10))
        right_pane.add(log_frame, weight=2)
        self._log = LogPanel(log_frame)
        self._log.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(self, padding=(14, 8), style="Footer.TFrame")
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self._legacy = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            footer, text="纯 Python 模式（--legacy）", variable=self._legacy, style="Footer.TCheckbutton"
        ).pack(side=tk.LEFT)
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
            if key == "browser":
                self._panels[key] = BrowserPanel(self._panel_host, app=self)
            else:
                self._panels[key] = self._panel_classes[key](self._panel_host)
            self._panel_scroll.refresh_bindings(self._panels[key])
        return self._panels[key]

    def jump_to_panel(self, key: str, *, input_path: str | None = None) -> None:
        if key not in self._panel_classes and key != "browser":
            self._status.configure(text=f"无法跳转：未知面板 {key}")
            return
        self._show_panel(key)
        if not input_path:
            return
        panel = self._ensure_panel(key)
        path = Path(input_path)
        self._prepare_panel_for_jump(panel, key, path)
        for attr in ("input_row", "exe_row", "scene_row", "engine_row", "_root_row", "in1"):
            row = getattr(panel, attr, None)
            if row is not None and hasattr(row, "set"):
                row.set(input_path)
                break
        label = PANEL_LABELS.get(key, key)
        self._status.configure(text=f"已跳转到「{label}」，路径已填入")

    def _prepare_panel_for_jump(self, panel: BasePanel, key: str, path: Path) -> None:
        op = getattr(panel, "op", None)
        if op is None or not hasattr(op, "set"):
            return
        ext = path.suffix.lower()
        if key == "g00" and ext in {".g00", ".g01"}:
            op.set("提取 --x")
            if hasattr(panel, "_on_op"):
                panel._on_op()
        elif key == "sound" and ext in {".ovk", ".owp", ".nwa", ".ogg", ".wav", ".mp3"}:
            op.set("提取 --x")
            if hasattr(panel, "_on_op"):
                panel._on_op()
        elif key == "video" and ext in {".omv", ".ogv"}:
            op.set("提取 --x")
            if hasattr(panel, "_on_op"):
                panel._on_op()
        elif key == "extract" and ext == ".pck":
            op.set("提取 --x")
            if hasattr(panel, "_on_op"):
                panel._on_op()

    def _show_panel(self, key: str) -> None:
        if self._current_key == "browser" and key != "browser":
            old = self._panels.get("browser")
            if old is not None and hasattr(old, "on_hide"):
                old.on_hide()
        prev_key = self._current_key
        self._current_key = key
        for k, item in self._nav_buttons.items():
            item.set_selected(k == key)
        try:
            panel = self._ensure_panel(key)
        except Exception as exc:
            self._current_key = prev_key
            for k, item in self._nav_buttons.items():
                item.set_selected(k == prev_key)
            messagebox.showerror(
                "面板加载失败",
                f"无法打开「{PANEL_LABELS.get(key, key)}」：\n\n{exc}",
            )
            return
        for k, p in self._panels.items():
            if k == key:
                p.pack(fill=tk.BOTH, expand=True)
            else:
                p.pack_forget()
        if key == "browser" and hasattr(panel, "on_show"):
            panel.on_show()
        self._panel_scroll.scroll_to_top()
        self._title.configure(text=PANEL_LABELS[key])
        self._hint.configure(text=PANEL_HINTS.get(key, ""))
        is_manual = key == "manual"
        is_browser = key == "browser"
        is_lsp = key == "lsp"
        if is_manual or is_browser:
            self._run_btn.configure(text="开始执行", state=tk.DISABLED)
            self._stop_btn.configure(state=tk.DISABLED)
            self._open_btn.configure(state=tk.DISABLED)
        else:
            self._run_btn.configure(text="启动 LSP" if is_lsp else "开始执行", state=tk.NORMAL)
            self._open_btn.configure(state=tk.NORMAL)
            self._stop_btn.configure(
                state=tk.NORMAL
                if is_lsp and self._lsp_proc and self._lsp_proc.poll() is None
                else tk.DISABLED
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
        if self._current_key in ("manual", "browser"):
            return
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
            env=_cli_subprocess_env(),
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
        browser = self._panels.get("browser")
        if browser is not None and hasattr(browser, "on_hide"):
            browser.on_hide()
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

    def _prefetch_ffmpeg(self) -> None:
        """便携版缺少 ffmpeg 时在后台预下载，避免首次试听长时间等待。"""
        if not getattr(sys, "frozen", False):
            return

        def work() -> None:
            from siglus_ssu.bundled_tools import ensure_ffmpeg_installed, find_ffplay

            if find_ffplay():
                return
            ensure_ffmpeg_installed()

        threading.Thread(target=work, daemon=True).start()

    def _check_const(self) -> None:
        if const_available():
            return
        if messagebox.askyesno(
            "缺少运行时常量",
            "未找到有效的 const.py。\n\n是否现在运行「初始化」下载常量文件？",
        ):
            self._show_panel("init")


def main() -> None:
    prepare_display()
    app = MainApp()
    app.mainloop()
