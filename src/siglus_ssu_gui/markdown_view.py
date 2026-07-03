"""将 Markdown 教程渲染到 tk.Text（标题、列表、表格、代码块等）。"""

from __future__ import annotations

import re
import tkinter as tk

from .theme import (
    ACCENT,
    BG_CARD,
    BG_ELEVATED,
    BG_INPUT,
    BG_PANEL,
    BORDER,
    FG,
    FG_MUTED,
    FG_SECONDARY,
    mono_font,
    ui_font,
)

_TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|$")
_INLINE_RE = re.compile(
    r"\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)"
)


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def _parse_table_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _configure_tags(text: tk.Text) -> None:
    text.tag_configure(
        "md_h1",
        font=ui_font(17, bold=True),
        foreground=ACCENT,
        spacing1=14,
        spacing3=10,
    )
    text.tag_configure(
        "md_h2",
        font=ui_font(14, bold=True),
        foreground=ACCENT,
        spacing1=12,
        spacing3=8,
    )
    text.tag_configure(
        "md_h3",
        font=ui_font(12, bold=True),
        foreground=FG,
        spacing1=10,
        spacing3=6,
    )
    text.tag_configure("md_bold", font=ui_font(11, bold=True))
    text.tag_configure(
        "md_code",
        font=mono_font(10),
        background=BG_ELEVATED,
        foreground="#e8c27a",
    )
    text.tag_configure(
        "md_codeblock",
        font=mono_font(10),
        background=BG_INPUT,
        foreground=FG_SECONDARY,
        lmargin1=18,
        lmargin2=18,
        spacing1=2,
        spacing3=2,
    )
    text.tag_configure("md_list", lmargin1=22, lmargin2=34, spacing1=2)
    text.tag_configure(
        "md_table_head",
        font=ui_font(11, bold=True),
        background=BG_CARD,
        foreground=ACCENT,
        spacing1=4,
    )
    text.tag_configure(
        "md_table_row",
        font=mono_font(10),
        background=BG_PANEL,
        spacing1=1,
    )
    text.tag_configure("md_hr", foreground=BORDER, justify=tk.CENTER, spacing1=8, spacing3=8)
    text.tag_configure("md_link", foreground=ACCENT, underline=True)
    text.tag_configure("md_quote", foreground=FG_MUTED, lmargin1=18, lmargin2=18)


def _insert_inline(text: tk.Text, line: str, base_tags: tuple[str, ...] = ()) -> None:
    pos = 0
    for match in _INLINE_RE.finditer(line):
        if match.start() > pos:
            text.insert(tk.END, line[pos : match.start()], base_tags)
        if match.group(1) is not None:
            text.insert(tk.END, match.group(1), (*base_tags, "md_bold"))
        elif match.group(2) is not None:
            text.insert(tk.END, match.group(2), (*base_tags, "md_code"))
        elif match.group(3) is not None:
            label, url = match.group(3), match.group(4)
            text.insert(tk.END, label, (*base_tags, "md_link"))
            text.insert(tk.END, f" ({url})", base_tags)
        pos = match.end()
    if pos < len(line):
        text.insert(tk.END, line[pos:], base_tags)


def _insert_table(text: tk.Text, rows: list[list[str]], *, header: bool) -> None:
    if not rows:
        return
    col_count = max(len(r) for r in rows)
    widths = [0] * col_count
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    for ri, row in enumerate(rows):
        padded = []
        for i in range(col_count):
            cell = row[i] if i < len(row) else ""
            padded.append(cell.ljust(widths[i]))
        line = " │ ".join(padded)
        tag = "md_table_head" if header and ri == 0 else "md_table_row"
        text.insert(tk.END, line + "\n", (tag,))


def render_markdown_to_text(text: tk.Text, content: str) -> None:
    text.configure(state=tk.NORMAL)
    text.delete("1.0", tk.END)
    _configure_tags(text)

    lines = content.splitlines()
    i = 0
    in_code = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            if in_code:
                text.insert(tk.END, "\n")
            i += 1
            continue

        if in_code:
            text.insert(tk.END, line + "\n", ("md_codeblock",))
            i += 1
            continue

        if _is_table_row(line):
            table_lines: list[str] = []
            while i < len(lines) and _is_table_row(lines[i]):
                table_lines.append(lines[i])
                i += 1
            parsed = [_parse_table_cells(row) for row in table_lines]
            if len(parsed) >= 2 and _TABLE_SEP_RE.match(table_lines[1].strip()):
                _insert_table(text, [parsed[0]], header=True)
                _insert_table(text, parsed[2:], header=False)
            else:
                _insert_table(text, parsed, header=True)
            text.insert(tk.END, "\n")
            continue

        if stripped in ("---", "***", "___"):
            text.insert(tk.END, "─" * 42 + "\n", ("md_hr",))
            i += 1
            continue

        if stripped.startswith("# "):
            text.insert(tk.END, stripped[2:] + "\n", ("md_h1",))
            i += 1
            continue
        if stripped.startswith("## "):
            text.insert(tk.END, stripped[3:] + "\n", ("md_h2",))
            i += 1
            continue
        if stripped.startswith("### "):
            text.insert(tk.END, stripped[4:] + "\n", ("md_h3",))
            i += 1
            continue

        if stripped.startswith("> "):
            text.insert(tk.END, stripped[2:] + "\n", ("md_quote",))
            i += 1
            continue

        list_match = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if list_match:
            indent, body = list_match.group(1), list_match.group(2)
            bullet = "• " if len(indent) < 2 else "◦ "
            text.insert(tk.END, bullet, ("md_list",))
            _insert_inline(text, body, ("md_list",))
            text.insert(tk.END, "\n")
            i += 1
            continue

        num_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if num_match:
            text.insert(tk.END, f"{num_match.group(1)}. ", ("md_list",))
            _insert_inline(text, num_match.group(2), ("md_list",))
            text.insert(tk.END, "\n")
            i += 1
            continue

        if not stripped:
            text.insert(tk.END, "\n")
            i += 1
            continue

        _insert_inline(text, line)
        text.insert(tk.END, "\n")
        i += 1

    text.configure(state=tk.DISABLED)
    text.see("1.0")
