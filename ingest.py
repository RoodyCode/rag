"""CLI entrypoint to enqueue PDF ingestion jobs."""

import sys
import time


def main() -> None:
    from ingestion.config import settings

    data_dir = settings.data_dir

    if not data_dir.exists():
        print(f"Error: data directory not found at {data_dir.resolve()}", file=sys.stderr)
        sys.exit(1)

    pdf_files = list(data_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {data_dir.resolve()}")
        print("Drop your PDFs into the data/ folder and re-run.")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF file(s):")
    for f in pdf_files:
        print(f"  • {f.relative_to(data_dir.parent)}")
    print()

    from ingestion.queue import enqueue_directory

    start = time.perf_counter()
    enqueued, skipped_existing = enqueue_directory(data_dir)
    elapsed = time.perf_counter() - start

    print(f"\nDone in {elapsed:.1f}s.")
    print(f"Enqueued: {enqueued} PDF job(s)")
    print(f"Skipped (already queued/known): {skipped_existing} PDF job(s)")
    print("Start workers with: uv run python worker.py")


if __name__ == "__main__":
    main()
