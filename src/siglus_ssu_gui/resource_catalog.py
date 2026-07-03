"""扫描目录并按 Siglus 资源类型分类。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

CATEGORY_ALL = "全部"
CATEGORY_IMAGE = "图片"
CATEGORY_AUDIO = "音频"
CATEGORY_VIDEO = "视频"
CATEGORY_SCRIPT = "脚本"
CATEGORY_OTHER = "其他"

CATEGORIES = (
    CATEGORY_ALL,
    CATEGORY_IMAGE,
    CATEGORY_AUDIO,
    CATEGORY_VIDEO,
    CATEGORY_SCRIPT,
    CATEGORY_OTHER,
)

_EXT_IMAGE = {".g00", ".g01", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
_EXT_AUDIO = {".ovk", ".owp", ".nwa", ".ogg", ".wav", ".mp3"}
_EXT_VIDEO = {".omv", ".ogv", ".mp4", ".webm"}
_EXT_SCRIPT = {
    ".pck",
    ".ss",
    ".dat",
    ".ini",
    ".inc",
    ".csv",
    ".txt",
    ".json",
    ".tutorial.json",
}
_EXT_OTHER = {".dbs", ".exe", ".dll", ".html", ".lzss", ".sav", ".gan"}

_TYPE_LABELS = {
    ".g00": "G00 立绘/背景",
    ".g01": "G01 图片",
    ".pck": "场景包",
    ".ss": "SceneScript",
    ".dat": "编译脚本",
    ".ovk": "语音包",
    ".owp": "音效包",
    ".nwa": "BGM",
    ".omv": "视频",
    ".ogg": "Ogg 音频",
    ".dbs": "数据库",
    ".exe": "可执行文件",
    ".ini": "配置",
    ".csv": "CSV",
    ".json": "JSON",
}


SIZE_UNKNOWN = -1


@dataclass(frozen=True, slots=True)
class ResourceEntry:
    path: Path
    category: str
    type_label: str
    size: int
    rel_name: str

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_known(self) -> bool:
        return self.size >= 0


def hydrate_size(entry: ResourceEntry) -> ResourceEntry:
    """按需读取文件大小（懒加载）。"""
    if entry.size_known:
        return entry
    try:
        size = entry.path.stat().st_size
    except OSError:
        size = 0
    return ResourceEntry(
        path=entry.path,
        category=entry.category,
        type_label=entry.type_label,
        size=size,
        rel_name=entry.rel_name,
    )


def classify_extension(ext: str) -> str:
    e = ext.lower()
    if e in _EXT_IMAGE:
        return CATEGORY_IMAGE
    if e in _EXT_AUDIO:
        return CATEGORY_AUDIO
    if e in _EXT_VIDEO:
        return CATEGORY_VIDEO
    if e in _EXT_SCRIPT:
        return CATEGORY_SCRIPT
    if e in _EXT_OTHER:
        return CATEGORY_OTHER
    return CATEGORY_OTHER


def type_label_for(path: Path) -> str:
    return _TYPE_LABELS.get(path.suffix.lower(), path.suffix.lower() or "文件")


def iter_directory_entries(
    root: Path,
    *,
    recursive: bool = True,
    category: str = CATEGORY_ALL,
    query: str = "",
    max_files: int = 8000,
    include_size: bool = False,
):
    """逐条产出资源条目；默认仅路径与类型（不 stat），适合大目录懒加载。"""
    if not root.is_dir():
        return
    q = query.strip().lower()
    count = 0
    walker = root.rglob("*") if recursive else root.iterdir()
    for path in walker:
        if count >= max_files:
            break
        try:
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            cat = classify_extension(path.suffix)
            if category != CATEGORY_ALL and cat != category:
                continue
            rel = path.relative_to(root).as_posix()
            if q and q not in rel.lower() and q not in path.name.lower():
                continue
            size = SIZE_UNKNOWN
            if include_size:
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
            yield ResourceEntry(
                path=path,
                category=cat,
                type_label=type_label_for(path),
                size=size,
                rel_name=rel,
            )
            count += 1
        except (OSError, ValueError):
            continue


def scan_directory(
    root: Path,
    *,
    recursive: bool = True,
    category: str = CATEGORY_ALL,
    query: str = "",
    max_files: int = 8000,
) -> list[ResourceEntry]:
    entries = list(
        iter_directory_entries(
            root,
            recursive=recursive,
            category=category,
            query=query,
            max_files=max_files,
            include_size=False,
        )
    )
    entries.sort(key=lambda e: (e.category, e.rel_name.lower()))
    return entries


def format_size(num: int) -> str:
    if num < 0:
        return "—"
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num / 1024:.1f} KB"
    if num < 1024 * 1024 * 1024:
        return f"{num / (1024 * 1024):.1f} MB"
    return f"{num / (1024 * 1024 * 1024):.2f} GB"


def panel_for_entry(entry: ResourceEntry) -> str | None:
    ext = entry.path.suffix.lower()
    if ext in {".g00", ".g01"} or entry.category == CATEGORY_IMAGE and ext in _EXT_IMAGE:
        return "g00"
    if ext in {".ovk", ".owp", ".nwa", ".ogg"} or entry.category == CATEGORY_AUDIO:
        return "sound"
    if ext in {".omv", ".ogv"}:
        return "video"
    if ext == ".pck":
        return "extract"
    if ext == ".dbs":
        return "db"
    if ext in {".ss", ".dat"}:
        return "textmap"
    if ext == ".exe" and "siglus" in entry.name.lower():
        return "patch"
    return None
