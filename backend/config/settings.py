from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment variables expected by the app.

    The infra<->app contract is these NAMES only; keep in sync with the
    repo-root .env.example (mirrored by env.j2 in the infrastructure repo).
    Values are plain env vars at runtime -- the app knows nothing about
    how they are provisioned.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Default values used if none are found so the backend doesn't crash
    APP_ENV: str = "local"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "greener"

    # Potentially sensitive: no default so no prod value ever lives in code,
    # optional so the app still boots without a real database (SCRUM-114).
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
