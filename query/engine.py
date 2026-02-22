from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.llms.openai import OpenAI
from llama_index.retrievers.bm25 import BM25Retriever

from ingestion.config import settings
from ingestion.pipeline import build_docstore, build_embed_model, build_vector_store

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer based on the document context provided. "
    "When you can, give the specific information the user asked for; if it's not "
    "in the context, say so."
)


def build_query_engine(similarity_top_k: int | None = None) -> RetrieverQueryEngine:
    top_k = similarity_top_k if similarity_top_k is not None else settings.similarity_top_k

    Settings.embed_model = build_embed_model()
    llm = OpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        system_prompt=SYSTEM_PROMPT,
        **({"api_base": settings.openai_base_url} if settings.openai_base_url else {}),
    )
    Settings.llm = llm

    vector_store = build_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    vector_retriever = index.as_retriever(similarity_top_k=top_k)
    bm25_retriever = BM25Retriever.from_defaults(
        docstore=build_docstore(),
        similarity_top_k=top_k,
    )

    hybrid_retriever = QueryFusionRetriever(
        [vector_retriever, bm25_retriever],
        similarity_top_k=top_k,
        num_queries=1,
        mode="relative_score",
        use_async=False,
    )

    reranker = LLMRerank(
        top_n=settings.rerank_top_n,
        llm=llm,
        choice_batch_size=5,
    )

    return RetrieverQueryEngine.from_args(
        retriever=hybrid_retriever,
        node_postprocessors=[reranker],
        llm=llm,
    )
