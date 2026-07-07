from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from siglus_ssu.bundled_tools import augment_path_env

from .process_util import kill_process_tree, popen_group_kwargs

_CLI_FLAG = "--ssu-cli"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _src_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _cli_subprocess_env() -> dict[str, str] | None:
    """源码启动时把 src 传给子进程；便携版注入内置 ffmpeg PATH。"""
    if is_frozen():
        return augment_path_env()
    env = augment_path_env()
    src = str(_src_root())
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src if not prev else f"{src}{os.pathsep}{prev}"
    return env


def popen_kwargs() -> dict:
    return popen_group_kwargs()


class CliRunner:
    """通过子进程调用 siglus-ssu，流式输出日志。"""

    def __init__(self, on_line: Callable[[str], None], on_done: Callable[[int], None]) -> None:
        self._on_line = on_line
        self._on_done = on_done
        self._proc: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._stopped = False

    @staticmethod
    def resolve_executable() -> list[str]:
        if is_frozen():
            return [sys.executable, _CLI_FLAG]
        exe = shutil.which("siglus-ssu")
        if exe:
            return [exe]
        return [sys.executable, "-m", "siglus_ssu"]

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    @property
    def pid(self) -> int | None:
        with self._lock:
            if self._proc is None:
                return None
            return self._proc.pid

    def run(self, argv: list[str], *, cwd: Path | None = None) -> None:
        if self.is_running:
            raise RuntimeError("已有任务在运行")
        self._stopped = False
        cmd = self.resolve_executable() + argv
        self._on_line(f"$ {' '.join(cmd)}\n")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
            env=_cli_subprocess_env(),
            **popen_group_kwargs(),
        )
        with self._lock:
            self._proc = proc

        def _reader() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                self._on_line(line)
            code = proc.wait()
            with self._lock:
                self._proc = None
                stopped = self._stopped
            if not stopped:
                self._on_done(code)

        threading.Thread(target=_reader, daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            if proc is None or proc.poll() is not None:
                return
            self._stopped = True
            pid = proc.pid
        kill_process_tree(pid)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            kill_process_tree(pid)
        with self._lock:
            if self._proc is proc:
                self._proc = None
