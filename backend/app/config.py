from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Investment Research API"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    database_path: Path = Field(
        default=Path("data/app.db"),
        validation_alias="DATABASE_PATH",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
