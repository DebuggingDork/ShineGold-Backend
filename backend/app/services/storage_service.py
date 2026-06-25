import uuid
from datetime import datetime

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
}


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

        return {
            "upload_url": signed["signed_url"],
            "object_key": object_key,
            "public_url": public_url,
            "expires_in": 300,
        }


storage_service = StorageService()