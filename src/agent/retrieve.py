"""Retrieval utilities for accessing indexed knowledge."""

from pathlib import Path
from typing import List


def retrieve_snippets(index_path: Path, query: str, limit: int = 3) -> List[str]:
    """Return simple matching snippets from the index file."""
    if not index_path.exists():
        return []
    with index_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    lowered_query = query.lower()
    matches = [line.strip() for line in lines if lowered_query in line.lower()]
    return matches[:limit]
