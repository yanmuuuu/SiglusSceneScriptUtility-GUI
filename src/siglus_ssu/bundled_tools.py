"""便携版内置 ffmpeg / ffplay 解析与 PATH 注入。"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def bundled_bin_dir() -> Path | None:
    """返回包含 ffplay/ffmpeg 的目录；便携版为 exe 旁的 ffmpeg 文件夹。"""
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "ffmpeg")
    root = _project_root()
    candidates.extend(
        [
            root / "build" / "ffmpeg" / "bin",
            root / "packaging" / "ffmpeg" / "win64",
            root / "dist" / "SiglusSSU-GUI" / "ffmpeg",
        ]
    )
    for directory in candidates:
        if not directory.is_dir():
            continue
        if (directory / "ffplay.exe").is_file() or (directory / "ffplay").is_file():
            return directory
    return None


def find_ffplay() -> str | None:
    directory = bundled_bin_dir()
    if directory:
        for name in ("ffplay.exe", "ffplay"):
            path = directory / name
            if path.is_file():
                return str(path)
    return shutil.which("ffplay")


def find_ffmpeg() -> str | None:
    directory = bundled_bin_dir()
    if directory:
        for name in ("ffmpeg.exe", "ffmpeg"):
            path = directory / name
            if path.is_file():
                return str(path)
    return shutil.which("ffmpeg")


def augment_path_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """将内置 ffmpeg 目录置于 PATH 前端，供子进程加载 DLL。"""
    merged = dict(env if env is not None else os.environ)
    directory = bundled_bin_dir()
    if directory is None:
        return merged
    prefix = str(directory)
    current = merged.get("PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    if prefix not in parts:
        merged["PATH"] = prefix + (os.pathsep + current if current else "")
    return merged


def ffmpeg_status_line() -> str:
    ffplay = find_ffplay()
    if not ffplay:
        return "音频播放：未找到 ffplay（便携版应含 ffmpeg 文件夹）"
    directory = bundled_bin_dir()
    if directory and ffplay.startswith(str(directory)):
        return "音频播放：已使用内置 ffplay"
    return "音频播放：使用系统 PATH 中的 ffplay"


def ensure_ffmpeg_installed() -> bool:
    """若缺少 ffplay，尝试下载到便携目录（仅 Windows）。"""
    if find_ffplay():
        return True
    if sys.platform != "win32":
        return False
    if getattr(sys, "frozen", False):
        target = Path(sys.executable).resolve().parent / "ffmpeg"
    else:
        target = _project_root() / "build" / "ffmpeg" / "bin"
    try:
        from siglus_ssu.ffmpeg_fetch import install_ffmpeg_windows

        install_ffmpeg_windows(target)
    except Exception:
        return False
    return find_ffplay() is not None
