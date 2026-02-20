from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    openai_api_key: str
    openai_base_url: str | None = None
    embed_model: str = "text-embedding-3-small"
    embed_dim: int = 1536
    table_name: str = "documents"


settings = Settings()
