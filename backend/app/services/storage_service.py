import uuid
from datetime import datetime
from urllib.parse import urlparse

from supabase import Client, create_client

from app.core.config import settings

ALLOWED_CONTEXTS = {
    "farm_photo": "farms",
    "farmer_photo": "farmers",
    "profile_photo": "profiles",
    "visit_photo": "visits",
    "visit_voice": "visits/voice",
}

EXTENSION_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "audio/mpeg": "mp3",
    "audio/mp4": "m4a",
    "audio/aac": "aac",
    "audio/wav": "wav",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/3gpp": "3gp",
    "audio/amr": "amr",
}

# Signed download URLs for recovery when public bucket reads fail
SIGNED_DOWNLOAD_EXPIRES_SECONDS = 60 * 60 * 24 * 7  # 7 days


class StorageError(Exception):
    pass


class StorageService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    def generate_presigned_upload(self, file_type: str, context: str) -> dict:
        if context not in ALLOWED_CONTEXTS:
            raise StorageError(f"Invalid context '{context}'. Must be one of {list(ALLOWED_CONTEXTS)}")
        if file_type not in EXTENSION_BY_MIME:
            raise StorageError(f"Unsupported file_type '{file_type}'")

        folder = ALLOWED_CONTEXTS[context]
        ext = EXTENSION_BY_MIME[file_type]
        date_path = datetime.utcnow().strftime("%Y/%m")
        object_key = f"{folder}/{date_path}/{uuid.uuid4()}.{ext}"

        # Supabase Storage: create_signed_upload_url returns a token-bearing PUT URL
        signed = self.client.storage.from_(self.bucket).create_signed_upload_url(object_key)

        public_url = self.client.storage.from_(self.bucket).get_public_url(object_key)
        if isinstance(public_url, str):
            public_url = public_url.strip().rstrip("?")

        result = {
            "upload_url": signed.get("signed_url") or signed.get("signedUrl"),
            "object_key": object_key,
            "public_url": public_url,
            "expires_in": 300,
        }
        if context == "visit_voice":
            result["max_duration_seconds"] = settings.MAX_VOICE_NOTE_SECONDS
            result["max_upload_bytes"] = settings.MAX_VOICE_UPLOAD_BYTES
        return result

    def object_key_from_public_url(self, url: str) -> str | None:
        """Extract storage object key from a public or authenticated Supabase URL."""
        trimmed = (url or "").strip()
        if not trimmed:
            return None
        parsed = urlparse(trimmed)
        path = parsed.path
        markers = (
            f"/storage/v1/object/public/{self.bucket}/",
            f"/storage/v1/object/sign/{self.bucket}/",
            f"/storage/v1/object/authenticated/{self.bucket}/",
        )
        for marker in markers:
            idx = path.find(marker)
            if idx >= 0:
                return path[idx + len(marker) :].lstrip("/")
        return None

    def create_signed_download_url(self, object_key: str, expires_in: int = SIGNED_DOWNLOAD_EXPIRES_SECONDS) -> str:
        signed = self.client.storage.from_(self.bucket).create_signed_url(object_key, expires_in)
        url = signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url")
        if not url:
            raise StorageError("Could not create signed download URL")
        return url


storage_service = StorageService()