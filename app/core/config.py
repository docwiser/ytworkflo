from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "ytworkflo"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["*"]
    DOWNLOAD_DIR: str = "/tmp/ytworkflo/downloads"
    AUDIO_DIR: str = "/tmp/ytworkflo/audio"
    SUBTITLE_DIR: str = "/tmp/ytworkflo/subtitles"
    THUMBNAIL_DIR: str = "/tmp/ytworkflo/thumbnails"
    MAX_BATCH_SIZE: int = 50
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    YTDLP_SOCKET_TIMEOUT: int = 30
    YTDLP_RETRIES: int = 3


settings = Settings()
