"""资源预览：图片缩略图、音频试听、文本摘要。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from .resource_catalog import CATEGORY_IMAGE, ResourceEntry, format_size

_PREVIEWABLE_IMAGE = {".g00", ".g01", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
_PREVIEWABLE_AUDIO = {".ogg", ".wav", ".owp", ".nwa", ".mp3"}
_TEXT_PREVIEW = {".ss", ".ini", ".inc", ".csv", ".txt", ".json", ".dat"}
_VIDEO_EXT = {".omv", ".ogv", ".mp4", ".webm"}


class PreviewService:
    def __init__(self) -> None:
        self._audio_proc: subprocess.Popen[bytes] | None = None
        self._temp_dirs: list[str] = []
        self._g00_scratch: str | None = None
        self._lock = threading.Lock()

    def cleanup(self) -> None:
        self.stop_audio()
        with self._lock:
            for d in self._temp_dirs:
                shutil.rmtree(d, ignore_errors=True)
            self._temp_dirs.clear()

    def _remember_temp(self, path: str) -> None:
        with self._lock:
            self._temp_dirs.append(path)

    def stop_audio(self) -> None:
        proc = self._audio_proc
        self._audio_proc = None
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def info_text(self, entry: ResourceEntry) -> str:
        p = entry.path
        lines = [
            entry.rel_name,
            f"类型：{entry.type_label}（{entry.category}）",
            f"大小：{format_size(entry.size)}",
            f"路径：{p}",
        ]
        ext = p.suffix.lower()
        if ext == ".pck":
            lines.extend(
                [
                    "",
                    "Scene.pck 为加密场景包，无法像文件夹直接预览内容。",
                    "请使用左侧「提取」解包，或点下方「跳转：提取」一键填入路径。",
                ]
            )
        elif ext == ".ovk":
            lines.extend(["", "语音包为归档格式，建议用「音频」提取或「语音收集」整理。"])
        elif ext in _VIDEO_EXT:
            lines.extend(["", "可预览：提取后用系统播放器打开，或点「播放/打开」。"])
        return "\n".join(lines)

    def text_snippet(self, path: Path, *, limit: int = 120) -> str:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return f"无法读取：{exc}"
        if path.suffix.lower() == ".dat":
            return f"二进制 .dat（{format_size(len(raw))}）\n\n请用「提取」或「分析」查看内容。"
        for enc in ("utf-8", "utf-8-sig", "cp932", "shift_jis"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                text = ""
        else:
            text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > limit:
            return "\n".join(lines[:limit]) + f"\n\n…（共 {len(lines)} 行，仅显示前 {limit} 行）"
        return text

    def load_thumbnail(self, path: Path, *, size: int = 128):
        """返回 PIL.Image 或 None。"""
        try:
            from PIL import Image
        except ImportError:
            return None
        try:
            if path.suffix.lower() in {".g00", ".g01"}:
                png = self._g00_first_png(path)
                if png is None:
                    return None
                try:
                    img = Image.open(png)
                    img.load()
                finally:
                    self._release_g00_work(png)
            else:
                img = Image.open(path)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            return img
        except Exception:
            return None

    def load_preview_image(self, path: Path, *, max_size: int = 520):
        try:
            from PIL import Image
        except ImportError:
            return None, "需要 Pillow 才能预览图片。请使用源码环境 uv sync 或更新便携版。"
        try:
            if path.suffix.lower() in {".g00", ".g01"}:
                png = self._g00_first_png(path)
                if png is None:
                    return None, "无法从 G00 解出预览图。"
                try:
                    img = Image.open(png)
                    img.load()
                finally:
                    self._release_g00_work(png)
            else:
                img = Image.open(path)
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            return img, ""
        except Exception as exc:
            return None, str(exc)

    def _g00_first_png(self, path: Path) -> Path | None:
        with self._lock:
            if self._g00_scratch is None:
                self._g00_scratch = tempfile.mkdtemp(prefix="ssu_g00_scratch_")
                self._remember_temp(self._g00_scratch)
            scratch = Path(self._g00_scratch)
        work = scratch / path.name
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True, exist_ok=True)
        try:
            from siglus_ssu import g00

            g00.extract_one(str(path), str(work))
        except Exception:
            shutil.rmtree(work, ignore_errors=True)
            return None
        pngs = sorted(work.glob("*.png"))
        if not pngs:
            shutil.rmtree(work, ignore_errors=True)
            return None
        return pngs[0]

    def _release_g00_work(self, png: Path) -> None:
        work = png.parent
        if self._g00_scratch and str(work).startswith(self._g00_scratch):
            shutil.rmtree(work, ignore_errors=True)

    def play_audio(self, path: Path) -> str | None:
        """启动试听；返回错误信息或 None。"""
        self.stop_audio()
        ext = path.suffix.lower()
        play_path = path
        if ext == ".owp":
            try:
                from siglus_ssu import sound

                ogg = sound.decode_owp_to_ogg_bytes(str(path))
                tmp = tempfile.mkdtemp(prefix="ssu_aud_prev_")
                self._remember_temp(tmp)
                play_path = Path(tmp) / "preview.ogg"
                play_path.write_bytes(ogg)
            except Exception as exc:
                return f"解码 OWP 失败：{exc}"
        elif ext == ".nwa":
            try:
                from siglus_ssu import sound

                wav_bytes = sound.decode_nwa_to_wav_bytes(str(path))
                tmp = tempfile.mkdtemp(prefix="ssu_aud_prev_")
                self._remember_temp(tmp)
                play_path = Path(tmp) / "preview.wav"
                play_path.write_bytes(wav_bytes)
            except Exception as exc:
                return f"解码 NWA 失败：{exc}"
        elif ext == ".ovk":
            return "OVK 为语音归档，请先用「音频」提取或选包内 .ogg 试听。"

        ffplay = shutil.which("ffplay")
        if ffplay:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                self._audio_proc = subprocess.Popen(
                    [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", str(play_path)],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                return None
            except OSError as exc:
                return str(exc)

        if ext == ".wav" and sys.platform == "win32":
            try:
                import winsound

                winsound.PlaySound(str(play_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return None
            except Exception as exc:
                return str(exc)

        return "未找到 ffplay。请安装 ffmpeg 并将 ffplay 加入 PATH。"

    def open_video(self, path: Path) -> str | None:
        ext = path.suffix.lower()
        target = path
        if ext == ".omv":
            try:
                from siglus_ssu import video

                tmp = tempfile.mkdtemp(prefix="ssu_vid_prev_")
                self._remember_temp(tmp)
                target = Path(tmp) / (path.stem + ".ogv")
                video.extract_ogv_from_omv(str(path), str(target))
            except Exception as exc:
                return f"提取 OMV 失败：{exc}"
        try:
            if sys.platform == "win32":
                os.startfile(target)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
            return None
        except OSError as exc:
            return str(exc)

    def can_thumbnail(self, entry: ResourceEntry) -> bool:
        return entry.path.suffix.lower() in _PREVIEWABLE_IMAGE

    def can_preview_image(self, entry: ResourceEntry) -> bool:
        return entry.category == CATEGORY_IMAGE and entry.path.suffix.lower() in _PREVIEWABLE_IMAGE

    def can_play_audio(self, entry: ResourceEntry) -> bool:
        return entry.path.suffix.lower() in _PREVIEWABLE_AUDIO

    def can_text_preview(self, entry: ResourceEntry) -> bool:
        return entry.path.suffix.lower() in _TEXT_PREVIEW

    def can_open_video(self, entry: ResourceEntry) -> bool:
        return entry.path.suffix.lower() in _VIDEO_EXT
