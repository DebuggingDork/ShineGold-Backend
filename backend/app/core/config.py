from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase Postgres
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str

    # Supabase Storage
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "shinegold-media"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ENVIRONMENT: str = "development"

    @property
    def database_url_direct_async(self) -> str:
        """Ensure the direct URL uses asyncpg (Supabase often provides postgresql://)."""
        url = self.DATABASE_URL_DIRECT
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()