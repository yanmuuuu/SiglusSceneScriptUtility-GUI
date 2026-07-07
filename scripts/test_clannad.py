#!/usr/bin/env python3
"""用 CLANNAD 游戏目录批量测试 siglus-ssu CLI（与 GUI 子进程一致）。"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r"C:\steam\steamapps\common\CLANNAD")
OUT = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "g00"
OUT.mkdir(parents=True, exist_ok=True)

G00_FILE = GAME / "g00" / "_BL_EXIT.g00"
PCK = GAME / "SceneZH.pck"
GAMEEXE = GAME / "GameexeZH.dat"
ENGINE = GAME / "SiglusEngine_Steam.exe"
NWA = GAME / "bgm" / "BGM01.nwa"
OMV = GAME / "mov" / "SZZC.omv"
DBS = GAME / "dat" / "text00.dbs"


def run(name: str, argv: list[str], *, timeout: int = 300) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "siglus_ssu"] + argv
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = time.perf_counter() - t0
        ok = proc.returncode == 0
        detail = (proc.stdout or "") + (proc.stderr or "")
        status = "OK" if ok else f"FAIL({proc.returncode})"
        print(f"[{status}] {name} ({elapsed:.1f}s)")
        if not ok:
            print(detail[-2000:])
        return ok, detail
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name} (>{timeout}s)")
        return False, "timeout"
    except Exception as exc:
        print(f"[ERROR] {name}: {exc}")
        return False, str(exc)


def main() -> int:
    quick = "--quick" in sys.argv
    if not GAME.is_dir():
        print(f"游戏目录不存在：{GAME}")
        return 1
    print(f"游戏：{GAME}")
    print(f"输出：{OUT}\n")

    cases: list[tuple[str, list[str], int]] = [
        ("init", ["init"], 60),
        ("g00-analyze", ["-g", "--a", str(G00_FILE)], 30),
        ("g00-extract", ["-g", "--x", str(G00_FILE), str(OUT / "g00_png")], 60),
        ("analyze-pck", ["-a", str(PCK)], 120),
        ("analyze-gei", ["-a", "--gei", str(GAMEEXE)], 30),
        ("extract-pck", ["-x", str(PCK), str(OUT / "scene_extract")], 300),
        ("sound-analyze", ["-s", "--a", str(NWA)], 30),
        ("sound-extract", ["-s", "--x", str(NWA), str(OUT / "sound_wav")], 60),
        ("video-analyze", ["-v", "--a", str(OMV)], 30),
        ("video-extract", ["-v", "--x", str(OMV), str(OUT / "video_ogv")], 120),
        ("db-analyze", ["-d", "--a", str(DBS)], 30),
        ("db-extract", ["-d", "--x", str(DBS), str(OUT / "db_csv")], 60),
        ("patch-info", ["-p", "--info", str(ENGINE)], 30),
        ("tutorial", ["-t", str(PCK), str(OUT / "tutorial.json")], 180),
        ("koe-stats", ["-k", "--stats-only", str(PCK), str(GAME / "koe"), str(OUT / "koe_stats")], 120),
    ]
    if not quick:
        cases.extend(
            [
                ("textmap", ["-m", str(OUT / "scene_extract")], 120),
                ("roundtrip-test", ["test", str(PCK)], 600),
            ]
        )

    failed: list[str] = []
    for name, argv, timeout in cases:
        ok, _ = run(name, argv, timeout=timeout)
        if not ok:
            failed.append(name)

    print("\n--- GUI panel argv ---")
    panel_script = ROOT / "scripts" / "test_panel_argv.py"
    if panel_script.is_file():
        proc = subprocess.run(
            [sys.executable, str(panel_script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            print("[OK] panel-argv (41 cases)")
        else:
            print("[FAIL] panel-argv")
            print((proc.stdout or "") + (proc.stderr or ""))
            failed.append("panel-argv")

    print("\n--- GUI PreviewService ---")
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from siglus_ssu_gui.resource_catalog import scan_directory
        from siglus_ssu_gui.preview_service import PreviewService
        from siglus_ssu_gui.resource_catalog import ResourceEntry, panel_for_entry

        t0 = time.perf_counter()
        g00_entries = scan_directory(GAME / "g00")
        print(f"[OK] scan-g00 {len(g00_entries)} files ({time.perf_counter()-t0:.2f}s)")

        svc = PreviewService()
        ent = ResourceEntry(
            path=G00_FILE,
            category="g00",
            type_label="G00",
            size=G00_FILE.stat().st_size,
            rel_name=G00_FILE.name,
        )
        t0 = time.perf_counter()
        img, err = svc.load_preview_image(G00_FILE)
        elapsed = time.perf_counter() - t0
        if img is not None:
            print(f"[OK] preview-g00 ({elapsed:.2f}s) {img.size}")
        else:
            print(f"[FAIL] preview-g00: {err}")
            failed.append("preview-g00")
        panel = panel_for_entry(ent)
        if panel == "g00":
            print("[OK] jump-panel-g00")
        else:
            print(f"[FAIL] jump-panel: {panel}")
            failed.append("jump-panel")
        if svc.can_play_audio(
            ResourceEntry(
                path=NWA,
                category="audio",
                type_label="NWA",
                size=NWA.stat().st_size,
                rel_name="BGM01.nwa",
            )
        ):
            err = svc.play_audio(NWA)
            if err:
                print(f"[WARN] play-audio: {err} (可能缺 ffplay)")
            else:
                print("[OK] play-audio started")
                svc.stop_audio()
        else:
            print("[FAIL] can_play_audio")
            failed.append("can_play_audio")
    except Exception as exc:
        print(f"[ERROR] PreviewService: {exc}")
        failed.append("preview-service")

    print("\n========== 汇总 ==========")
    if failed:
        print("失败：", ", ".join(failed))
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
