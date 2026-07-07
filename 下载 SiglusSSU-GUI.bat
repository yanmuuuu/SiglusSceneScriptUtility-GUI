@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 下载 SiglusSSU-GUI 便携版
echo.
echo  ========================================
echo    SiglusSSU-GUI 一键下载到桌面
echo  ========================================
echo.
echo  将自动：下载 -^> 解压到桌面 -^> 创建快捷方式
echo  无需安装 Python、ffmpeg 或其它环境。
echo.
set "INSTALLER=%~dp0download_portable.ps1"
if not exist "%INSTALLER%" set "INSTALLER=%~dp0scripts\download_portable.ps1"
if not exist "%INSTALLER%" (
    echo 未找到 download_portable.ps1
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" %*
if errorlevel 1 (
    echo.
    echo 下载失败。若尚无 GitHub 发布包，维护者可先运行 scripts\build_portable.bat
    echo 再执行: powershell -File scripts\download_portable.ps1 -Local
    echo.
    pause
    exit /b 1
)
