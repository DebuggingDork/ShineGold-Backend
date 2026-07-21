#!/usr/bin/env bash
# Production start script (Render, Docker, VPS).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
