"""PyInstaller 入口：使用绝对导入，避免 frozen 下相对导入失败。"""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--ssu-cli":
        sys.argv = ["siglus-ssu", *sys.argv[2:]]
        from siglus_ssu.__main__ import main as cli_main

        raise SystemExit(cli_main())
    from siglus_ssu_gui.app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
