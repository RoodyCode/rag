import sys
import time


def main() -> None:
    args = sys.argv[1:]

    if args:
        questions = [" ".join(args)]
        interactive = False
    else:
        questions = []
        interactive = True

    from query.engine import build_query_engine  # deferred so config errors surface cleanly

    print("Building query engine…")
    engine = build_query_engine()
    print("Ready.\n")

    def ask(question: str) -> None:
        start = time.perf_counter()
        response = engine.query(question)
        elapsed = time.perf_counter() - start

        print(f"Answer: {response}\n")

        source_nodes = getattr(response, "source_nodes", [])
        if source_nodes:
            print(f"Sources ({len(source_nodes)}):")
            seen: set[str] = set()
            for node in source_nodes:
                fname = node.metadata.get("file_name") or node.metadata.get("file_path", "unknown")
                if fname not in seen:
                    seen.add(fname)
                    score = node.get_score()
                    score_str = f"  score={score:.3f}" if score is not None else ""
                    print(f"  • {fname}{score_str}")

        print(f"\n[{elapsed:.1f}s]")

    if interactive:
        print("Interactive mode — type your question and press Enter (Ctrl-C to quit).\n")
        try:
            while True:
                question = input("Question: ").strip()
                if not question:
                    continue
                ask(question)
                print()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
    else:
        ask(questions[0])


if __name__ == "__main__":
    main()
