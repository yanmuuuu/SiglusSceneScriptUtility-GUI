from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import ttk

from ..widgets import (
    AngouRow,
    FileListRow,
    PathRow,
    TextRow,
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
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出目录", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.disam = labeled_check(parent, "同时反汇编并反编译（--disam）")
        self.angou = AngouRow(parent)
        self.angou.pack(fill=tk.X, pady=4)
        self._on_op()

    def _on_op(self) -> None:
        op = self.op.get()
        if op == "pck":
            self.disam.pack(anchor=tk.W, pady=1)
        else:
            self.disam.pack_forget()

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
        )
        self.input_row = PathRow(parent, "输入目录", mode="dir")
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            parent,
            "输出",
            mode="save",
            filetypes=[("PCK 文件", "*.pck"), ("所有文件", "*.*")],
        )
        self.output_row.pack(fill=tk.X, pady=4)
        opts = ttk.LabelFrame(parent, text="选项", padding=6)
        opts.pack(fill=tk.X, pady=4)
        self.charset = labeled_combo(opts, "源文件编码", ["自动", "UTF-8", "Shift-JIS"])
        self.debug = labeled_check(opts, "保留临时文件（--debug）")
        self.serial = labeled_check(opts, "串行编译（--serial）")
        self.dat_repack = labeled_check(opts, "仅重打包已有 .dat（--dat-repack）")
        self.no_angou = labeled_check(opts, "禁用加密（--no-angou）")
        self.no_lzss = labeled_check(opts, "禁用 LZSS（--no-lzss）")
        self.tmp_row = PathRow(opts, "增量缓存目录", mode="dir")
        self.tmp_row.pack(fill=tk.X, pady=4)

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
        )
        self.in1 = PathRow(parent, "输入文件 1", mode="file")
        self.in1.pack(fill=tk.X, pady=4)
        self.in2 = PathRow(parent, "输入文件 2", mode="file")
        self.in2.pack(fill=tk.X, pady=4)
        self.csv_out = PathRow(
            parent,
            "输出 CSV",
            mode="save",
            filetypes=[("CSV", "*.csv"), ("所有文件", "*.*")],
        )
        self.csv_out.pack(fill=tk.X, pady=4)
        self.disam = labeled_check(parent, "写出反汇编（--disam）")
        self.payload = labeled_check(parent, "语义级比较（--payload）")
        self.angou = AngouRow(parent)
        self.angou.pack(fill=tk.X, pady=4)

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
        self.op = labeled_combo(parent, "操作", ["分析 --a", "提取 --x", "合并 --m", "创建 --c"])
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.merge_list = FileListRow(parent, "合并文件列表（--m）")
        self.merge_list.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出", mode="either")
        self.output_row.pack(fill=tk.X, pady=4)
        self.trim = labeled_check(parent, "裁剪透明边（--trim）")
        self.type_row = TextRow(parent, "g00 类型")
        self.type_row.pack(fill=tk.X, pady=4)
        self.refer_row = PathRow(parent, "参考 g00", mode="file")
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
        self.op = labeled_combo(parent, "操作", ["提取 --x", "分析 --a", "编码 --c", "播放 --play"])
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出目录", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.gameexe_row = PathRow(parent, "Gameexe.dat", mode="file")
        self.gameexe_row.pack(fill=tk.X, pady=4)
        self.angou = AngouRow(parent)
        self.angou.pack(fill=tk.X, pady=4)

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
        self.op = labeled_combo(parent, "操作", ["提取 --x", "分析 --a", "编码 --c"])
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出", mode="either")
        self.output_row.pack(fill=tk.X, pady=4)
        self.refer_row = PathRow(parent, "参考 omv", mode="file")
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
        self.op = labeled_combo(parent, "操作", ["导出 --x", "分析 --a", "编译 --c"])
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出", mode="either")
        self.output_row.pack(fill=tk.X, pady=4)
        self.type_row = TextRow(parent, "数据库类型")
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
        self.scene_row = PathRow(parent, "场景输入", mode="either")
        self.scene_row.pack(fill=tk.X, pady=4)
        self.koe_no = TextRow(parent, "KOE 编号")
        self.koe_no.pack(fill=tk.X, pady=4)
        self.voice_row = PathRow(parent, "语音资源目录", mode="dir")
        self.voice_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(parent, "输出目录", mode="dir")
        self.output_row.pack(fill=tk.X, pady=4)
        self.stats_only = labeled_check(parent, "仅统计不提取（--stats-only）")
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
        self.input_row = PathRow(parent, "输入", mode="either")
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
        self.key_row = PathRow(parent, "密钥来源", mode="file")
        self.key_row.pack(fill=tk.X, pady=4)
        self.output_row = PathRow(
            parent,
            "输出 exe",
            mode="save",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
        )
        self.output_row.pack(fill=tk.X, pady=4)
        self.loc = labeled_combo(parent, "地域检测", ["关闭 (0)", "恢复 (1)"])
        self.inplace = labeled_check(parent, "直接覆盖原文件（--inplace）")

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
            filetypes=[("PCK", "*.pck"), ("所有文件", "*.*")],
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
        self.force = labeled_check(parent, "强制覆盖已有常量（--force）")
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
        self.input_row = PathRow(parent, "输入", mode="either")
        self.input_row.pack(fill=tk.X, pady=4)
        self.serial = labeled_check(parent, "串行编译（--serial）")

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
        self.serial = labeled_check(parent, "禁用并行扫描（--serial）")

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
    "g00",
    "sound",
    "video",
    "db",
    "koe",
    "textmap",
    "patch",
    "tutorial",
    "exec",
    "init",
    "test",
    "lsp",
]
