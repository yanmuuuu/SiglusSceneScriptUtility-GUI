#!/usr/bin/env python3
"""配置 SiglusSSU-GUI 运行环境（uv + Python 3.12 + 锁定依赖）。

用法:
    python scripts/setup_env.py          # 运行所需依赖（Pillow 等）
    python scripts/setup_env.py --dev    # 含打包/ lint 开发依赖
    python scripts/setup_env.py --check  # 仅检查，不安装
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_VENV_BIN = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
VENV_PYTHON = (_VENV_BIN / "python.exe") if os.name == "nt" else (_VENV_BIN / "python")
MARKER = ROOT / ".venv" / ".ssu-env-ready"
MIN_PYTHON = (3, 12)


def _run(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("$", " ".join(cmd), flush=True)
    merged = os.environ.copy()
    if env:
        merged.update(env)
    subprocess.check_call(cmd, cwd=cwd, env=merged)


def _find_uv() -> str | None:
    return shutil.which("uv")


def _install_uv_windows() -> str | None:
    print("未检测到 uv，正在自动安装（Astral 官方安装器）…", flush=True)
    ps = (
        "irm https://astral.sh/uv/install.ps1 | iex; "
        "$bin = Join-Path $env:USERPROFILE '.local\\bin'; "
        "if (Test-Path $bin) { $env:Path = \"$bin;$env:Path\" }; "
        "uv --version"
    )
    try:
        subprocess.check_call(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            cwd=ROOT,
        )
    except subprocess.CalledProcessError:
        return None
    return _find_uv()


def _install_uv_unix() -> str | None:
    print("未检测到 uv，正在自动安装…", flush=True)
    try:
        subprocess.check_call(
            ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
            cwd=ROOT,
        )
    except subprocess.CalledProcessError:
        return None
    home = Path.home() / ".local" / "bin" / "uv"
    if home.is_file():
        return str(home)
    return _find_uv()


def ensure_uv() -> str:
    uv = _find_uv()
    if uv:
        return uv
    if platform.system() == "Windows":
        uv = _install_uv_windows()
    else:
        uv = _install_uv_unix()
    if not uv:
        raise SystemExit(
            "无法安装 uv。请手动安装: https://github.com/astral-sh/uv\n"
            "Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        )
    return uv


def ensure_python(uv: str) -> None:
    """让 uv 准备 Python 3.12（无则自动下载）。"""
    pin = ROOT / ".python-version"
    if not pin.is_file():
        pin.write_text("3.12\n", encoding="utf-8")
    try:
        _run([uv, "python", "install", "3.12"])
    except subprocess.CalledProcessError:
        print("提示：若本机已有 Python 3.12+，uv sync 仍会尝试使用。", flush=True)


def sync_deps(uv: str, *, dev: bool, frozen: bool) -> None:
    cmd = [uv, "sync"]
    if frozen:
        cmd.append("--frozen")
    if dev:
        cmd.extend(["--group", "dev"])
    _run(cmd)


def verify_env() -> None:
    if not VENV_PYTHON.is_file():
        raise SystemExit(f"未找到虚拟环境: {VENV_PYTHON}\n请先成功运行 uv sync。")
    _run(
        [
            str(VENV_PYTHON),
            "-c",
            "import PIL; import siglus_ssu_gui; import siglus_ssu; "
            "print('环境 OK — GUI', siglus_ssu_gui.__version__)",
        ]
    )


def check_only() -> int:
    if not VENV_PYTHON.is_file():
        print("未配置：缺少 .venv")
        return 1
    try:
        verify_env()
    except subprocess.CalledProcessError:
        print("环境不完整或依赖损坏")
        return 1
    print("环境已就绪")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="配置 SiglusSSU-GUI 环境")
    parser.add_argument("--dev", action="store_true", help="安装开发依赖（PyInstaller、ruff 等）")
    parser.add_argument("--check", action="store_true", help="仅检查环境是否可用")
    parser.add_argument(
        "--frozen",
        action="store_true",
        help="严格按 uv.lock 安装（CI 用；默认允许必要时更新 lock）",
    )
    args = parser.parse_args()

    if args.check:
        return check_only()

    if sys.version_info < MIN_PYTHON:
        print(
            f"提示：当前解释器为 Python {sys.version_info.major}.{sys.version_info.minor}，"
            f"运行环境将由 uv 准备 Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}。",
            flush=True,
        )

    os.chdir(ROOT)
    print(f"项目目录: {ROOT}")
    print(f"需要 Python >={MIN_PYTHON[0]}.{MIN_PYTHON[1]}", flush=True)

    uv = ensure_uv()
    _run([uv, "--version"])
    ensure_python(uv)
    sync_deps(uv, dev=args.dev, frozen=args.frozen)
    verify_env()

    MARKER.write_text("ok\n", encoding="utf-8")
    print()
    print("=" * 50)
    print("  环境配置完成")
    print("=" * 50)
    print()
    print("启动 GUI:")
    if platform.system() == "Windows":
        print("  双击  启动 SiglusSSU-GUI.bat")
        print("  或    uv run siglus-ssu-gui")
    else:
        print("  uv run siglus-ssu-gui")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
