"""Inspect media URLs stored in DB and verify they are reachable."""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import httpx
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal

logging.disable(logging.INFO)


async def main() -> None:
    urls: list[tuple[str, str]] = []
    async with AsyncSessionLocal() as s:
        r = await s.execute(
            text("SELECT employee_id, name, profile_photo_url FROM users ORDER BY employee_id")
        )
        for emp, name, url in r.all():
            print(f"USER {emp} | {name} | {url}")
            if url:
                urls.append((f"user {emp}", url))

        r = await s.execute(
            text(
                "SELECT name, photos FROM farms "
                "WHERE photos IS NOT NULL AND photos::text != '[]' "
                "ORDER BY created_at DESC LIMIT 5"
            )
        )
        for name, photos in r.all():
            print(f"FARM {name} | {photos}")
            if isinstance(photos, list):
                for p in photos[:2]:
                    urls.append((f"farm {name}", p))

        r = await s.execute(text("SELECT name, photo_url FROM farmers LIMIT 5"))
        for name, url in r.all():
            print(f"FARMER {name} | {url}")
            if url:
                urls.append((f"farmer {name}", url))

    print("\n--- reachability ---")
    with httpx.Client(timeout=20) as c:
        for label, url in urls:
            try:
                resp = c.get(url)
                print(f"{resp.status_code} | {len(resp.content):>8} bytes | {label} | {url[:110]}")
            except Exception as e:  # noqa: BLE001
                print(f"ERR  | {label} | {e}")


if __name__ == "__main__":
    asyncio.run(main())
