from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import ttk

from ..widgets import (
    AngouRow,
    AUDIO_FILETYPES,
    CollapsibleSection,
    DBS_FILETYPES,
    DAT_FILETYPES,
    FileListRow,
    G00_FILETYPES,
    IMAGE_FILETYPES,
    PCK_FILETYPES,
    PathRow,
    Section,
    TextRow,
    VIDEO_FILETYPES,
    labeled_check,
    labeled_combo,
    labeled_radio,
)
from .base import BasePanel


class ExtractPanel(BasePanel):
    TITLE = "提取"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_radio(
            parent,
            "操作类型",
            [
                ("pck", "提取 .pck"),
                ("disam", "反汇编 .dat（目录或 .pck）"),
                ("gei", "还原 Gameexe.ini"),
            ],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.input_row = PathRow(
            paths.body,
            "输入",
            mode="file",
            filetypes=PCK_FILETYPES,
            hint="选择要提取的 .pck 文件",
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            paths.body, "输出目录", mode="dir", hint="留空则输出到输入文件旁边"
        )
        self.output_row.pack(fill=tk.X, pady=4)
        opts = Section(parent, "选项")
        opts.pack(fill=tk.X, pady=4)
        self.disam = labeled_check(opts.body, "同时反汇编并反编译（--disam）")
        self.angou = AngouRow(opts.body)
        self.angou.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op == "pck":
            self.disam.pack(anchor=tk.W, pady=1)
            self.input_row.set_mode("file", filetypes=PCK_FILETYPES)
            self.input_row.set_hint("选择要提取的 .pck 文件")
        elif op == "disam":
            self.disam.pack_forget()
            self.input_row.set_mode("file_or_dir", filetypes=PCK_FILETYPES)
            self.input_row.set_hint("含 .dat 的文件夹，或原始 .pck 文件")
        else:
            self.disam.pack_forget()
            self.input_row.set_mode("file_or_dir", filetypes=DAT_FILETYPES)
            self.input_row.set_hint("Gameexe.dat 或其所在目录")

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        op = self.op.get()
        inp = self.input_row.get()
        if err := self.input_row.validate_exists(required=True):
            return err
        argv = ["-x"]
        if op == "gei":
            argv.append("--gei")
        elif op == "disam":
            argv.append("--disam")
        elif self.disam.get():
            argv.append("--disam")
        argv.append(inp)
        out = self.output_row.get()
        if out:
            argv.append(out)
            self._output_hint = Path(out)
        else:
            self._output_hint = self._hint_from_path(inp)
        self.angou.append_argv(argv)
        return argv, self._output_hint


class CompilePanel(BasePanel):
    TITLE = "编译"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_radio(
            parent,
            "操作类型",
            [("std", "标准编译（.ss → .pck）"), ("gei", "仅编译 Gameexe.dat")],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.input_row = PathRow(
            paths.body,
            "输入目录",
            mode="dir",
            hint="包含 .ss 源码与 Gameexe.ini（如有）的工作目录",
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            paths.body,
            "输出",
            mode="save_or_dir",
            filetypes=PCK_FILETYPES,
            hint="填写 .pck 路径，或选择已存在目录（将生成 Scene.pck）",
        )
        self.output_row.pack(fill=tk.X, pady=4)
        opts = Section(parent, "常用选项")
        opts.pack(fill=tk.X, pady=4)
        self.charset = labeled_combo(opts.body, "源文件编码", ["自动", "UTF-8", "Shift-JIS"])
        self.debug = labeled_check(opts.body, "保留临时文件（--debug）")
        self.serial = labeled_check(opts.body, "串行编译（--serial）")
        adv = CollapsibleSection(parent, "高级选项", start_open=False)
        adv.pack(fill=tk.X, pady=4)
        self.dat_repack = labeled_check(adv.body, "仅重打包已有 .dat（--dat-repack）")
        self.no_angou = labeled_check(adv.body, "禁用加密（--no-angou）")
        self.no_lzss = labeled_check(adv.body, "禁用 LZSS（--no-lzss）")
        self.tmp_row = PathRow(adv.body, "增量缓存目录", mode="dir", hint="填写则启用 --tmp（与 --debug 互斥）")
        self.tmp_row.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        if self.op.get() == "gei":
            self.output_row.set_mode("dir")
            self.output_row.set_hint("输出目录（将写入 Gameexe.dat）")
        else:
            self.output_row.set_mode("save_or_dir", filetypes=PCK_FILETYPES)
            self.output_row.set_hint("填写 .pck 路径，或选择已存在目录（将生成 Scene.pck）")

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True, as_dir=True):
            return err
        out = self.output_row.get()
        if not out:
            return "请指定输出路径"
        argv = ["-c"]
        if self.op.get() == "gei":
            argv.append("--gei")
        if self.debug.get() and self.tmp_row.get():
            return "不能同时使用 --debug 与 --tmp"
        if self.debug.get():
            argv.append("--debug")
        cs = self.charset.get()
        if cs == "UTF-8":
            argv.extend(["--charset", "utf8"])
        elif cs == "Shift-JIS":
            argv.extend(["--charset", "cp932"])
        if self.serial.get():
            argv.append("--serial")
        if self.dat_repack.get():
            argv.append("--dat-repack")
        if self.no_angou.get():
            argv.append("--no-angou")
        if self.no_lzss.get():
            argv.append("--no-lzss")
        tmp = self.tmp_row.get()
        if tmp:
            if err := self.tmp_row.validate_exists(required=True, as_dir=True):
                return err
            argv.extend(["--tmp", tmp])
        argv.append(self.input_row.get())
        argv.append(out)
        self._output_hint = self._hint_from_path(out, as_dir=True)
        return argv, self._output_hint


class AnalyzePanel(BasePanel):
    TITLE = "分析"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent,
            "操作类型",
            ["分析单个文件", "比较两个文件", "台词统计导出 CSV", "分析 Gameexe.dat"],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.in1 = PathRow(
            paths.body, "输入文件 1", mode="file", filetypes=PCK_FILETYPES
        )
        self.in1.pack(fill=tk.X, pady=4)
        self.in2 = PathRow(
            paths.body, "输入文件 2", mode="file", filetypes=PCK_FILETYPES
        )
        self.in2.pack(fill=tk.X, pady=4)
        self.csv_out = PathRow(
            paths.body,
            "输出 CSV",
            mode="save",
            filetypes=[("CSV", "*.csv"), ("所有文件", "*.*")],
        )
        self.csv_out.pack(fill=tk.X, pady=4)
        opts = Section(parent, "选项")
        opts.pack(fill=tk.X, pady=4)
        self.disam = labeled_check(opts.body, "写出反汇编（--disam）")
        self.payload = labeled_check(opts.body, "语义级比较（--payload，较慢）")
        self.angou = AngouRow(opts.body)
        self.angou.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op == "比较两个文件":
            self.in2.pack(fill=tk.X, pady=4)
            self.payload.widget.pack(anchor=tk.W, pady=2)
            self.disam.widget.pack(anchor=tk.W, pady=2)
            self.csv_out.pack_forget()
        elif op == "台词统计导出 CSV":
            self.in2.pack_forget()
            self.payload.pack_forget()
            self.disam.pack_forget()
            self.csv_out.pack(fill=tk.X, pady=4)
        else:
            self.in2.pack_forget()
            self.csv_out.pack_forget()
            self.payload.pack_forget()
            if op == "分析单个文件":
                self.disam.widget.pack(anchor=tk.W, pady=2)
            else:
                self.disam.pack_forget()

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        op = self.op.get()
        argv = ["-a"]
        if op == "分析 Gameexe.dat":
            argv.append("--gei")
            if err := self.in1.validate_exists(required=True, as_dir=False):
                return err
            argv.append(self.in1.get())
            self._output_hint = self._hint_from_path(self.in1.get())
            self.angou.append_argv(argv)
            return argv, self._output_hint
        if op == "台词统计导出 CSV":
            argv.append("--word")
            if err := self.in1.validate_exists(required=True, as_dir=False):
                return err
            argv.append(self.in1.get())
            csv = self.csv_out.get()
            if csv:
                argv.append(csv)
                self._output_hint = self._hint_from_path(csv)
            else:
                self._output_hint = self._hint_from_path(self.in1.get())
            self.angou.append_argv(argv)
            return argv, self._output_hint
        if op == "比较两个文件":
            if err := self.in1.validate_exists(required=True, as_dir=False):
                return err
            if err := self.in2.validate_exists(required=True, as_dir=False):
                return err
            if self.payload.get():
                argv.append("--payload")
            if self.disam.get():
                argv.append("--disam")
            argv.extend([self.in1.get(), self.in2.get()])
            self._output_hint = self._hint_from_path(self.in1.get())
            self.angou.append_argv(argv)
            return argv, self._output_hint
        if err := self.in1.validate_exists(required=True, as_dir=False):
            return err
        if self.disam.get():
            argv.append("--disam")
        argv.append(self.in1.get())
        self._output_hint = self._hint_from_path(self.in1.get())
        self.angou.append_argv(argv)
        return argv, self._output_hint


class G00Panel(BasePanel):
    TITLE = "图片 g00"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent,
            "操作",
            ["分析 --a", "提取 --x", "合并 --m", "创建 --c"],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.input_row = PathRow(
            paths.body,
            "输入",
            mode="file",
            filetypes=G00_FILETYPES,
            hint="选择单个 .g00 文件",
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.merge_list = FileListRow(
            paths.body, "合并文件列表（--m）", filetypes=G00_FILETYPES
        )
        self.merge_list.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            paths.body,
            "输出目录",
            mode="dir",
            hint="提取出的 PNG/JPEG 将写入此文件夹",
        )
        self.output_row.pack(fill=tk.X, pady=4)
        opts = Section(parent, "选项")
        opts.pack(fill=tk.X, pady=4)
        self.trim = labeled_check(opts.body, "裁剪透明边（--trim）")
        self.type_row = TextRow(opts.body, "g00 类型", hint="创建模式：--type N")
        self.type_row.pack(fill=tk.X, pady=4)
        self.refer_row = PathRow(
            opts.body,
            "参考 g00",
            mode="file",
            filetypes=G00_FILETYPES,
            hint="创建/更新模式可选",
        )
        self.refer_row.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op.startswith("分析"):
            self.input_row.pack(fill=tk.X, pady=4)
            self.input_row.set_mode("file", filetypes=G00_FILETYPES)
            self.input_row.set_hint("选择单个 .g00 文件（结果在下方日志）")
            self.output_row.pack_forget()
            self.merge_list.pack_forget()
            self.trim.pack_forget()
            self.type_row.pack_forget()
            self.refer_row.pack_forget()
        elif op.startswith("提取"):
            self.input_row.pack(fill=tk.X, pady=4)
            self.input_row.set_mode("file_or_dir", filetypes=G00_FILETYPES)
            self.input_row.set_hint("单个 .g00，或包含多个 .g00 的文件夹")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.output_row.set_label("输出目录")
            self.output_row.set_hint("提取出的 PNG/JPEG 将写入此文件夹")
            self.merge_list.pack_forget()
            self.trim.widget.pack(anchor=tk.W, pady=2)
            self.type_row.pack_forget()
            self.refer_row.pack_forget()
        elif op.startswith("合并"):
            self.input_row.pack_forget()
            self.merge_list.pack(fill=tk.X, pady=4)
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.output_row.set_label("输出目录")
            self.output_row.set_hint("合并后的 PNG 将写入此文件夹")
            self.trim.widget.pack(anchor=tk.W, pady=2)
            self.type_row.pack_forget()
            self.refer_row.pack_forget()
        else:
            self.input_row.pack(fill=tk.X, pady=4)
            self.input_row.set_mode("file_or_dir", filetypes=IMAGE_FILETYPES)
            self.input_row.set_hint("PNG/JPEG/JSON 布局，或包含这些文件的文件夹")
            self.merge_list.pack_forget()
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("save_or_dir", filetypes=G00_FILETYPES)
            self.output_row.set_label("输出")
            self.output_row.set_hint("可指定 .g00 文件路径，或选择输出文件夹；留空则使用默认位置")
            self.trim.pack_forget()
            self.type_row.pack(fill=tk.X, pady=4)
            self.refer_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        op = self.op.get()
        argv = ["-g"]
        if op.startswith("分析"):
            argv.extend(["--a", self.input_row.get()])
            if err := self.input_row.validate_exists(required=True):
                return err
            return argv, self._hint_from_path(self.input_row.get())
        if op.startswith("提取"):
            if err := self.input_row.validate_exists(required=True):
                return err
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.append("--x")
            if self.trim.get():
                argv.append("--trim")
            argv.extend([self.input_row.get(), out])
            self._output_hint = Path(out)
            return argv, self._output_hint
        if op.startswith("合并"):
            if err := self.merge_list.validate():
                return err
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.append("--m")
            if self.trim.get():
                argv.append("--trim")
            argv.extend(self.merge_list.paths())
            argv.extend(["--o", out])
            self._output_hint = Path(out)
            return argv, self._output_hint
        # create
        if err := self.input_row.validate_exists(required=True):
            return err
        argv.append("--c")
        gtype = self.type_row.get()
        if gtype:
            argv.extend(["--type", gtype])
        refer = self.refer_row.get()
        if refer:
            argv.extend(["--refer", refer])
        argv.append(self.input_row.get())
        out = self.output_row.get()
        if out:
            argv.append(out)
            self._output_hint = self._hint_from_path(out)
        else:
            self._output_hint = self._hint_from_path(self.input_row.get())
        return argv, self._output_hint


class SoundPanel(BasePanel):
    TITLE = "音频"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent,
            "操作",
            ["提取 --x", "分析 --a", "编码 --c", "播放 --play"],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.input_row = PathRow(
            paths.body, "输入", mode="file_or_dir", filetypes=AUDIO_FILETYPES
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(paths.body, "输出目录", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.gameexe_row = PathRow(
            paths.body,
            "Gameexe.dat",
            mode="file",
            filetypes=DAT_FILETYPES,
            hint="提取/播放时可选，用于正确解密",
        )
        self.gameexe_row.pack(fill=tk.X, pady=4)
        self.angou = AngouRow(paths.body)
        self.angou.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op.startswith("分析"):
            self.input_row.set_mode("file", filetypes=AUDIO_FILETYPES)
            self.input_row.set_hint("选择 .ovk / .owp / .nwa 文件")
            self.output_row.pack_forget()
            self.gameexe_row.pack_forget()
        elif op.startswith("播放"):
            self.input_row.set_mode("file_or_dir", filetypes=AUDIO_FILETYPES)
            self.input_row.set_hint("单个音频文件，或包含多个音频的文件夹")
            self.output_row.pack_forget()
            self.gameexe_row.pack(fill=tk.X, pady=4)
        elif op.startswith("提取"):
            self.input_row.set_mode("file_or_dir", filetypes=AUDIO_FILETYPES)
            self.input_row.set_hint("游戏音频目录或单个音频包文件")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.gameexe_row.pack(fill=tk.X, pady=4)
        else:
            self.input_row.set_mode("file", filetypes=[("OGG", "*.ogg"), ("所有文件", "*.*")])
            self.input_row.set_hint("选择要编码的 .ogg 文件")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.gameexe_row.pack_forget()

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        op = self.op.get()
        argv = ["-s"]
        if err := self.input_row.validate_exists(required=True):
            return err
        if op.startswith("提取"):
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.extend(["--x", self.input_row.get(), out])
            ge = self.gameexe_row.get()
            if ge:
                argv.extend(["--trim", ge])
            self._output_hint = Path(out)
        elif op.startswith("分析"):
            argv.extend(["--a", self.input_row.get()])
            self._output_hint = self._hint_from_path(self.input_row.get())
        elif op.startswith("编码"):
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.extend(["--c", self.input_row.get(), out])
            self._output_hint = Path(out)
        else:
            argv.extend(["--play", self.input_row.get()])
            ge = self.gameexe_row.get()
            if ge:
                argv.append(ge)
            self._output_hint = self._hint_from_path(self.input_row.get())
        self.angou.append_argv(argv)
        return argv, self._output_hint


class VideoPanel(BasePanel):
    TITLE = "视频"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent,
            "操作",
            ["提取 --x", "分析 --a", "编码 --c"],
            command=self._on_op,
        )
        paths = Section(parent, "路径")
        paths.pack(fill=tk.X, pady=4)
        self.input_row = PathRow(
            paths.body, "输入", mode="file_or_dir", filetypes=VIDEO_FILETYPES
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(paths.body, "输出", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.refer_row = PathRow(
            paths.body,
            "参考 omv",
            mode="file",
            filetypes=VIDEO_FILETYPES,
            hint="编码模式可选",
        )
        self.refer_row.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op.startswith("分析"):
            self.input_row.set_mode("file", filetypes=VIDEO_FILETYPES)
            self.input_row.set_hint("选择 .omv 文件")
            self.output_row.pack_forget()
            self.refer_row.pack_forget()
        elif op.startswith("提取"):
            self.input_row.set_mode("file", filetypes=VIDEO_FILETYPES)
            self.input_row.set_hint("选择 .omv 文件")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.output_row.set_hint("提取出的视频将写入此文件夹")
            self.refer_row.pack_forget()
        else:
            self.input_row.set_mode("file", filetypes=[("OGV", "*.ogv"), ("所有文件", "*.*")])
            self.input_row.set_hint("选择要编码的 .ogv 文件")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("save_or_dir", filetypes=VIDEO_FILETYPES)
            self.output_row.set_hint("可指定输出 .omv 文件，或选择输出文件夹")
            self.refer_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True):
            return err
        op = self.op.get()
        argv = ["-v"]
        if op.startswith("提取"):
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.extend(["--x", self.input_row.get(), out])
            self._output_hint = Path(out)
        elif op.startswith("分析"):
            argv.extend(["--a", self.input_row.get()])
            self._output_hint = self._hint_from_path(self.input_row.get())
        else:
            out = self.output_row.get()
            if not out:
                return "请指定输出文件或目录"
            argv.extend(["--c", self.input_row.get(), out])
            refer = self.refer_row.get()
            if refer:
                argv.extend(["--refer", refer])
            self._output_hint = self._hint_from_path(out)
        return argv, self._output_hint


class DbPanel(BasePanel):
    TITLE = "数据库"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent, "操作", ["导出 --x", "分析 --a", "编译 --c"], command=self._on_op
        )
        self.input_row = PathRow(
            parent, "输入", mode="file_or_dir", filetypes=DBS_FILETYPES
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.type_row = TextRow(parent, "数据库类型")
        self.type_row.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op.startswith("导出"):
            self.input_row.set_mode("file_or_dir", filetypes=DBS_FILETYPES)
            self.input_row.set_hint(".dbs 文件，或包含多个 .dbs 的文件夹")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("dir")
            self.output_row.set_hint("导出的 CSV 将写入此文件夹")
            self.type_row.pack_forget()
        elif op.startswith("分析"):
            self.input_row.set_mode("file", filetypes=DBS_FILETYPES)
            self.input_row.set_hint("选择 .dbs 文件")
            self.output_row.pack_forget()
            self.type_row.pack_forget()
        else:
            self.input_row.set_mode("file_or_dir")
            self.input_row.set_hint("CSV 文件，或包含 CSV 的编译目录")
            self.output_row.pack(fill=tk.X, pady=4)
            self.output_row.set_mode("save_or_dir", filetypes=DBS_FILETYPES)
            self.output_row.set_hint("可指定输出 .dbs 文件，或选择输出文件夹")
            self.type_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True):
            return err
        op = self.op.get()
        argv = ["-d"]
        if op.startswith("导出"):
            out = self.output_row.get()
            if not out:
                return "请指定输出目录"
            argv.extend(["--x", self.input_row.get(), out])
            self._output_hint = Path(out)
        elif op.startswith("分析"):
            argv.extend(["--a", self.input_row.get()])
            self._output_hint = self._hint_from_path(self.input_row.get())
        else:
            out = self.output_row.get()
            if not out:
                return "请指定输出"
            argv.append("--c")
            gtype = self.type_row.get()
            if gtype:
                argv.extend(["--type", gtype])
            argv.extend([self.input_row.get(), out])
            self._output_hint = self._hint_from_path(out)
        return argv, self._output_hint


class KoePanel(BasePanel):
    TITLE = "语音收集"

    def _build(self, parent: ttk.Frame) -> None:
        self.mode = labeled_radio(
            parent,
            "模式",
            [("scene", "按场景收集"), ("single", "单条 KOE 编号")],
        )
        self.scene_row = PathRow(
            parent, "场景输入", mode="file_or_dir", filetypes=PCK_FILETYPES
        )
        self.scene_row.pack(fill=tk.X, pady=4)
        self.koe_no = TextRow(parent, "KOE 编号")
        self.koe_no.pack(fill=tk.X, pady=4)
        self.voice_row = PathRow(parent, "语音资源目录", mode="dir")
        self.voice_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出目录", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.stats_only = labeled_check(parent, "仅统计不提取（--stats-only）", in_section=False)
        self.angou = AngouRow(parent)
        self.angou.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.voice_row.validate_exists(required=True, as_dir=True):
            return err
        if err := self.output_row.validate_exists(required=True, as_dir=True):
            return err
        argv = ["-k"]
        if self.stats_only.get():
            argv.append("--stats-only")
        if self.mode.get() == "single":
            no = self.koe_no.get()
            if not no:
                return "请填写 KOE 编号"
            argv.extend(["--single", no])
        else:
            if err := self.scene_row.validate_exists(required=True):
                return err
            argv.append(self.scene_row.get())
        argv.extend([self.voice_row.get(), self.output_row.get()])
        self._output_hint = Path(self.output_row.get())
        self.angou.append_argv(argv)
        return argv, self._output_hint


class TextmapPanel(BasePanel):
    TITLE = "文本映射"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_radio(
            parent,
            "操作",
            [
                ("ss", "从 .ss 导出"),
                ("ss_apply", "写回 .ss"),
                ("dat", "从 .dat 导出"),
                ("dat_apply", "写回 .dat"),
            ],
        )
        self.input_row = PathRow(
            parent,
            "输入",
            mode="file_or_dir",
            hint=".ss / .dat 文件，或包含这些文件的目录",
        )
        self.input_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True):
            return err
        argv = ["-m"]
        op = self.op.get()
        if op == "ss_apply":
            argv.append("--apply")
        elif op == "dat":
            argv.append("--disam")
        elif op == "dat_apply":
            argv.append("--disam-apply")
        argv.append(self.input_row.get())
        self._output_hint = self._hint_from_path(self.input_row.get())
        return argv, self._output_hint


class PatchPanel(BasePanel):
    TITLE = "引擎补丁"

    def _build(self, parent: ttk.Frame) -> None:
        self.op = labeled_combo(
            parent,
            "操作",
            [
                "更换密钥 --altkey",
                "CJK 语言 --lang cjk",
                "CJK + 中文路径 --lang cjk-path",
                "查看信息 --info",
                "地域检测 --loc",
            ],
        )
        self.exe_row = PathRow(parent, "SiglusEngine.exe", mode="file")
        self.exe_row.pack(fill=tk.X, pady=4)
        self.key_row = PathRow(parent, "密钥来源", mode="file_or_dir")
        self.key_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            parent,
            "输出 exe",
            mode="save",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
        )
        self.output_row.pack(fill=tk.X, pady=4)
        self.loc = labeled_combo(parent, "地域检测", ["关闭 (0)", "恢复 (1)"])
        self.inplace = labeled_check(parent, "直接覆盖原文件（--inplace）", in_section=False)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.exe_row.validate_exists(required=True, as_dir=False):
            return err
        exe = self.exe_row.get()
        op = self.op.get()
        argv = ["-p"]
        if op.startswith("更换"):
            key = self.key_row.get()
            if not key:
                return "请指定密钥来源文件"
            if err := self.key_row.validate_exists(required=True, as_dir=False):
                return err
            argv.extend(["--altkey", exe, key])
        elif op.startswith("CJK +"):
            argv.extend(["--lang", "cjk-path", exe])
        elif op.startswith("CJK"):
            argv.extend(["--lang", "cjk", exe])
        elif op.startswith("查看"):
            argv.extend(["--info", exe])
            return argv, self._hint_from_path(exe)
        else:
            loc = "0" if self.loc.get().startswith("关闭") else "1"
            argv.extend(["--loc", loc, exe])
        out = self.output_row.get()
        if out:
            argv.extend(["-o", out])
            self._output_hint = self._hint_from_path(out)
        elif self.inplace.get():
            argv.append("--inplace")
            self._output_hint = self._hint_from_path(exe)
        else:
            self._output_hint = self._hint_from_path(exe)
        return argv, self._output_hint


