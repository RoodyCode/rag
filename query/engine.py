from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.llms.openai import OpenAI

from ingestion.config import settings
from ingestion.pipeline import build_embed_model, build_vector_store


def build_query_engine(similarity_top_k: int = 5) -> BaseQueryEngine:
    Settings.embed_model = build_embed_model()
    Settings.llm = OpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        **({"api_base": settings.openai_base_url} if settings.openai_base_url else {}),
    )

    vector_store = build_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    return index.as_query_engine(similarity_top_k=similarity_top_k)
