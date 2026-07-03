"""细滚动条 + 滚轮：表单区、导航、日志等可滚动区域。"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk


def _wheel_delta(event: tk.Event) -> int:
    if sys.platform == "darwin":
        return int(event.delta)
    if hasattr(event, "delta") and event.delta:
        return int(-event.delta / 120)
    return 0


class VerticalScrollArea(ttk.Frame):
    """Canvas 垂直滚动容器：细滚动条、滚轮、内容不足时自动隐藏滚动条。"""

    def __init__(
        self,
        master: tk.Misc,
        *,
        bg: str,
        body_style: str = "SectionBody.TFrame",
        padding: tuple[int, int] = (4, 6),
    ) -> None:
        super().__init__(master)
        self._bg = bg
        self._canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg=bg)
        self._scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style="Thin.Vertical.TScrollbar", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._on_yview)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.body = ttk.Frame(self._canvas, padding=padding, style=body_style)
        self._window = self._canvas.create_window((0, 0), window=self.body, anchor=tk.NW)

        self.body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._bind_wheel_tree(self._canvas)
        self._bind_wheel_tree(self.body)
        self.after_idle(self._sync_scrollregion)

    @property
    def canvas(self) -> tk.Canvas:
        return self._canvas

    def _on_yview(self, first: str, last: str) -> None:
        self._scrollbar.set(first, last)
        needs = float(first) > 0.0 or float(last) < 1.0
        if needs:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        elif self._scrollbar.winfo_ismapped():
            self._scrollbar.pack_forget()

    def _sync_scrollregion(self) -> None:
        self.body.update_idletasks()
        width = max(self.body.winfo_reqwidth(), self._canvas.winfo_width())
        height = self.body.winfo_reqheight()
        if height > 0:
            self._canvas.configure(scrollregion=(0, 0, width, height))

    def refresh_bindings(self, root: tk.Misc | None = None) -> None:
        """给子控件（含侧栏导航按钮）补上滚轮绑定。"""
        target = root or self.body
        self._bind_wheel_tree(target)
        for child in target.winfo_children():
            self.refresh_bindings(child)
        self.after_idle(self._sync_scrollregion)

    def _on_body_configure(self, _event: tk.Event) -> None:
        self._sync_scrollregion()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # 只同步宽度；高度由内容决定，否则无法滚动
        self._canvas.itemconfigure(self._window, width=event.width)
        self._sync_scrollregion()

    def _bind_wheel_tree(self, widget: tk.Misc) -> None:
        widget.bind("<MouseWheel>", self._on_wheel, add="+")
        widget.bind("<Button-4>", self._on_wheel_up, add="+")
        widget.bind("<Button-5>", self._on_wheel_down, add="+")

    def _on_wheel(self, event: tk.Event) -> str:
        step = _wheel_delta(event)
        if step:
            self._canvas.yview_scroll(step, "units")
        return "break"

    def _on_wheel_up(self, _event: tk.Event) -> str:
        self._canvas.yview_scroll(-1, "units")
        return "break"

    def _on_wheel_down(self, _event: tk.Event) -> str:
        self._canvas.yview_scroll(1, "units")
        return "break"

    def scroll_to_top(self) -> None:
        self._canvas.yview_moveto(0)


def bind_text_scroll(text: tk.Text, *, horizontal: bool = True) -> None:
    """为 Text / 日志区绑定滚轮。"""

    def _wheel(event: tk.Event) -> str:
        step = _wheel_delta(event)
        if step:
            text.yview_scroll(step, "units")
        return "break"

    def _up(_event: tk.Event) -> str:
        text.yview_scroll(-1, "units")
        return "break"

    def _down(_event: tk.Event) -> str:
        text.yview_scroll(1, "units")
        return "break"

    for seq, handler in (
        ("<MouseWheel>", _wheel),
        ("<Button-4>", _up),
        ("<Button-5>", _down),
    ):
        text.bind(seq, handler, add="+")

    if horizontal:

        def _shift_wheel(event: tk.Event) -> str | None:
            if not (event.state & 0x1):
                return None
            step = _wheel_delta(event)
            if step:
                text.xview_scroll(step, "units")
            return "break"

        text.bind("<MouseWheel>", _shift_wheel, add="+")


def bind_listbox_scroll(listbox: tk.Listbox) -> None:
    def _wheel(event: tk.Event) -> str:
        step = _wheel_delta(event)
        if step:
            listbox.yview_scroll(step, "units")
        return "break"

    listbox.bind("<MouseWheel>", _wheel, add="+")
    listbox.bind("<Button-4>", lambda _e: listbox.yview_scroll(-1, "units"), add="+")
    listbox.bind("<Button-5>", lambda _e: listbox.yview_scroll(1, "units"), add="+")