class TutorialPanel(BasePanel):
    TITLE = "场景教程"

    def _build(self, parent: ttk.Frame) -> None:
        self.input_row = PathRow(
            parent,
            "输入 Scene.pck",
            mode="file",
            filetypes=PCK_FILETYPES,
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            parent,
            "输出 JSON",
            mode="save",
            filetypes=[("JSON", "*.json"), ("所有文件", "*.*")],
        )
        self.output_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True, as_dir=False):
            return err
        argv = ["-t", self.input_row.get()]
        out = self.output_row.get()
        if out:
            argv.append(out)
            self._output_hint = self._hint_from_path(out)
        else:
            self._output_hint = self._hint_from_path(self.input_row.get())
        return argv, self._output_hint


class ExecPanel(BasePanel):
    TITLE = "执行标签"

    def _build(self, parent: ttk.Frame) -> None:
        self.engine_row = PathRow(parent, "引擎路径", mode="file")
        self.engine_row.pack(fill=tk.X, pady=4)
        self.scene_row = TextRow(parent, "场景名")
        self.scene_row.pack(fill=tk.X, pady=4)
        self.label_row = TextRow(parent, "标签名")
        self.label_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.engine_row.validate_exists(required=True, as_dir=False):
            return err
        scene = self.scene_row.get()
        label = self.label_row.get()
        if not scene:
            return "请填写场景名"
        if not label:
            return "请填写标签名"
        argv = ["-e", self.engine_row.get(), scene, label]
        return argv, self._hint_from_path(self.engine_row.get())


