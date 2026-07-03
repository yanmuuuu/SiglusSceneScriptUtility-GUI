"""SiglusSceneScriptUtility GUI 入口。

便携版（PyInstaller）下同一 exe 兼作 GUI 与 CLI：
  SiglusSSU-GUI.exe           → 图形界面
  SiglusSSU-GUI.exe --ssu-cli → 内部调用 siglus-ssu
"""

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
