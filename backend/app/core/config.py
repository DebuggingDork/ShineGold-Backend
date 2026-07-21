from urllib.parse import unquote, urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase Postgres
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    SUPABASE_DB_REGION: str = "ap-south-1"
    SUPABASE_POOLER_PREFIX: str = "aws-1"

    # Supabase Storage
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "shinegold-media"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- App ---
    ENVIRONMENT: str = "development"

    # Max distance (km) from executive home to farm for proximity-based assignment acceptance
    EXECUTIVE_ASSIGNMENT_RADIUS_KM: float = 70.0

    # Days after a completed visit before the farm becomes due for another visit
    FARM_VISIT_COOLDOWN_DAYS: int = 30

    # Voice notes: client auto-stops at this length; reject longer reported durations
    MAX_VOICE_NOTE_SECONDS: int = 150
    # Soft cap for visit voice uploads (~150s AAC/opus; WAV on web stays under this)
    MAX_VOICE_UPLOAD_BYTES: int = 8 * 1024 * 1024

    @property
    def asyncpg_connect_args(self) -> dict:
        """Supabase transaction pooler (pgbouncer) does not support prepared statements."""
        return {
            "ssl": "require",
            "statement_cache_size": 0,
        }

    @property
    def supabase_project_ref(self) -> str:
        host = urlparse(self.SUPABASE_URL).hostname or ""
        if host.endswith(".supabase.co"):
            return host.removesuffix(".supabase.co")
        return host

    def _pooler_async_url(self, source_url: str, port: int) -> str:
        """Supabase pooler host ({prefix}-REGION.pooler.supabase.com) resolves over IPv4."""
        parsed = urlparse(source_url)
        ref = self.supabase_project_ref
        host = f"{self.SUPABASE_POOLER_PREFIX}-{self.SUPABASE_DB_REGION}.pooler.supabase.com"
        return URL.create(
            drivername="postgresql+asyncpg",
            username=f"postgres.{ref}",
            password=unquote(parsed.password or ""),
            host=host,
            port=port,
            database="postgres",
        ).render_as_string(hide_password=False)

    def _needs_pooler_fixup(self, hostname: str | None) -> bool:
        if not hostname:
            return False
        if hostname.endswith(".pooler.supabase.com") and not hostname.startswith(
            ("aws-0-", "aws-1-")
        ):
            return True
        return hostname.startswith("db.")

    @property
    def database_url_async(self) -> str:
        """Runtime URL: transaction pooler (port 6543)."""
        parsed = urlparse(self.DATABASE_URL)
        if self._needs_pooler_fixup(parsed.hostname) or parsed.username == "postgres":
            return self._pooler_async_url(self.DATABASE_URL, parsed.port or 6543)
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def database_url_direct_async(self) -> str:
        """Migration URL: session pooler (port 5432).

        db.<ref>.supabase.co is often IPv6-only; Windows/Python DNS frequently
        cannot resolve it. Session pooler on the regional host works for Alembic.
        """
        parsed = urlparse(self.DATABASE_URL_DIRECT)
        if self._needs_pooler_fixup(parsed.hostname):
            return self._pooler_async_url(self.DATABASE_URL_DIRECT, 5432)
        url = self.DATABASE_URL_DIRECT
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()