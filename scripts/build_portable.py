#!/usr/bin/env python3
"""构建 Windows 便携版：解压到任意目录，双击 SiglusSSU-GUI.exe 即可使用。

用法（维护者/CI 在本机执行一次打包；最终用户无需 Python）：
    python scripts/build_portable.py          # 无 Rust 时自动打纯 Python 包
    python scripts/build_portable.py --rust   # 强制编译 Rust 加速（需安装 Rust）

产出：
    dist/SiglusSSU-GUI/          便携版文件夹（可整个复制到桌面）
    dist/SiglusSSU-GUI-portable.zip
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST_DIR = ROOT / "dist" / "SiglusSSU-GUI"
SPEC = ROOT / "packaging" / "SiglusSSU-GUI.spec"
README_TXT = ROOT / "packaging" / "使用说明.txt"


def run(cmd: list[str], **kwargs) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT, **kwargs)


def has_rust() -> bool:
    return shutil.which("cargo") is not None


def ensure_built(*, want_rust: bool) -> bool:
    """安装打包依赖。返回是否成功包含 native_accel。"""
    run([sys.executable, "-m", "pip", "install", "-U", "pyinstaller>=6.6"])
    if want_rust:
        if not has_rust():
            print(
                "错误：指定了 --rust，但未找到 cargo。\n"
                "请安装 Rust：https://rustup.rs/\n"
                "或去掉 --rust，打纯 Python 便携版。",
                file=sys.stderr,
            )
            raise SystemExit(1)
        run([sys.executable, "-m", "pip", "install", "-U", "maturin"])
        print("正在编译 Rust 原生扩展（首次可能需 5–15 分钟）…", flush=True)
        run([sys.executable, "-m", "pip", "install", "-e", "."])
        sys.path.insert(0, str(SRC))
        try:
            import siglus_ssu.native_accel  # noqa: F401

            print("已包含 Rust 加速扩展。", flush=True)
            return True
        except ImportError:
            print("警告：Rust 编译完成但未找到 native_accel。", file=sys.stderr)
            return False
    print(
        "未安装 Rust/cargo，跳过 `pip install -e .`（避免卡在 maturin 编译）。\n"
        "将打包纯 Python 便携版；运行速度较慢，可在 GUI 勾选「纯 Python 模式」。",
        flush=True,
    )
    return False


def build_pyinstaller() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    src_str = str(SRC)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_str if not prev else f"{src_str}{__import__('os').pathsep}{prev}"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(SPEC),
        ],
        env=env,
    )


def post_process() -> None:
    if not DIST_DIR.is_dir():
        raise RuntimeError(f"未找到输出目录：{DIST_DIR}")
    if README_TXT.is_file():
        shutil.copy2(README_TXT, DIST_DIR / "使用说明.txt")
    launcher = DIST_DIR / "启动 SiglusSSU-GUI.bat"
    launcher.write_text(
        textwrap.dedent(
            """\
            @echo off
            chcp 65001 >nul
            cd /d "%~dp0"
            start "" "SiglusSSU-GUI.exe"
            """
        ),
        encoding="utf-8",
        newline="\r\n",
    )
    zip_base = ROOT / "dist" / "SiglusSSU-GUI-portable"
    zip_path = Path(f"{zip_base}.zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", ROOT / "dist", "SiglusSSU-GUI")
    print(f"\n完成：{DIST_DIR}")
    print(f"压缩包：{zip_path}")
    print("将整个 SiglusSSU-GUI 文件夹复制到桌面，双击 SiglusSSU-GUI.exe 即可运行。")


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 SiglusSSU-GUI Windows 便携版")
    parser.add_argument(
        "--rust",
        action="store_true",
        help="编译并打包 Rust 原生加速（需安装 Rust，耗时更长）",
    )
    args = parser.parse_args()

    if sys.platform != "win32":
        print("警告：当前脚本面向 Windows 便携版；仍尝试继续构建。", file=sys.stderr)

    ensure_built(want_rust=args.rust)
    build_pyinstaller()
    post_process()


if __name__ == "__main__":
    main()
