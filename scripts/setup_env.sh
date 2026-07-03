#!/usr/bin/env sh
set -e
cd "$(dirname "$0")/.."
echo "SiglusSSU-GUI 环境配置"
if command -v uv >/dev/null 2>&1; then
  uv python install 3.12
  exec uv sync
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/setup_env.py "$@"
elif command -v python >/dev/null 2>&1; then
  exec python scripts/setup_env.py "$@"
else
  echo "需要 Python 3.8+ 或已安装的 uv（可自动下载 Python 3.12）" >&2
  exit 1
fi