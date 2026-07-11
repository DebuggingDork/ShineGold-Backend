"""Ensure Supabase storage bucket allows all ShineGold media MIME types."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.storage_service import EXTENSION_BY_MIME, storage_service


def main() -> None:
    bucket = storage_service.bucket
    allowed = sorted(EXTENSION_BY_MIME.keys())
    print(f"Updating bucket '{bucket}' allowed_mime_types ({len(allowed)} types)...")
    storage_service.client.storage.update_bucket(
        bucket,
        {"allowed_mime_types": allowed},
    )
    print("Done. Allowed types:")
    for mime in allowed:
        print(f"  - {mime}")


if __name__ == "__main__":
    main()
