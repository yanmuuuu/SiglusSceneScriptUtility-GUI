@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo CLANNAD 全功能回归测试（输出到桌面\g00）
echo 完整测试含回编约 15 分钟；加 --quick 跳过最慢项
echo.
where uv >nul 2>&1
if %errorlevel%==0 (
    uv run python scripts\test_clannad.py %*
) else (
    python scripts\test_clannad.py %*
)
pause