class InitPanel(BasePanel):
    TITLE = "初始化"

    def _build(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="下载或刷新运行时常量 const.py。首次使用其他功能前请先执行一次。",
            wraplength=520,
        ).pack(anchor=tk.W, pady=(0, 8))
        self.force = labeled_check(parent, "强制覆盖已有常量（--force）", in_section=False)
        self.ref_row = TextRow(parent, "Git 引用")
        self.ref_row.pack(fill=tk.X, pady=4)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        argv = ["init"]
        if self.force.get():
            argv.append("--force")
        ref = self.ref_row.get()
        if ref:
            argv.extend(["--ref", ref])
        return argv, None


class TestPanel(BasePanel):
    TITLE = "回编测试"

    def _build(self, parent: ttk.Frame) -> None:
        self.input_row = PathRow(
            parent,
            "输入",
            mode="file_or_dir",
            filetypes=PCK_FILETYPES,
            hint="单个 .pck 或包含多个 .pck 的文件夹",
        )
        self.input_row.pack(fill=tk.X, pady=4)
        self.serial = labeled_check(parent, "串行编译（--serial）", in_section=False)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        if err := self.input_row.validate_exists(required=True):
            return err
        argv = ["test"]
        if self.serial.get():
            argv.append("--serial")
        argv.append(self.input_row.get())
        return argv, self._hint_from_path(self.input_row.get())


