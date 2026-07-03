# SiglusSceneScriptUtility GUI

为 [SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility)（`siglus-ssu`）提供图形界面，让提取、编译、文本映射等常用操作可以通过文件选择器和中文界面完成，无需记忆命令行参数。

> 本仓库在 upstream 项目基础上增加 GUI 层及相关文档；核心编译、提取逻辑仍由上游 `siglus-ssu` 提供。

## 上游项目

| 项目 | 链接 |
|---|---|
| 仓库 | [Jirehlov/SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility) |
| 作者 | [Jirehlov](https://github.com/Jirehlov) |
| CLI 手册（中文） | [manual_cn.md](manual_cn.md) |
| CLI 手册（英文） | [manual.md](manual.md) |
| 更新日志 | [changelog.md](changelog.md) |

感谢上游项目对 SiglusEngine 资源格式的研究与实现。使用 CLI 的完整参数说明、语言规范与故障排除，请以 upstream 手册为准。

## 本仓库内容

| 文件 | 说明 |
|---|---|
| [SPEC.md](SPEC.md) | GUI 界面与功能规格（开发参考） |
| [instructions.md](instructions.md) | 图形界面操作指南（中文） |
| `src/siglus_ssu/` | 上游 CLI 源码（与 upstream 同步） |
| `src/siglus_ssu_gui/` | GUI 实现（tkinter） |

GUI 通过子进程调用 `siglus-ssu`，不重复实现底层逻辑，行为与命令行一致。

## 功能概览

图形界面按 `siglus-ssu` 命令分区，支持通过浏览按钮选择输入文件/文件夹及输出路径：

| 功能 | 对应命令 |
|---|---|
| 提取 | `siglus-ssu -x` |
| 编译 | `siglus-ssu -c` |
| 分析 | `siglus-ssu -a` |
| 图片 g00 | `siglus-ssu -g` |
| 音频 | `siglus-ssu -s` |
| 视频 | `siglus-ssu -v` |
| 数据库 | `siglus-ssu -d` |
| 语音收集 | `siglus-ssu -k` |
| 文本映射 | `siglus-ssu -m` |
| 引擎补丁 | `siglus-ssu -p` |
| 场景教程 | `siglus-ssu -t` |
| 执行标签 | `siglus-ssu -e` |
| 初始化 | `siglus-ssu init` |
| 回编测试 | `siglus-ssu test` |
| 语言服务器 | `siglus-ssu -lsp` |

详细操作步骤见 **[instructions.md](instructions.md)**。

## 便携版（推荐，无需安装 Python）

像 **FModel** 一样：下载 → 解压到桌面 → 双击运行。

1. 在 GitHub **Releases** 页面下载 `SiglusSSU-GUI-portable.zip`（发布前可从 Actions → Portable Windows Build 的 Artifacts 下载）
2. 解压得到 `SiglusSSU-GUI` 文件夹
3. 将整个文件夹放到桌面（或任意位置）
4. **双击 `SiglusSSU-GUI.exe`** 即可使用

> 请保持文件夹完整，不要只复制 exe。`_internal` 目录必须与 exe 在同一文件夹内。

首次运行若提示缺少常量文件，在程序内选择 **初始化** 并执行一次（需联网）。

文件夹内附带 `使用说明.txt`，更多操作见 [instructions.md](instructions.md#便携版推荐)。

### 自行打包便携版（开发者）

需要 Python 3.12+ 与 [Rust](https://rustup.rs/)，在项目根目录执行：

```bat
scripts\build_portable.bat
```

产出：`dist/SiglusSSU-GUI/`（可复制到桌面）与 `dist/SiglusSSU-GUI-portable.zip`。

## 安装（开发者 / 源码）

### 前提条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)（推荐，与 upstream 一致）
- Rust 工具链（构建原生加速扩展，见 [rustup.rs](https://rustup.rs/)）

### 从源码

```bash
git clone <本仓库地址>
cd SiglusSceneScriptUtility-GUI

uv sync
uv run siglus-ssu init   # 若提示缺少 const.py
uv run siglus-ssu-gui    # 启动图形界面
```

### 使用 CLI（无需 GUI）

```bash
# 提取 Scene.pck
uv run siglus-ssu -x /path/to/Scene.pck /path/to/translation_work

# 编译回 .pck
uv run siglus-ssu -c /path/to/translation_work /path/to/Scene_translated.pck
```

也可从 PyPI 安装上游包：`pip install siglus-ssu`（见 [manual_cn.md](manual_cn.md)）。

### 启动 GUI

```bash
uv run siglus-ssu-gui
# 或
uv run python -m siglus_ssu_gui
```

## 典型工作流（汉化）

1. **提取**：选择 `Scene.pck`，输出到工作目录，可选反汇编/反编译
2. **编辑**：修改脚本，或通过「文本映射」导出/翻译/写回 CSV
3. **编译**：选择工作目录，输出为 `SceneZH.pck` 等
4. **（可选）引擎补丁**：对 `SiglusEngine.exe` 应用 CJK 或中文路径补丁

分步说明见 [instructions.md](instructions.md#常用工作流)。

## 许可证与归属

- 上游 [SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility) 及其文档、源码版权归原作者所有。
- 本仓库 GUI 相关代码与文档（`SPEC.md`、`instructions.md`、`src/siglus_ssu_gui/` 等）由本仓库维护；合并或同步 upstream 更新时，请保留上游版权与致谢信息。

## 相关链接

- 上游仓库：https://github.com/Jirehlov/SiglusSceneScriptUtility
- 上游 Issues：https://github.com/Jirehlov/SiglusSceneScriptUtility/issues

CLI 或格式相关的问题请先查阅 upstream 手册与 Issues；GUI 界面问题请在本仓库反馈。
