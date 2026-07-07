@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo 正在构建 SiglusSSU-GUI 便携版（含 ffmpeg 音频播放）...
echo.
where uv >nul 2>&1
if %errorlevel%==0 (
    uv run python scripts\build_portable.py %*
) else (
    python scripts\build_portable.py %*
)
