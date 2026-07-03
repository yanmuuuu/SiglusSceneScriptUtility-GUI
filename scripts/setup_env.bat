@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo SiglusSSU-GUI 环境配置
echo.

set "PY="
call :try_py py -3.12
if defined PY goto :run
call :try_py py -3
if defined PY goto :run
call :try_py python3
if defined PY goto :run
call :try_py python
if defined PY goto :run

where uv >nul 2>&1
if %errorlevel%==0 (
    echo 未找到本机 Python，使用 uv 自动准备环境…
    uv python install 3.12
    uv sync
    if errorlevel 1 goto :fail
    if /i not "%~1"=="--no-pause" pause
    exit /b 0
)

echo 未找到 Python 3.8+ 或 uv。请先安装其一，或从 https://www.python.org/downloads/ 安装 Python 3.12+
goto :fail

:fail
if /i not "%~1"=="--no-pause" pause
exit /b 1

:try_py
%1 -c "import sys; raise SystemExit(0 if sys.version_info>=(3,8) else 2)" 2>nul
if %errorlevel%==0 set "PY=%1"
exit /b 0

:run
echo 使用: %PY%
%PY% scripts\setup_env.py %*
if errorlevel 1 (
    echo.
    echo 配置失败。请确认网络可用，或手动安装 Python 3.12+ 与 uv。
    if /i not "%~1"=="--no-pause" pause
    exit /b 1
)
echo.
if /i not "%~1"=="--no-pause" pause
exit /b 0
