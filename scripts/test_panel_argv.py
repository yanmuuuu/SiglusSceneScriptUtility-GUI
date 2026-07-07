#!/usr/bin/env python3
"""Instantiate each GUI panel and verify build_command() argv (no mainloop)."""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from siglus_ssu_gui.panels import PANELS  # noqa: E402
from siglus_ssu_gui.panels.browser_panel import BrowserPanel  # noqa: E402
from siglus_ssu_gui.theme import apply_theme, prepare_display  # noqa: E402

GAME = Path(r"C:\steam\steamapps\common\CLANNAD")
OUT = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "g00"
OUT.mkdir(parents=True, exist_ok=True)

PATHS = {
    "pck": GAME / "SceneZH.pck",
    "gameexe": GAME / "GameexeZH.dat",
    "engine": GAME / "SiglusEngine_Steam.exe",
    "g00": GAME / "g00" / "_BL_EXIT.g00",
    "g00b": GAME / "g00" / "AKA.g00",
    "nwa": GAME / "bgm" / "BGM01.nwa",
    "omv": GAME / "mov" / "SZZC.omv",
    "dbs": GAME / "dat" / "text00.dbs",
    "koe": GAME / "koe",
    "game": GAME,
}

VALID_PREFIXES = frozenset(
    {"-x", "-c", "-a", "-g", "-s", "-v", "-d", "-k", "-m", "-p", "-t", "-e", "init", "test", "-lsp"}
)
NON_CLI_PANELS = frozenset({"manual", "browser"})


def set_text(row: Any, value: str) -> None:
    row.var.set(value)


def set_op(panel: Any, value: str) -> None:
    op = panel.op
    if hasattr(op, "set"):
        op.set(value)
    else:
        op.set(value)  # Combobox
    if hasattr(panel, "_on_op"):
        panel._on_op()


def set_mode(panel: Any, value: str) -> None:
    panel.mode.set(value)


def fill_merge_list(row: Any, *paths: Path) -> None:
    row.listbox.delete(0, tk.END)
    for p in paths:
        row.listbox.insert(tk.END, str(p))


def is_valid_argv(argv: list[str]) -> str | None:
    if not argv:
        return "empty argv"
    if not all(isinstance(x, str) and x for x in argv):
        return "argv contains non-string or empty element"
    if argv[0] not in VALID_PREFIXES:
        return f"unexpected command prefix: {argv[0]!r}"
    return None


def run_case(
    key: str,
    label: str,
    panel: Any,
    configure: Callable[[], None],
    *,
    expect_cli: bool = True,
) -> tuple[bool, str]:
    try:
        configure(panel)
        panel.update_idletasks()
        result = panel.build_command()
    except Exception:
        return False, f"CRASH: {traceback.format_exc(limit=3)}"

    if not expect_cli:
        if isinstance(result, str):
            return True, f"non-CLI: {result[:60]}…"
        return False, f"expected non-CLI message, got {result!r}"

    if isinstance(result, str):
        return False, f"validation error: {result}"
    if not isinstance(result, tuple) or len(result) != 2:
        return False, f"unexpected return type: {type(result)!r}"
    argv, _hint = result
    if not isinstance(argv, list):
        return False, f"argv is not a list: {type(argv)!r}"
    if err := is_valid_argv(argv):
        return False, err
    return True, " ".join(argv)


def configure_extract(panel: Any, op: str) -> None:
    set_op(panel, op)
    if op == "pck":
        panel.input_row.set(str(PATHS["pck"]))
        panel.output_row.set(str(OUT / "scene_extract"))
    elif op == "disam":
        panel.input_row.set(str(PATHS["pck"]))
        panel.output_row.set(str(OUT / "disam_out"))
    else:
        panel.input_row.set(str(PATHS["gameexe"]))
        panel.output_row.set(str(OUT / "gei_out"))


def configure_compile(panel: Any, op: str) -> None:
    work = OUT / "scene_extract"
    work.mkdir(parents=True, exist_ok=True)
    set_op(panel, op)
    panel.input_row.set(str(work))
    if op == "gei":
        panel.output_row.set(str(OUT / "gei_compile"))
    else:
        panel.output_row.set(str(OUT / "Scene_out.pck"))


def configure_analyze(panel: Any, op: str) -> None:
    set_op(panel, op)
    if op == "比较两个文件":
        panel.in1.set(str(PATHS["pck"]))
        panel.in2.set(str(PATHS["pck"]))
    elif op == "台词统计导出 CSV":
        panel.in1.set(str(PATHS["pck"]))
        panel.csv_out.set(str(OUT / "words.csv"))
    elif op == "分析 Gameexe.dat":
        panel.in1.set(str(PATHS["gameexe"]))
    else:
        panel.in1.set(str(PATHS["pck"]))


