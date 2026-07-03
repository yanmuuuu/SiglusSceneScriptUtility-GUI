# 上游项目说明

本仓库基于 **[Jirehlov/SiglusSceneScriptUtility](https://github.com/Jirehlov/SiglusSceneScriptUtility)** 开发，在保留其 CLI 能力的同时增加图形界面。

| 项目 | 说明 |
|---|---|
| 上游仓库 | https://github.com/Jirehlov/SiglusSceneScriptUtility |
| 上游作者 | [Jirehlov](https://github.com/Jirehlov) |
| 捆绑 CLI 版本 | 0.3.7（见 `pyproject.toml` 中 `upstream-version`） |
| GUI 版本 | 0.1.0 |

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
