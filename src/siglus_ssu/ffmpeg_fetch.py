"""下载并安装 Windows 版 ffmpeg（供便携版捆绑或首次播放时安装）。"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# 按优先级尝试：GitHub 镜像通常比 gyan.dev 更快
FFMPEG_URLS = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip",
    "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip",
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
)


def _download_curl(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "curl.exe",
            "-fL",
            "--retry",
            "3",
            "--retry-delay",
            "2",
            "--connect-timeout",
            "30",
            "-o",
            str(dest),
            url,
        ],
    )
    if dest.stat().st_size < 1_000_000:
        raise RuntimeError("下载文件过小，可能不完整")


def _download_powershell(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ps = (
        '$ProgressPreference = "SilentlyContinue"; '
        f'Invoke-WebRequest -Uri "{url}" -OutFile "{dest}" -UseBasicParsing'
    )
    subprocess.check_call(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
    )
    if dest.stat().st_size < 1_000_000:
        raise RuntimeError("下载文件过小，可能不完整")


def _download_urllib(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "SiglusSSU-GUI"})
    with urllib.request.urlopen(req, timeout=600) as resp, dest.open("wb") as out:
        total = int(resp.headers.get("Content-Length", 0) or 0)
        done = 0
        while True:
            chunk = resp.read(512 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total and done % (5 * 1024 * 1024) < len(chunk):
                pct = done * 100 // total
                print(f"\r  下载中… {pct}% ({done // (1024 * 1024)} / {total // (1024 * 1024)} MB)", end="", flush=True)
        if total:
            print(flush=True)
    if dest.stat().st_size < 1_000_000:
        raise RuntimeError("下载文件过小，可能不完整")


def _download(url: str, dest: Path) -> None:
    errors: list[str] = []
    if shutil.which("curl.exe"):
        try:
            _download_curl(url, dest)
            return
        except Exception as exc:
            errors.append(f"curl: {exc}")
            dest.unlink(missing_ok=True)
    try:
        _download_powershell(url, dest)
        return
    except Exception as exc:
        errors.append(f"powershell: {exc}")
        dest.unlink(missing_ok=True)
    try:
        _download_urllib(url, dest)
        return
    except Exception as exc:
        errors.append(f"urllib: {exc}")
        dest.unlink(missing_ok=True)
    raise RuntimeError("; ".join(errors))


def _extract_bin(zip_path: Path, out_bin: Path) -> None:
    if out_bin.exists():
        shutil.rmtree(out_bin)
    out_bin.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            norm = name.replace("\\", "/")
            if "/bin/" not in norm or norm.endswith("/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix not in {".exe", ".dll"}:
                continue
            target = out_bin / Path(name).name
            with zf.open(name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def install_ffmpeg_windows(target_bin: Path, *, force: bool = False) -> Path:
    if (
        not force
        and target_bin.is_dir()
        and (target_bin / "ffplay.exe").is_file()
        and (target_bin / "ffmpeg.exe").is_file()
    ):
        return target_bin
    last_err: Exception | None = None
    with tempfile.TemporaryDirectory(prefix="ssu_ffmpeg_") as tmp:
        zpath = Path(tmp) / "ffmpeg.zip"
        for url in FFMPEG_URLS:
            print(f"尝试下载 ffmpeg：{url}", flush=True)
            try:
                _download(url, zpath)
                _extract_bin(zpath, target_bin)
                if (target_bin / "ffplay.exe").is_file():
                    print(f"已安装 ffmpeg → {target_bin}", flush=True)
                    return target_bin
                raise RuntimeError(f"压缩包内未找到 ffplay.exe：{url}")
            except Exception as exc:
                last_err = exc
                print(f"  失败：{exc}", flush=True)
                zpath.unlink(missing_ok=True)
                if target_bin.exists():
                    shutil.rmtree(target_bin, ignore_errors=True)
    raise RuntimeError(f"所有下载源均失败：{last_err}")


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("仅支持 Windows")
    root = Path(__file__).resolve().parents[2]
    target = root / "build" / "ffmpeg" / "bin"
    install_ffmpeg_windows(target)
    print(f"完成：{target}")


if __name__ == "__main__":
    main()
