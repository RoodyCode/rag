"""Ingestion pipeline primitives: loading, chunking, embedding, and storage writes."""

from pathlib import Path

from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.node_parser.docling import DoclingNodeParser
from llama_index.readers.docling import DoclingReader
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.storage.kvstore.redis import RedisKVStore
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url

from ingestion.config import settings


def build_redis_uri() -> str:
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def build_docstore() -> RedisDocumentStore:
    redis_kvstore = RedisKVStore(redis_uri=build_redis_uri())
    return RedisDocumentStore(redis_kvstore, namespace=settings.redis_namespace)


def build_vector_store() -> PGVectorStore:
    url = make_url(settings.database_url)
    return PGVectorStore.from_params(
        database=url.database,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name=settings.table_name,
        embed_dim=settings.embed_dim
    )


def list_pdf_files(data_dir: Path) -> list[Path]:
    return sorted(data_dir.rglob("*.pdf"))


def load_pdf_document(pdf_path: Path):
    reader = DoclingReader(export_type=DoclingReader.ExportType.JSON)
    file_reader = SimpleDirectoryReader(
        input_files=[str(pdf_path)],
        file_extractor={".pdf": reader},
    )
    return file_reader.load_data(show_progress=False)


def build_embed_model() -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=settings.embed_model)


def build_pipeline(vector_store: PGVectorStore) -> IngestionPipeline:
    hf_tokenizer = HuggingFaceTokenizer.from_pretrained(
        model_name=settings.embed_model, max_tokens=512
    )
    chunker = HybridChunker(
        tokenizer=hf_tokenizer,
        merge_peers=True,
    )
    return IngestionPipeline(
        transformations=[
            DoclingNodeParser(chunker=chunker),
            build_embed_model(),
        ],
        vector_store=vector_store,
        docstore=SimpleDocumentStore(),
        docstore_strategy=DocstoreStrategy.UPSERTS,
    )


def process_pdf(pdf_path: Path) -> int:
    """Ingest a single PDF and return inserted/updated node count."""
    print(f"Processing PDF: {pdf_path}")
    documents = load_pdf_document(pdf_path)
    if not documents:
        print(f"No parseable content for {pdf_path}. Skipping.")
        return 0

    vector_store = build_vector_store()
    pipeline = build_pipeline(vector_store)

    nodes = pipeline.run(documents=documents, show_progress=True)
    if not nodes:
        print(f"No nodes produced for {pdf_path}.")
        return 0

    docstore = build_docstore()
    docstore.add_documents(nodes)
    print(f"Ingested {len(nodes)} node(s) for {pdf_path}.")
    return len(nodes)


def run(data_dir: Path) -> int:
    """Ingest all PDFs under *data_dir* into the vector store sequentially.

    Returns the number of nodes that were inserted/updated.
    """
    print(f"Loading PDFs from: {data_dir.resolve()}")
    pdf_files = list_pdf_files(data_dir)
    if not pdf_files:
        print("No PDF documents found — nothing to ingest.")
        return 0

    total_nodes = 0
    for pdf_path in pdf_files:
        total_nodes += process_pdf(pdf_path)

    print(f"Ingestion complete. {total_nodes} node(s) inserted/updated.")
    return total_nodes
