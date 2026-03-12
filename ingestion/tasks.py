"""Worker task wrappers that execute ingestion pipeline functions."""

import time
from pathlib import Path

from ingestion.pipeline import process_pdf


def process_pdf_task(pdf_path_str: str) -> int:
    pdf_path = Path(pdf_path_str)
    start = time.perf_counter()
    node_count = process_pdf(pdf_path)
    elapsed = time.perf_counter() - start
    print(f"Finished task for {pdf_path} in {elapsed:.1f}s ({node_count} node(s)).")
    return node_count
