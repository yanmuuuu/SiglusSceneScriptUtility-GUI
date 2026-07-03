@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo SiglusSceneScriptUtility GUI
echo.

if exist "%~dp0dist\SiglusSSU-GUI\SiglusSSU-GUI.exe" (
    echo [便携版] 无需 Python，正在启动...
    start "" "%~dp0dist\SiglusSSU-GUI\SiglusSSU-GUI.exe"
    exit /b 0
)

set "PYCMD="
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info>=(3,12) else 2)" 2>nul
    if %errorlevel%==0 set "PYCMD=%~dp0.venv\Scripts\python.exe"
)
if defined PYCMD goto :launch
call :try_py py -3.12
if defined PYCMD goto :launch
call :try_py py -3
if defined PYCMD goto :launch
call :try_py python3
if defined PYCMD goto :launch
call :try_py python
if defined PYCMD goto :launch
goto :nopython

:try_py
%1 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,12) else 2)" 2>nul
if %errorlevel%==0 set "PYCMD=%1"
exit /b 0

:launch
set "PYTHONPATH=%~dp0src"
echo [源码] 使用 %PYCMD%
%PYCMD% -c "import sys; print('Python', sys.version.split()[0])"
%PYCMD% -m siglus_ssu_gui
if errorlevel 1 goto :failed
exit /b 0

:failed
echo.
echo 源码模式启动失败（见上方报错）。
echo 若尚未打包，可在项目根目录运行: scripts\build_portable.bat
goto :nopython

:nopython
echo.
echo ========================================
echo   未能启动 GUI
echo ========================================
echo.
echo 【普通用户 - 推荐，无需 Python】
echo   1. 下载 Releases 中的 SiglusSSU-GUI-portable.zip
echo      或在本机运行 scripts\build_portable.bat 生成便携版
echo   2. 双击 dist\SiglusSSU-GUI\SiglusSSU-GUI.exe
echo.
echo 【开发者 - 从源码运行】
echo   - 必须 Python 3.12 或更高（3.11 及以下不支持）
echo   - 下载: https://www.python.org/downloads/
echo   - 安装时勾选 "Add python.exe to PATH"
echo   - 推荐命令:
echo       uv sync
echo       uv run siglus-ssu-gui
echo.
pause
exit /b 1
