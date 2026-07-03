# 上游项目说明

本仓库基于 **[Jirehlov/SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility)** 开发，在保留其 CLI 能力的同时增加图形界面。

| 项目 | 说明 |
|---|---|
| 上游仓库 | https://github.com/Jirehlov/SiglusSceneScriptUtility |
| 上游作者 | [Jirehlov](https://github.com/Jirehlov) |
| 捆绑 CLI 版本 | 0.3.7（见 `pyproject.toml` 中 `upstream-version`） |
| GUI 版本 | 0.2.0 |

## 目录归属

| 路径 | 归属 |
|---|---|
| `src/siglus_ssu/` | 上游 CLI 核心（随 upstream 同步） |
| `src/siglus_ssu_gui/` | 本仓库 GUI 实现 |
| `manual.md` / `manual_cn.md` | 上游 CLI 手册（含 GUI 引导注释） |
| `changelog.md` | 变更日志（含 GUI 与上游记录） |
| `SPEC.md` / `instructions.md` | 本仓库 GUI 文档 |

## 同步 upstream

```bash
git remote add upstream https://github.com/Jirehlov/SiglusSceneScriptUtility.git
git fetch upstream
# 按需 cherry-pick 或 merge upstream/main 到 src/siglus_ssu/ 等路径
```

合并时请保留本仓库的 `README.md`、`SPEC.md`、`instructions.md`、`src/siglus_ssu_gui/` 及 `pyproject.toml` 中的 GUI 相关配置。

## 日常 Git 工作流

### 克隆时为什么会带上别人的提交？

`git clone` 复制的是**整个仓库历史**，不只是当前文件。因此本地会保留上游作者从最初到当前的所有 commit；本仓库的 GUI 相关提交是在这条历史**之后**追加的。这是 Fork 式开发的正常行为，便于追溯来源与按需同步上游。

### 两个远程各做什么

| 远程 | 典型地址 | 用途 |
|---|---|---|
| **origin** | `git@github.com:yanmuuuu/SiglusSceneScriptUtility-GUI.git` | 你自己的仓库；日常 `git push` 推到这里 |
| **upstream** | `https://github.com/Jirehlov/SiglusSceneScriptUtility.git` | 上游只读；需要新功能或 bug 修复时 `git fetch` |

首次克隆他人项目并改 remote 后，若尚未配置 upstream，执行：

```bash
git remote add upstream https://github.com/Jirehlov/SiglusSceneScriptUtility.git
```

查看当前配置：

```bash
git remote -v
```

### 日常开发（只改自己的仓库）

```bash
# 改代码 …
git add .
git commit -m "说明本次改动"
git push origin main
```

推送到 **origin** 即可；上游作者的新提交**不会**自动进入你的仓库，只有你主动 fetch / merge 时才会合并进来。

### 同步上游更新

当 [Jirehlov/SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility) 发布新版本或修复 bug 时：

```bash
git fetch upstream
git merge upstream/main
# 若有冲突，按「目录归属」一节保留 GUI 侧文件，合并 CLI 核心变更
git push origin main
```

若只想拿个别提交，可用 `git cherry-pick <commit>`，不必整分支 merge。

同步后建议检查：

- `pyproject.toml` 中的 `upstream-version` 是否需更新
- `changelog.md` 是否记录了本次合并的上游版本
- GUI 面板是否仍能正常调用更新后的 CLI

### 与「从零新建仓库」的区别

| 方式 | 提交历史 | 适用场景 |
|---|---|---|
| **clone 后改造**（本仓库） | 保留上游全部 commit + 自己的 commit | 在 CLI 上加 GUI、偶尔跟上游、方便对比差异 |
| **只复制文件、新建 git** | 仅自己的 commit | 完全独立、不再关心上游历史 |

本仓库采用第一种方式。

