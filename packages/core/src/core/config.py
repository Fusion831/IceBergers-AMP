"""Application Configuration using Pydantic Settings."""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General Environment
    PROJECT_NAME: str = "Antarctic Mission Intelligence Platform (AMIP) POC"
    APP_NAME: str = "AMIP Backend POC"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    MOCK_MODE: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./amip_dev.db"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///:memory:"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    USE_CELERY: bool = False

    # File Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path("data"))
    MODELS_DIR: Path = Field(default_factory=lambda: Path("models"))

    # Logging
    LOG_LEVEL: str = "INFO"

    # Operational Default Parameters
    DEFAULT_MIN_WATER_DEPTH_MARGIN_M: float = 3.0
    DEFAULT_MAX_NAVIGABLE_SIC: float = 0.85
    DEFAULT_ICEBERG_BUFFER_KM: float = 5.0
    DEFAULT_ICEBERG_ENSEMBLE_SIZE: int = 50
    DEFAULT_TIMESTEPS: List[int] = [0, 1, 7, 14, 30, 60, 90]

    # Default Reference Transect
    CAPE_TOWN_LAT: float = -33.9249
    CAPE_TOWN_LON: float = 18.4241
    BHARATI_LAT: float = -69.4068
    BHARATI_LON: float = 76.1953
    MAITRI_LAT: float = -70.7644
    MAITRI_LON: float = 11.7340

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_version(self) -> str:
        return self.APP_VERSION

    @property
    def mock_mode(self) -> bool:
        return self.MOCK_MODE

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def debug(self) -> bool:
        return self.DEBUG

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def host(self) -> str:
        return self.HOST

    @property
    def port(self) -> int:
        return self.PORT

    @property
    def cors_origins(self) -> List[str]:
        return self.CORS_ORIGINS


settings = Settings()