class LspPanel(BasePanel):
    TITLE = "语言服务器"
    background = True

    def _build(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="启动 SiglusSS 语言服务器（供编辑器 LSP 集成）。点击开始后保持运行，使用「停止」结束。",
            wraplength=520,
        ).pack(anchor=tk.W, pady=(0, 8))
        self.serial = labeled_check(parent, "禁用并行扫描（--serial）", in_section=False)

    def _build_command(self) -> tuple[list[str], Path | None] | str:
        argv = ["-lsp"]
        if self.serial.get():
            argv.append("--serial")
        return argv, None


PANELS: list[tuple[str, type[BasePanel]]] = [
    ("extract", ExtractPanel),
    ("compile", CompilePanel),
    ("analyze", AnalyzePanel),
    ("g00", G00Panel),
    ("sound", SoundPanel),
    ("video", VideoPanel),
    ("db", DbPanel),
    ("koe", KoePanel),
    ("textmap", TextmapPanel),
    ("patch", PatchPanel),
    ("tutorial", TutorialPanel),
    ("exec", ExecPanel),
    ("init", InitPanel),
    ("test", TestPanel),
    ("lsp", LspPanel),
]

PANEL_LABELS = {
    "extract": "提取",
    "compile": "编译",
    "analyze": "分析",
    "g00": "图片 g00",
    "sound": "音频",
    "video": "视频",
    "db": "数据库",
    "koe": "语音收集",
    "textmap": "文本映射",
    "patch": "引擎补丁",
    "tutorial": "场景教程",
    "exec": "执行标签",
    "init": "初始化",
    "test": "回编测试",
    "lsp": "语言服务器",
}

