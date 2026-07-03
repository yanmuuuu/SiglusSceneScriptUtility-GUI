from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Any

from ..preview_service import PreviewService
from ..resource_catalog import (
    CATEGORIES,
    CATEGORY_ALL,
    CATEGORY_IMAGE,
    ResourceEntry,
    format_size,
    hydrate_size,
    iter_directory_entries,
    panel_for_entry,
)
from ..scroll import VerticalScrollArea, bind_listbox_scroll, bind_text_scroll
from ..theme import (
    BG_CARD,
    BG_PANEL,
    BORDER,
    FG,
    FG_SECONDARY,
    LIST_BG,
    LIST_HEADER_BG,
    LIST_HEADER_FG,
    make_listbox,
    ui_font,
)
from ..widgets import PathRow, Section
from .base import BasePanel

if TYPE_CHECKING:
    from ..app import MainApp

_STATE_FILE = Path(__file__).resolve().parents[2] / ".gui_state.json"
_THUMB_COLS = 5
_THUMB_ROW_HEIGHT = 132
_SCAN_BATCH = 200
_TREE_UI_CHUNK = 120
_TREE_FAST_LIMIT = 200
_THUMB_LOAD_WORKERS = 2
_THUMB_CACHE_MAX = 64


class BrowserPanel(BasePanel):
    TITLE = "资源浏览"
    HELP_DOC = "资源浏览.md"

    def __init__(self, master: tk.Misc, *, app: MainApp | None = None) -> None:
        self._app = app
        self._preview_svc = PreviewService()
        self._entries: list[ResourceEntry] = []
        self._selected: ResourceEntry | None = None
        self._thumb_photos: dict[int, tk.PhotoImage] = {}
        self._preview_photo: tk.PhotoImage | None = None
        self._scan_id = 0
        self._thumb_gen = 0
        self._thumb_loading: set[int] = set()
        self._scan_running = False
        self._thumb_image_indices: list[int] = []
        self._thumb_total_rows = 0
        self._thumb_load_sem = threading.Semaphore(_THUMB_LOAD_WORKERS)
        self._preview_token = 0
        self._thumb_last_first_row = -1
        super().__init__(master)

    def on_hide(self) -> None:
        self._scan_id += 1
        self._thumb_gen += 1
        self._scan_running = False
        self._thumb_loading.clear()
        self._preview_svc.cleanup()
        status = self._status.cget("text")
        if "扫描中" in status or "加载预览" in status:
            if self._entries:
                self._status.configure(text=f"共 {len(self._entries)} 个文件（已暂停后台任务）")
            else:
                self._status.configure(text="扫描已中断，返回本页将自动重试")

    def on_show(self) -> None:
        if self._entries:
            return
        root = self._root_row.get().strip()
        if not root or not Path(root).is_dir():
            return
        if self._scan_running:
            return
        self._status.configure(text="准备加载资源列表…")
        self.after(150, self._refresh)

    def _build(self, parent: ttk.Frame) -> None:
        top = Section(parent, "浏览根目录")
        top.pack(fill=tk.X, pady=(0, 6))
        self._root_row = PathRow(
            top.body,
            "根目录",
            mode="dir",
            hint="选择游戏目录、解包输出目录或任意文件夹（类似 FModel 选根路径）",
        )
        self._root_row.pack(fill=tk.X, pady=4)
        row = ttk.Frame(top.body)
        row.pack(fill=tk.X, pady=2)
        self._recursive = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text="包含子文件夹", variable=self._recursive).pack(side=tk.LEFT)
        ttk.Button(row, text="刷新 (F5)", style="Secondary.TButton", command=self._refresh).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ttk.Button(row, text="选择目录…", style="Secondary.TButton", command=self._browse_root).pack(
            side=tk.RIGHT
        )

        filt = ttk.Frame(parent)
        filt.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(filt, text="分类", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self._category = ttk.Combobox(
            filt, values=list(CATEGORIES), width=8, state="readonly"
        )
        self._category.set(CATEGORY_ALL)
        self._category.pack(side=tk.LEFT, padx=(8, 16))
        self._category.bind("<<ComboboxSelected>>", lambda _e: self._on_category_change())

        ttk.Label(filt, text="搜索", style="Subtitle.TLabel").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        search = ttk.Entry(filt, textvariable=self._search_var, width=28)
        search.pack(side=tk.LEFT, padx=(8, 0))
        search.bind("<KeyRelease>", self._debounced_refresh)
        self._search_after: str | None = None
        self._category_after: str | None = None
        ttk.Label(filt, text="列表", style="Hint.TLabel").pack(side=tk.RIGHT)
        self._view_mode = tk.StringVar(value="list")
        ttk.Radiobutton(
            filt, text="列表", variable=self._view_mode, value="list", command=self._switch_view
        ).pack(side=tk.RIGHT)
        ttk.Radiobutton(
            filt, text="缩略图", variable=self._view_mode, value="thumb", command=self._switch_view
        ).pack(side=tk.RIGHT, padx=(0, 8))

        split = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True, pady=4)
        self._split = split

        left = ttk.Frame(split, padding=(0, 4))
        split.add(left, weight=3)
        self._list_frame = ttk.Frame(left)
        self._thumb_frame = ttk.Frame(left)
        self._build_list_view(self._list_frame)
        self._build_thumb_view(self._thumb_frame)
        self._list_frame.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(split, padding=(8, 0, 0, 0))
        split.add(right, weight=2)
        self._build_preview_pane(right)

        actions = ttk.Frame(parent)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="预览 (Enter)", command=self._preview_selected).pack(side=tk.LEFT)
        ttk.Button(actions, text="播放/打开", style="Secondary.TButton", command=self._play_or_open).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(actions, text="停止播放", style="Secondary.TButton", command=self._stop_audio).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(actions, text="打开所在目录", style="Secondary.TButton", command=self._open_parent).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(actions, text="跳转功能", style="Secondary.TButton", command=self._jump_panel).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        self._status = ttk.Label(actions, text="", style="Hint.TLabel")
        self._status.pack(side=tk.RIGHT)

        self._bind_keys(parent)
        self._load_last_root()
        self.after_idle(lambda: split.sashpos(0, 420))

    def _build_list_view(self, parent: ttk.Frame) -> None:
        box = tk.Frame(parent, bg=BG_PANEL)
        box.pack(fill=tk.BOTH, expand=True)
        header = tk.Label(
            box,
            text="相对路径          类型              大小",
            bg=LIST_HEADER_BG,
            fg=LIST_HEADER_FG,
            font=ui_font(10, bold=True),
            anchor=tk.W,
            padx=8,
            pady=5,
        )
        header.pack(fill=tk.X)
        body = tk.Frame(box, bg=LIST_BG, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill=tk.BOTH, expand=True)
        sy = ttk.Scrollbar(body, orient=tk.VERTICAL, style="Thin.Vertical.TScrollbar")
        self._list = make_listbox(body)
        sy.configure(command=self._list.yview)
        self._list.configure(yscrollcommand=sy.set)
        self._list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        bind_listbox_scroll(self._list)
        self._list.bind("<<ListboxSelect>>", self._on_list_select)
        self._list.bind("<Double-1>", lambda _e: self._preview_selected())
        self._list.bind("<Return>", lambda _e: self._preview_selected())

    @staticmethod
    def _row_label(ent: ResourceEntry) -> str:
        return f"{ent.rel_name}    {ent.type_label}    {format_size(ent.size)}"

    def _build_thumb_view(self, parent: ttk.Frame) -> None:
        self._thumb_scroll = VerticalScrollArea(
            parent, bg=BG_PANEL, body_style="Panel.TFrame", padding=(4, 4)
        )
        self._thumb_scroll.pack(fill=tk.BOTH, expand=True)
        self._thumb_inner = ttk.Frame(self._thumb_scroll.body)
        self._thumb_inner.pack(fill=tk.X, anchor=tk.NW)
        canvas = self._thumb_scroll.canvas
        canvas.configure(yscrollcommand=self._thumb_yscroll)
        bind_listbox_scroll(canvas)

    def _thumb_yscroll(self, first: str, last: str) -> None:
        self._thumb_scroll._on_yview(first, last)
        self.after_idle(self._thumb_sync_viewport)

    def _build_preview_pane(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="预览", style="Subtitle.TLabel").pack(anchor=tk.W)
        self._preview_image = tk.Label(
            parent,
            text="选择文件后点「预览」或双击",
            anchor=tk.CENTER,
            bg=BG_CARD,
            fg=FG_SECONDARY,
            padx=8,
            pady=24,
        )
        self._preview_image.pack(fill=tk.X, pady=6)
        text_box = ttk.Frame(parent)
        text_box.pack(fill=tk.BOTH, expand=True)
        self._preview_text = tk.Text(
            text_box,
            height=12,
            wrap=tk.WORD,
            bg=BG_CARD,
            fg=FG,
            insertbackground=FG,
            relief=tk.FLAT,
            padx=8,
            pady=8,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        sy = ttk.Scrollbar(text_box, orient=tk.VERTICAL, command=self._preview_text.yview)
        self._preview_text.configure(yscrollcommand=sy.set, state=tk.DISABLED)
        self._preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        bind_text_scroll(self._preview_text, horizontal=False)

    def _bind_keys(self, widget: tk.Misc) -> None:
        widget.bind("<F5>", self._on_f5)
        widget.bind("<Return>", lambda _e: self._preview_selected())

    def _debounced_refresh(self, _event: tk.Event | None = None) -> None:
        if self._search_after:
            self.after_cancel(self._search_after)
        self._search_after = self.after(280, self._refresh)

    def _on_f5(self, event: tk.Event) -> str | None:
        if self._app and self._app._current_key != "browser":
            return None
        self._refresh()
        return "break"

    def _browse_root(self) -> None:
        path = filedialog.askdirectory(title="选择浏览根目录")
        if path:
            self._root_row.set(path)
            self._save_last_root(path)
            self._refresh()

    def _load_last_root(self) -> None:
        try:
            if _STATE_FILE.is_file():
                data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
                root = data.get("browser_root", "")
                if root and Path(root).is_dir():
                    self._root_row.set(root)
                    self._status.configure(text="已记住上次目录，打开本页后将自动加载")
        except (OSError, json.JSONDecodeError):
            pass

    def _save_last_root(self, path: str) -> None:
        try:
            data = {}
            if _STATE_FILE.is_file():
                data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            data["browser_root"] = path
            _STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _on_category_change(self) -> None:
        cat = self._category.get()
        if cat != CATEGORY_IMAGE and self._view_mode.get() == "thumb":
            self._view_mode.set("list")
        self._switch_view()
        if self._category_after:
            self.after_cancel(self._category_after)
        self._category_after = self.after(280, self._refresh)

    def _switch_view(self) -> None:
        if self._view_mode.get() == "thumb" and self._category.get() in (CATEGORY_ALL, CATEGORY_IMAGE):
            self._list_frame.pack_forget()
            self._thumb_frame.pack(fill=tk.BOTH, expand=True)
            if self._entries:
                self._prepare_thumb_indices()
            self._thumb_last_first_row = -1
            self.after_idle(self._thumb_sync_viewport)
        else:
            self._thumb_frame.pack_forget()
            self._list_frame.pack(fill=tk.BOTH, expand=True)
            self._thumb_scroll.set_fixed_scroll_height(None)

    def _refresh(self) -> None:
        root = self._root_row.get().strip()
        if not root:
            self._status.configure(text="请选择根目录")
            return
        root_path = Path(root)
        if not root_path.is_dir():
            self._status.configure(text="根目录不存在")
            return
        self._save_last_root(root)
        self._scan_id += 1
        scan_id = self._scan_id
        self._thumb_gen += 1
        self._scan_running = True
        self._thumb_loading.clear()
        self._thumb_photos.clear()
        self._entries.clear()
        self._selected = None
        for child in self._thumb_inner.winfo_children():
            child.destroy()
        self._thumb_image_indices.clear()
        self._thumb_last_first_row = -1
        self._thumb_scroll.set_fixed_scroll_height(None)
        self._list.delete(0, tk.END)
        self._status.configure(text="扫描中…（仅加载文件名）")

        cat = self._category.get() or CATEGORY_ALL
        query = self._search_var.get()
        recursive = self._recursive.get()
        self._start_scan_worker(scan_id, root_path, cat, query, recursive)

    def _start_scan_worker(
        self,
        scan_id: int,
        root_path: Path,
        cat: str,
        query: str,
        recursive: bool,
    ) -> None:
        if scan_id != self._scan_id:
            return

        def work() -> None:
            batch: list[ResourceEntry] = []
            total = 0
            try:
                for ent in iter_directory_entries(
                    root_path, recursive=recursive, category=cat, query=query
                ):
                    if scan_id != self._scan_id:
                        return
                    batch.append(ent)
                    total += 1
                    if len(batch) >= _SCAN_BATCH:
                        chunk = batch
                        batch = []
                        n = total
                        self.after(
                            0, lambda c=chunk, n=n, sid=scan_id: self._append_scan_batch(c, n, sid)
                        )
                if scan_id != self._scan_id:
                    return
                tail = batch
                self.after(0, lambda sid=scan_id, t=tail: self._finish_scan(t, sid))
            except Exception as exc:
                self.after(0, lambda sid=scan_id, err=exc: self._scan_failed(sid, err))

        threading.Thread(target=work, daemon=True).start()

    def _scan_failed(self, scan_id: int, exc: Exception) -> None:
        if scan_id != self._scan_id:
            return
        self._scan_running = False
        self._status.configure(text=f"扫描失败：{exc}")

    def _append_scan_batch(self, batch: list[ResourceEntry], total: int, scan_id: int) -> None:
        if scan_id != self._scan_id:
            return
        self._entries.extend(batch)
        self._status.configure(text=f"扫描中… 已发现 {total} 个文件（完成后显示列表）")

    def _finish_scan(self, tail: list[ResourceEntry], scan_id: int) -> None:
        if scan_id != self._scan_id:
            return
        if tail:
            self._append_scan_batch(tail, len(self._entries) + len(tail), scan_id)
        self._entries.sort(key=lambda e: (e.category, e.rel_name.lower()))
        self._populate_list(scan_id)

    def _populate_list(self, scan_id: int) -> None:
        if scan_id != self._scan_id:
            return
        self._list.delete(0, tk.END)
        if len(self._entries) <= _TREE_FAST_LIMIT:
            labels = [self._row_label(e) for e in self._entries]
            if labels:
                self._list.insert(tk.END, *labels)
            self._finish_list_populate(scan_id)
            return
        self._status.configure(text=f"正在显示 {len(self._entries)} 个文件…")
        self._populate_list_chunked(scan_id, 0)

    def _populate_list_chunked(self, scan_id: int, start: int) -> None:
        if scan_id != self._scan_id:
            return
        end = min(start + _TREE_UI_CHUNK, len(self._entries))
        labels = [self._row_label(self._entries[i]) for i in range(start, end)]
        if labels:
            self._list.insert(tk.END, *labels)
        if end < len(self._entries):
            self.after(2, lambda: self._populate_list_chunked(scan_id, end))
            return
        self._finish_list_populate(scan_id)

    def _finish_list_populate(self, scan_id: int) -> None:
        if scan_id != self._scan_id:
            return
        self._scan_running = False
        capped = len(self._entries) >= 8000
        msg = f"共 {len(self._entries)} 个文件（大小在选中后显示）"
        if capped:
            msg += "；已达上限，请用搜索或分类缩小范围"
        self._status.configure(text=msg)
        if self._view_mode.get() == "thumb" and self._category.get() in (
            CATEGORY_ALL,
            CATEGORY_IMAGE,
        ):
            self._prepare_thumb_indices()
            self._thumb_last_first_row = -1
            self.after_idle(self._thumb_sync_viewport)

    def _prepare_thumb_indices(self) -> None:
        self._thumb_image_indices = [
            i for i, e in enumerate(self._entries) if self._preview_svc.can_thumbnail(e)
        ]
        n = len(self._thumb_image_indices)
        self._thumb_total_rows = (n + _THUMB_COLS - 1) // _THUMB_COLS if n else 0

    def _thumb_sync_viewport(self) -> None:
        if self._view_mode.get() != "thumb":
            return
        if not self._thumb_image_indices:
            for child in self._thumb_inner.winfo_children():
                child.destroy()
            self._thumb_scroll.set_fixed_scroll_height(None)
            if not self._entries:
                return
            ttk.Label(
                self._thumb_inner,
                text="当前筛选下没有可缩略图的图片文件。",
                style="Panel.TLabel",
            ).pack(padx=8, pady=8)
            self._thumb_scroll._bind_wheel_tree(self._thumb_inner)
            return

        canvas = self._thumb_scroll.canvas
        canvas.update_idletasks()
        total_h = self._thumb_total_rows * _THUMB_ROW_HEIGHT
        self._thumb_scroll.set_fixed_scroll_height(total_h)

        top = canvas.canvasy(0)
        view_h = max(canvas.winfo_height(), _THUMB_ROW_HEIGHT)
        first_row = max(0, int(top // _THUMB_ROW_HEIGHT))
        rows_visible = max(2, int(view_h // _THUMB_ROW_HEIGHT) + 2)
        last_row = min(self._thumb_total_rows - 1, first_row + rows_visible)

        if first_row == self._thumb_last_first_row and self._thumb_inner.winfo_children():
            return
        self._thumb_last_first_row = first_row

        for child in self._thumb_inner.winfo_children():
            child.destroy()

        if first_row > 0:
            top_sp = tk.Frame(self._thumb_inner, height=first_row * _THUMB_ROW_HEIGHT, bg=BG_PANEL)
            top_sp.pack(fill=tk.X)
            top_sp.pack_propagate(False)

        for row in range(first_row, last_row + 1):
            row_fr = tk.Frame(self._thumb_inner, bg=BG_PANEL)
            row_fr.pack(fill=tk.X)
            for col in range(_THUMB_COLS):
                thumb_idx = row * _THUMB_COLS + col
                if thumb_idx >= len(self._thumb_image_indices):
                    break
                ent_idx = self._thumb_image_indices[thumb_idx]
                ent = self._entries[ent_idx]
                cell = tk.Frame(row_fr, bg=BG_CARD, padx=4, pady=4)
                cell.grid(row=0, column=col, padx=4, pady=4, sticky="n")
                if ent_idx in self._thumb_photos:
                    img_lbl = tk.Label(cell, image=self._thumb_photos[ent_idx], bg=BG_CARD)
                else:
                    img_lbl = tk.Label(
                        cell, text="加载中…", width=12, anchor=tk.CENTER, bg=BG_CARD, fg=FG_SECONDARY
                    )
                    self._queue_thumb_load(ent_idx, img_lbl)
                img_lbl.pack()
                cap = tk.Label(
                    cell,
                    text=ent.name if len(ent.name) <= 16 else ent.name[:14] + "…",
                    bg=BG_CARD,
                    fg=FG,
                    anchor=tk.CENTER,
                    font=ui_font(9),
                )
                cap.pack()
                for w in (cell, img_lbl, cap):
                    w.bind("<Button-1>", lambda _e, i=ent_idx: self._select_index(i))
                    w.bind("<Double-1>", lambda _e: self._preview_selected())

        bottom_rows = self._thumb_total_rows - last_row - 1
        if bottom_rows > 0:
            bot_sp = tk.Frame(self._thumb_inner, height=bottom_rows * _THUMB_ROW_HEIGHT, bg=BG_PANEL)
            bot_sp.pack(fill=tk.X)
            bot_sp.pack_propagate(False)

        self._thumb_scroll._bind_wheel_tree(self._thumb_inner)

    def _queue_thumb_load(self, ent_idx: int, label: tk.Label) -> None:
        if ent_idx in self._thumb_photos:
            photo = self._thumb_photos[ent_idx]
            if label.winfo_exists():
                label.configure(image=photo, text="", bg=BG_CARD)
            return
        if ent_idx in self._thumb_loading:
            return
        self._thumb_loading.add(ent_idx)
        gen = self._thumb_gen

        def work() -> None:
            try:
                with self._thumb_load_sem:
                    if gen != self._thumb_gen:
                        return
                    if ent_idx >= len(self._entries):
                        return
                    ent = self._entries[ent_idx]
                    img = self._preview_svc.load_thumbnail(ent.path, size=96)
                self.after(0, lambda: self._apply_thumb(gen, ent_idx, label, img))
            finally:
                self.after(0, lambda: self._thumb_loading.discard(ent_idx))

        threading.Thread(target=work, daemon=True).start()

    def _apply_thumb(self, gen: int, ent_idx: int, label: tk.Label, img: Any) -> None:
        if gen != self._thumb_gen:
            return
        if img is None:
            if label.winfo_exists():
                label.configure(text="无预览", fg=FG_SECONDARY)
            return
        try:
            from PIL import ImageTk

            photo = ImageTk.PhotoImage(img)
            self._thumb_photos[ent_idx] = photo
            if len(self._thumb_photos) > _THUMB_CACHE_MAX:
                drop = next(iter(self._thumb_photos))
                if drop != ent_idx:
                    self._thumb_photos.pop(drop, None)
            if label.winfo_exists():
                label.configure(image=photo, text="", bg=BG_CARD)
        except Exception:
            if label.winfo_exists():
                label.configure(text="无预览", fg=FG_SECONDARY)

    def _on_list_select(self, _event: tk.Event | None = None) -> None:
        sel = self._list.curselection()
        if not sel:
            return
        self._select_index(int(sel[0]), preview=False)

    def _select_index(self, index: int, *, preview: bool = False) -> None:
        if index < 0 or index >= len(self._entries):
            return
        self._selected = self._entries[index]
        self._list.selection_clear(0, tk.END)
        self._list.selection_set(index)
        self._list.activate(index)
        self._list.see(index)
        self._show_entry_info(self._selected)
        if preview:
            self._preview_selected()

    def _current_entry(self) -> ResourceEntry | None:
        if self._selected:
            return self._selected
        sel = self._list.curselection()
        if sel:
            try:
                return self._entries[int(sel[0])]
            except (ValueError, IndexError):
                pass
        return None

    def _show_entry_info(self, ent: ResourceEntry) -> None:
        if not ent.size_known:
            hydrated = hydrate_size(ent)
            for i, e in enumerate(self._entries):
                if e.path == hydrated.path:
                    self._entries[i] = hydrated
                    ent = hydrated
                    break
        self._preview_image.configure(image="", text="")
        self._preview_photo = None
        self._preview_image.configure(
            text="选择文件后点「预览」或双击",
            bg=BG_CARD,
            fg=FG_SECONDARY,
        )
        self._set_preview_text(self._preview_svc.info_text(ent))

    def _preview_selected(self) -> None:
        ent = self._current_entry()
        if ent is None:
            return
        self._selected = ent
        self._preview_token += 1
        token = self._preview_token
        self._show_entry_info(ent)
        self._status.configure(text="加载预览…")

        def work() -> None:
            image_result: tuple[Any, str] | None = None
            text_extra = ""
            try:
                if self._preview_svc.can_preview_image(ent):
                    image_result = self._preview_svc.load_preview_image(ent.path)
                elif self._preview_svc.can_text_preview(ent):
                    text_extra = "\n\n" + self._preview_svc.text_snippet(ent.path)
            except Exception as exc:
                image_result = (None, str(exc))
            self.after(0, lambda: self._apply_preview(token, ent, image_result, text_extra))

        threading.Thread(target=work, daemon=True).start()

    def _apply_preview(
        self,
        token: int,
        ent: ResourceEntry,
        image_result: tuple[Any, str] | None,
        text_extra: str,
    ) -> None:
        if token != self._preview_token or self._selected != ent:
            return
        if text_extra:
            self._append_preview_text(text_extra)
        if image_result is not None:
            img, err = image_result
            if img is not None:
                try:
                    from PIL import ImageTk

                    self._preview_photo = ImageTk.PhotoImage(img)
                    self._preview_image.configure(image=self._preview_photo, text="", bg=BG_CARD)
                except Exception as exc:
                    self._append_preview_text(f"\n\n图片预览失败：{exc}")
            elif err:
                self._append_preview_text(f"\n\n{err}")
        self._status.configure(text=f"已选：{ent.name}")

    def _set_preview_text(self, text: str) -> None:
        self._preview_text.configure(state=tk.NORMAL)
        self._preview_text.delete("1.0", tk.END)
        self._preview_text.insert(tk.END, text)
        self._preview_text.configure(state=tk.DISABLED)

    def _append_preview_text(self, text: str) -> None:
        self._preview_text.configure(state=tk.NORMAL)
        self._preview_text.insert(tk.END, text)
        self._preview_text.configure(state=tk.DISABLED)

    def _play_or_open(self) -> None:
        ent = self._current_entry()
        if ent is None:
            return
        if self._preview_svc.can_play_audio(ent):
            err = self._preview_svc.play_audio(ent.path)
            if err:
                messagebox.showerror("播放", err)
            return
        if self._preview_svc.can_open_video(ent):
            err = self._preview_svc.open_video(ent.path)
            if err:
                messagebox.showerror("打开视频", err)
            return
        messagebox.showinfo("预览", "当前文件类型请使用「预览」或「跳转功能」。")

    def _stop_audio(self) -> None:
        self._preview_svc.stop_audio()

    def _open_parent(self) -> None:
        ent = self._current_entry()
        if ent is None:
            return
        folder = ent.path.parent
        if sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        else:
            if sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)

    def _jump_panel(self) -> None:
        ent = self._current_entry()
        if ent is None:
            return
        key = panel_for_entry(ent)
        if not key or self._app is None:
            messagebox.showinfo("跳转", "未找到匹配的功能面板。")
            return
        self._app.jump_to_panel(key, input_path=str(ent.path))

    def _build_command(self) -> tuple[list[str], None] | str:
        return "资源浏览为交互式面板，请使用面板内按钮操作。"
