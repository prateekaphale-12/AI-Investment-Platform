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

    # LLM Provider Settings
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", validation_alias="OPENAI_MODEL")
    
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", validation_alias="GROQ_MODEL")
    
    # News API Keys (free tiers)
    alpha_vantage_key: str = Field(default="", validation_alias="ALPHA_VANTAGE_KEY")
    newsapi_key: str = Field(default="", validation_alias="NEWSAPI_KEY")
    finnhub_key: str = Field(default="", validation_alias="FINNHUB_KEY")
    
    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24, validation_alias="JWT_EXPIRE_MINUTES")

    database_path: Path = Field(
        default=Path("data/app.db"),
        validation_alias="DATABASE_PATH",
    )
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    postgres_db: str = Field(default="ai_investment", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="ai_app", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="Cr7m10p7!!", validation_alias="POSTGRES_PASSWORD")
    postgres_port: int = Field(default=5433, validation_alias="POSTGRES_PORT")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
