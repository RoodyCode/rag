"""Central application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    bedrock_api_key: str
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    aws_region: str = "eu-central-1"
    embed_model: str = "BAAI/bge-m3"
    embed_dim: int = 1024
    table_name: str = "documents"
    llm_model: str = "openai.gpt-oss-20b-1:0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_namespace: str = "rag"
    ingest_queue_name: str = "ingestion"
    ingest_job_timeout_seconds: int = 1800
    ingest_result_ttl_seconds: int = 3600
    ingest_failure_ttl_seconds: int = 86400
    ingest_retry_max: int = 3
    ingest_worker_count: int = 2
    rerank_model: str = "BAAI/bge-reranker-large"
    rerank_top_n: int = 5
    similarity_top_k: int = 10


settings = Settings()