def configure_g00(panel: Any, op: str, tmp: Path) -> None:
    set_op(panel, op)
    if op.startswith("分析"):
        panel.input_row.set(str(PATHS["g00"]))
    elif op.startswith("提取"):
        panel.input_row.set(str(PATHS["g00"]))
        panel.output_row.set(str(OUT / "g00_png"))
    elif op.startswith("合并"):
        fill_merge_list(panel.merge_list, PATHS["g00"], PATHS["g00b"])
        panel.output_row.set(str(OUT / "g00_merge"))
    else:
        dummy_png = tmp / "dummy.png"
        dummy_png.write_bytes(b"\x89PNG\r\n\x1a\n")
        panel.input_row.set(str(dummy_png))
        panel.output_row.set(str(OUT / "created.g00"))
        set_text(panel.type_row, "1")


def configure_sound(panel: Any, op: str, tmp: Path) -> None:
    set_op(panel, op)
    if op.startswith("分析"):
        panel.input_row.set(str(PATHS["nwa"]))
    elif op.startswith("播放"):
        panel.input_row.set(str(PATHS["nwa"]))
        panel.gameexe_row.set(str(PATHS["gameexe"]))
    elif op.startswith("提取"):
        panel.input_row.set(str(PATHS["nwa"]))
        panel.output_row.set(str(OUT / "sound_wav"))
        panel.gameexe_row.set(str(PATHS["gameexe"]))
    else:
        dummy_ogg = tmp / "dummy.ogg"
        dummy_ogg.write_bytes(b"OggS")
        panel.input_row.set(str(dummy_ogg))
        panel.output_row.set(str(OUT / "sound_enc"))


def configure_video(panel: Any, op: str, tmp: Path) -> None:
    set_op(panel, op)
    if op.startswith("分析"):
        panel.input_row.set(str(PATHS["omv"]))
    elif op.startswith("提取"):
        panel.input_row.set(str(PATHS["omv"]))
        panel.output_row.set(str(OUT / "video_ogv"))
    else:
        dummy_ogv = tmp / "dummy.ogv"
        dummy_ogv.write_bytes(b"OggS")
        panel.input_row.set(str(dummy_ogv))
        panel.output_row.set(str(OUT / "encoded.omv"))
        panel.refer_row.set(str(PATHS["omv"]))


def configure_db(panel: Any, op: str, tmp: Path) -> None:
    set_op(panel, op)
    if op.startswith("分析"):
        panel.input_row.set(str(PATHS["dbs"]))
    elif op.startswith("导出"):
        panel.input_row.set(str(PATHS["dbs"]))
        panel.output_row.set(str(OUT / "db_csv"))
    else:
        dummy_csv = tmp / "dummy.csv"
        dummy_csv.write_text("a,b\n1,2\n", encoding="utf-8")
        panel.input_row.set(str(dummy_csv))
        panel.output_row.set(str(OUT / "compiled.dbs"))
        set_text(panel.type_row, "0")


def configure_koe(panel: Any, mode: str) -> None:
    set_mode(panel, mode)
    panel.voice_row.set(str(PATHS["koe"]))
    out = OUT / "koe_out"
    out.mkdir(parents=True, exist_ok=True)
    panel.output_row.set(str(out))
    if mode == "single":
        set_text(panel.koe_no, "1")
    else:
        panel.scene_row.set(str(PATHS["pck"]))


def configure_textmap(panel: Any, op: str) -> None:
    panel.op.set(op)
    if op in {"dat", "dat_apply"}:
        panel.input_row.set(str(PATHS["gameexe"]))
    else:
        panel.input_row.set(str(PATHS["pck"]))


def configure_patch(panel: Any, op: str) -> None:
    set_op(panel, op)
    panel.exe_row.set(str(PATHS["engine"]))
    if op.startswith("更换"):
        panel.key_row.set(str(PATHS["gameexe"]))
        panel.output_row.set(str(OUT / "patched.exe"))
    elif op.startswith("地域"):
        panel.loc.set("关闭 (0)")
    elif not op.startswith("查看"):
        panel.output_row.set(str(OUT / "patched.exe"))


