@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo 正在构建 SiglusSSU-GUI 便携版...
echo.
echo 默认：纯 Python 打包（无需 Rust，几分钟内完成）
echo 若已安装 Rust 且需要加速，请运行：python scripts\build_portable.py --rust
echo.
python scripts\build_portable.py %*
