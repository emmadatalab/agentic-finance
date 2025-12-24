"""Indexing utilities for turning ingested content into a searchable structure."""

from pathlib import Path
from typing import List


def build_index(documents: List[str], destination: Path) -> Path:
    """Persist a placeholder index file."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(documents)
    with destination.open("w", encoding="utf-8") as f:
        f.write(content)
    return destination
