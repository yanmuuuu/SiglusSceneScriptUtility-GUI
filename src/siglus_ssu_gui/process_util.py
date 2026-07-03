from __future__ import annotations

import os
import signal
import subprocess
import sys


def kill_process_tree(pid: int | None) -> None:
    """终止进程及其子进程（siglus-ssu 并行任务会派生子进程）。"""
    if pid is None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def popen_group_kwargs() -> dict:
    """子进程使用独立进程组，便于 Unix 上一并终止。"""
    kw: dict = {}
    if sys.platform == "win32":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    return kw
