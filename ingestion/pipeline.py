from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.node_parser.docling import DoclingNodeParser
from llama_index.readers.docling import DoclingReader
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

from ingestion.config import settings


def build_vector_store() -> PGVectorStore:
    url = make_url(settings.database_url)
    return PGVectorStore.from_params(
        database=url.database,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name=settings.table_name,
        embed_dim=settings.embed_dim,
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )


def load_documents(data_dir: Path):
    reader = DoclingReader(export_type=DoclingReader.ExportType.JSON)
    dir_reader = SimpleDirectoryReader(
        input_dir=str(data_dir),
        file_extractor={".pdf": reader},
        recursive=True,
    )
    return dir_reader.load_data(show_progress=True)


def build_pipeline(vector_store: PGVectorStore) -> IngestionPipeline:
    embed_model = OpenAIEmbedding(
        model=settings.embed_model,
        api_key=settings.openai_api_key,
    )
    return IngestionPipeline(
        transformations=[
            DoclingNodeParser(),
            embed_model,
        ],
        vector_store=vector_store,
        docstore=SimpleDocumentStore(),
        docstore_strategy=DocstoreStrategy.UPSERTS,
    )


def run(data_dir: Path) -> int:
    """Ingest all PDFs under *data_dir* into the vector store.

    Returns the number of nodes that were inserted/updated.
    """
    print(f"Loading PDFs from: {data_dir.resolve()}")
    documents = load_documents(data_dir)
    if not documents:
        print("No PDF documents found — nothing to ingest.")
        return 0

    print(f"Loaded {len(documents)} document(s). Building pipeline…")
    vector_store = build_vector_store()
    pipeline = build_pipeline(vector_store)

    nodes = pipeline.run(documents=documents, show_progress=True)
    print(f"Ingestion complete. {len(nodes)} node(s) inserted/updated.")
    return len(nodes)