def build_cases(tmp: Path) -> list[tuple[str, str, type, Callable[[Any], None], bool]]:
    """key, case_label, panel_class, configure(panel), expect_cli"""
    cases: list[tuple[str, str, type, Callable[[Any], None], bool]] = []

    for op in ("pck", "disam", "gei"):
        cases.append(("extract", op, None, lambda p, o=op: configure_extract(p, o), True))
    for op in ("std", "gei"):
        cases.append(("compile", op, None, lambda p, o=op: configure_compile(p, o), True))
    for op in ("分析单个文件", "比较两个文件", "台词统计导出 CSV", "分析 Gameexe.dat"):
        cases.append(("analyze", op, None, lambda p, o=op: configure_analyze(p, o), True))
    for op in ("分析 --a", "提取 --x", "合并 --m", "创建 --c"):
        cases.append(("g00", op, None, lambda p, o=op: configure_g00(p, o, tmp), True))
    for op in ("提取 --x", "分析 --a", "编码 --c", "播放 --play"):
        cases.append(("sound", op, None, lambda p, o=op: configure_sound(p, o, tmp), True))
    for op in ("提取 --x", "分析 --a", "编码 --c"):
        cases.append(("video", op, None, lambda p, o=op: configure_video(p, o, tmp), True))
    for op in ("导出 --x", "分析 --a", "编译 --c"):
        cases.append(("db", op, None, lambda p, o=op: configure_db(p, o, tmp), True))
    for mode in ("scene", "single"):
        cases.append(("koe", mode, None, lambda p, m=mode: configure_koe(p, m), True))
    for op in ("ss", "ss_apply", "dat", "dat_apply"):
        cases.append(("textmap", op, None, lambda p, o=op: configure_textmap(p, o), True))
    for op in (
        "更换密钥 --altkey",
        "CJK 语言 --lang cjk",
        "CJK + 中文路径 --lang cjk-path",
        "查看信息 --info",
        "地域检测 --loc",
    ):
        cases.append(("patch", op, None, lambda p, o=op: configure_patch(p, o), True))

    cases.extend(
        [
            (
                "tutorial",
                "default",
                None,
                lambda p: (
                    p.input_row.set(str(PATHS["pck"])),
                    p.output_row.set(str(OUT / "tutorial.json")),
                ),
                True,
            ),
            (
                "exec",
                "default",
                None,
                lambda p: (
                    p.engine_row.set(str(PATHS["engine"])),
                    set_text(p.scene_row, "test_scene"),
                    set_text(p.label_row, "test_label"),
                ),
                True,
            ),
            ("init", "default", None, lambda _p: None, True),
            ("test", "default", None, lambda p: p.input_row.set(str(PATHS["pck"])), True),
            ("lsp", "default", None, lambda _p: None, True),
            ("manual", "default", None, lambda _p: None, False),
            ("browser", "default", BrowserPanel, lambda p: p._root_row.set(str(PATHS["game"])), False),
        ]
    )
    return cases


def main() -> int:
    if not GAME.is_dir():
        print(f"游戏目录不存在：{GAME}")
        return 1

    missing = [k for k, p in PATHS.items() if k not in {"game"} and not Path(p).exists()]
    if missing:
        print("缺少样本文件：", ", ".join(missing))
        return 1

    prepare_display()
    root = tk.Tk()
    root.withdraw()
    apply_theme(root)
    host = ttk.Frame(root)
    host.pack()

    panel_classes = dict(PANELS)
    panel_classes["browser"] = BrowserPanel
    panels: dict[str, Any] = {}

    tested_keys: set[str] = set()
    failures: list[str] = []
    passes: list[str] = []

    with tempfile.TemporaryDirectory(prefix="ssu_panel_argv_") as tmpdir:
        tmp = Path(tmpdir)
        cases = build_cases(tmp)

        for key, case_label, _cls_override, configure, expect_cli in cases:
            tested_keys.add(key)
            tag = f"{key}/{case_label}"
            try:
                if key not in panels:
                    if key == "browser":
                        panels[key] = BrowserPanel(host, app=None)
                    else:
                        panels[key] = panel_classes[key](host)
                    panels[key].update_idletasks()
            except Exception:
                failures.append(f"{tag}: INSTANTIATE CRASH\n{traceback.format_exc(limit=3)}")
                continue

            ok, detail = run_case(key, case_label, panels[key], configure, expect_cli=expect_cli)
            if ok:
                passes.append(f"{tag}: {detail}")
            else:
                failures.append(f"{tag}: {detail}")

    root.destroy()

    print(f"GAME={GAME}")
    print(f"OUT={OUT}")
    print(f"\nPanel keys tested ({len(tested_keys)}): {', '.join(sorted(tested_keys))}")
    print(f"Cases run: {len(passes) + len(failures)}  passed: {len(passes)}  failed: {len(failures)}")

    if failures:
        print("\n--- FAILURES ---")
        for line in failures:
            print(line)
        return 1

    print("\nAll panel argv builds OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
