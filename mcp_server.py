from mcp.server.fastmcp import FastMCP

from query.engine import RetrieverQueryEngine, build_query_engine

_engine: RetrieverQueryEngine | None = None


def _get_engine() -> RetrieverQueryEngine:
    """Build the query engine once and reuse (lazy singleton). Avoids rebuild on every SSE connection."""
    global _engine
    if _engine is None:
        print("Building query engine…")
        _engine = build_query_engine()
        print("Query engine ready.")
    return _engine


mcp = FastMCP("Knowledge Base Assistant")


@mcp.tool()
def search_knowledge(query: str) -> str:
    """
    Search the user's private knowledge base.

    This tool must be called for:
    - personal data (e.g. account number, IBAN, salary)
    - contracts
    - invoices
    - financial information
    - any question about stored documents

    Do not answer these questions directly.
    Always call this tool first.
    """
    try:
        engine = _get_engine()
        response = engine.query(query)
        sources = [
            node.metadata.get("file_name") or node.metadata.get("file_path", "unknown")
            for node in getattr(response, "source_nodes", [])
        ]
        deduplicated = list(dict.fromkeys(sources))
        if deduplicated:
            return f"{response}\n\nSources: {', '.join(deduplicated)}"
        return f"{response}\n\nSources: (none)"
    except Exception as e:
        return f"Error querying knowledge base: {e!s}"


if __name__ == "__main__":
    mcp.run(transport="sse")
