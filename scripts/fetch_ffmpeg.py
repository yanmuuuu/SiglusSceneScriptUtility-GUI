#!/usr/bin/env python3
"""CLI：下载 Windows 版 ffmpeg 供便携包捆绑。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from siglus_ssu.ffmpeg_fetch import install_ffmpeg_windows  # noqa: E402

DEFAULT_BIN = ROOT / "build" / "ffmpeg" / "bin"


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 ffmpeg essentials 到 build/ffmpeg/bin")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--target", type=Path, default=DEFAULT_BIN)
    args = parser.parse_args()
    print(f"正在安装 ffmpeg 到 {args.target} …", flush=True)
    install_ffmpeg_windows(args.target, force=args.force)
    print(f"完成：{args.target}", flush=True)


if __name__ == "__main__":
    main()
