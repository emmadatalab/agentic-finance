"""Content generation utilities leveraging retrieved snippets."""

from typing import List


def draft_response(query: str, snippets: List[str]) -> str:
    """Return a simple stitched response using snippets as grounding."""
    if not snippets:
        return f"No knowledge available yet for: {query}"
    joined = "\n".join(f"- {snippet}" for snippet in snippets)
    return f"Query: {query}\nGrounded points:\n{joined}"
