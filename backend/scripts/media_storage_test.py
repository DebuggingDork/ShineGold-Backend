"""Test presign upload flow and DB media stats."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal

BASE = "http://127.0.0.1:8011"
PASSWORD = "ChangeMe123!"


def tiny_jpeg() -> bytes:
    # 1x1 pixel JPEG
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
        b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
        b"\x1c $.\x27 ,#\x1c\x1c(7),01444\x1f\x27=9=82<.342\xff\xc0\x00\x0b\x08"
        b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01"
        b"\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
        b"\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05"
        b"\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa"
        b"\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17"
        b"\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85"
        b"\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5"
        b"\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5"
        b"\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4"
        b"\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda"
        b"\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\x00\x00\xff\xd9"
    )


def tiny_mp3_header() -> bytes:
    return b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 20


def login(client: httpx.Client, employee_id: str) -> str:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        json={"employee_id": employee_id, "password": PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def test_presign_uploads() -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    with httpx.Client(timeout=30.0) as client:
        token = login(client, "EXEC001")
        headers = {"Authorization": f"Bearer {token}"}
        cases = [
            ("visit_photo", "image/jpeg", tiny_jpeg()),
            ("visit_voice", "audio/mpeg", tiny_mp3_header()),
            ("profile_photo", "image/jpeg", tiny_jpeg()),
            ("farm_photo", "image/jpeg", tiny_jpeg()),
        ]
        for context, file_type, body in cases:
            name = f"presign+PUT {context}"
            try:
                r = client.post(
                    f"{BASE}/api/v1/uploads/presign",
                    headers=headers,
                    json={"file_type": file_type, "context": context},
                )
                if r.status_code != 200:
                    results.append((name, False, f"presign {r.status_code}: {r.text[:200]}"))
                    continue
                data = r.json()
                put = client.put(
                    data["upload_url"],
                    content=body,
                    headers={"Content-Type": file_type},
                )
                if put.status_code not in (200, 201):
                    results.append((name, False, f"PUT {put.status_code}: {put.text[:200]}"))
                    continue
                get = client.get(data["public_url"])
                ok = get.status_code == 200 and len(get.content) > 0
                detail = (
                    f"PUT={put.status_code} GET={get.status_code} "
                    f"bytes={len(get.content)} key={data['object_key']}"
                )
                results.append((name, ok, detail))
            except Exception as e:  # noqa: BLE001
                results.append((name, False, str(e)))
    return results


async def db_stats() -> dict[str, object]:
    tables = [
        "users",
        "farms",
        "farmers",
        "farm_executive_assignments",
        "visits",
        "visit_photos",
        "visit_form_templates",
        "visit_form_questions",
        "visit_form_answers",
        "password_reset_requests",
    ]
    stats: dict[str, object] = {}
    async with AsyncSessionLocal() as session:
        for table in tables:
            r = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            stats[table] = r.scalar_one()
        r = await session.execute(
            text("SELECT status, COUNT(*) FROM visits GROUP BY status ORDER BY status")
        )
        stats["visit_status_breakdown"] = list(r.all())
        r = await session.execute(
            text("SELECT COUNT(*) FROM visit_photos WHERE photo_url IS NOT NULL")
        )
        stats["visit_photos_with_url"] = r.scalar_one()
        r = await session.execute(
            text("SELECT COUNT(*) FROM visits WHERE voice_note_url IS NOT NULL")
        )
        stats["visits_with_voice"] = r.scalar_one()
        r = await session.execute(
            text("SELECT COUNT(*) FROM farms WHERE photos IS NOT NULL AND photos::text != '[]'")
        )
        stats["farms_with_photos"] = r.scalar_one()
        r = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE profile_photo_url IS NOT NULL")
        )
        stats["users_with_profile_photo"] = r.scalar_one()
    return stats


def main() -> None:
    print("=== Media presign + Supabase upload ===")
    upload_results = test_presign_uploads()
    passed = 0
    for name, ok, detail in upload_results:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name} — {detail}")
        if ok:
            passed += 1
    print(f"Upload tests: {passed}/{len(upload_results)} passed\n")

    print("=== Database stats (Supabase Postgres) ===")
    stats = asyncio.run(db_stats())
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
