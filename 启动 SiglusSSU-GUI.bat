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

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [首次运行] 未检测到虚拟环境，正在自动配置（uv + Python 3.12 + 依赖）…
    echo.
    call :bootstrap_env
    if errorlevel 1 goto :nopython
    echo.
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

:bootstrap_env
where uv >nul 2>&1
if %errorlevel%==0 (
    echo 检测到 uv，直接同步依赖…
    uv python install 3.12
    uv sync
    exit /b %errorlevel%
)
set "BOOTPY="
call :try_boot py -3.12
if defined BOOTPY goto :do_boot
call :try_boot py -3
if defined BOOTPY goto :do_boot
call :try_boot python3
if defined BOOTPY goto :do_boot
call :try_boot python
if defined BOOTPY goto :do_boot
echo 无法找到 Python 或 uv。请先双击 环境配置.bat，或安装 Python 3.12+ / uv。
exit /b 1

:try_boot
%1 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,8) else 2)" 2>nul
if %errorlevel%==0 set "BOOTPY=%1"
exit /b 0

:do_boot
%BOOTPY% "%~dp0scripts\setup_env.py"
exit /b %errorlevel%

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
echo 【从源码运行 - 克隆仓库后】
echo   1. 双击 环境配置.bat  （或 启动 SiglusSSU-GUI.bat 首次会自动配置）
echo   2. 脚本会自动：安装 uv（若无）→ 下载 Python 3.12（若无）→ uv sync 安装依赖
echo   3. 需要开发/打包工具时: scripts\setup_env.bat --dev
echo.
echo 【开发者 - 手动命令】
echo   - 必须 Python 3.12 或更高（3.11 及以下不支持）
echo   - 或仅安装 uv 后: uv sync  （uv 可自动下载 Python 3.12）
echo   - 启动: uv run siglus-ssu-gui
echo.
pause
exit /b 1