PANEL_ORDER = [
    "extract",
    "compile",
    "analyze",
    "textmap",
    "tutorial",
    "g00",
    "sound",
    "video",
    "db",
    "koe",
    "patch",
    "exec",
    "init",
    "test",
    "lsp",
]

PANEL_NAV_GROUPS: list[tuple[str, list[str]]] = [
    (
        "场景与脚本",
        ["extract", "compile", "analyze", "textmap", "tutorial", "exec"],
    ),
    (
        "游戏资源",
        ["g00", "sound", "video", "db", "koe"],
    ),
    (
        "系统与工具",
        ["patch", "init", "test", "lsp"],
    ),
]

PANEL_HINTS: dict[str, str] = {
    "extract": "从 .pck 解包场景，或将 .dat 反汇编为可读脚本。汉化流程的第一步。",
    "compile": "把修改后的 .ss 目录重新打包为 .pck。汉化流程的最后一步。",
    "analyze": "查看包内结构、对比两个文件差异、统计台词字数。结果输出在下方日志。",
    "g00": "处理 Siglus 图片资源：分析、提取 PNG、合并或从图片创建 .g00。",
    "sound": "提取/分析/编码游戏音频（.ovk .owp .nwa .ogg）。",
    "video": "提取或编码游戏视频（.omv / .ogv）。",
    "db": "导出、分析或重新编译游戏数据库 .dbs。",
    "koe": "按场景或编号从 voice 目录收集角色语音到子文件夹。",
    "textmap": "在 .ss / .dat 与 CSV 表格之间导出、写回译文（翻译工作流核心）。",
    "patch": "修改 SiglusEngine.exe：换密钥、CJK 中文显示、中文路径等。请先备份原文件。",
    "tutorial": "从 Scene.pck 生成剧情分支 JSON，配合 tutorial_viewer.html 查看。",
    "exec": "从指定场景标签启动引擎（调试用）。",
    "init": "下载运行时常量 const.py。首次使用或升级工具后执行一次。",
    "test": "自动执行 提取→编译→对比，验证工具链是否正常。",
    "lsp": "启动语言服务器，供 VS Code / Cursor 获得 .ss 语法提示。",
}
