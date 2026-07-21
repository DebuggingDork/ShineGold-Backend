"""Local API base URL for dev scripts and tests.

Port is defined in pyproject.toml [tool.fastapi].port (8000 — same as `fastapi dev` / `fastapi run` default).
Flutter AppConfig.apiPort must match.
Override for a session: SHINEGOLD_API_PORT=8000 or SHINEGOLD_API_BASE=http://127.0.0.1:8000
"""
from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_PORT = 8000


def _port_from_pyproject() -> int:
    try:
        import tomllib

        data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        return int(data["tool"]["fastapi"]["port"])
    except Exception:
        return _DEFAULT_PORT


API_PORT = int(os.environ.get("SHINEGOLD_API_PORT", _port_from_pyproject()))
API_BASE = os.environ.get("SHINEGOLD_API_BASE", f"http://127.0.0.1:{API_PORT}")
