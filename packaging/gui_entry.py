"""PyInstaller 入口：使用绝对导入，避免 frozen 下相对导入失败。"""

from __future__ import annotations

import multiprocessing
import sys


def main() -> None:
    # Windows 便携版下 ProcessPoolExecutor 会重新执行本 exe；
    # freeze_support + 跳过 worker 子进程，避免每开一个 worker 就弹一个 GUI 窗口。
    multiprocessing.freeze_support()
    if multiprocessing.parent_process() is not None:
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "--ssu-cli":
        sys.argv = ["siglus-ssu", *sys.argv[2:]]
        from siglus_ssu.__main__ import main as cli_main

        raise SystemExit(cli_main())
    from siglus_ssu_gui.app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
