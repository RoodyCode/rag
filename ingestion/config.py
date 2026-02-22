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
    embed_model: str = "BAAI/bge-m3"
    embed_dim: int = 1024
    table_name: str = "documents"
    llm_model: str = "gpt-4o-mini"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_namespace: str = "rag"
    rerank_model: str = "BAAI/bge-reranker-large"
    rerank_top_n: int = 5
    similarity_top_k: int = 10


settings = Settings()
