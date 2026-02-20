import sys
import time
from pathlib import Path


def main() -> None:
    data_dir = Path(__file__).parent / "data"

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

    from ingestion.pipeline import run  # deferred so config errors surface cleanly

    start = time.perf_counter()
    node_count = run(data_dir)
    elapsed = time.perf_counter() - start

    print(f"\nDone in {elapsed:.1f}s — {node_count} node(s) stored in PostgreSQL.")


if __name__ == "__main__":
    main()
