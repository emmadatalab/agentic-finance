"""Ingestion utilities for preparing raw knowledge base content."""

from pathlib import Path
from typing import Iterable, List


def discover_documents(base_path: Path) -> List[Path]:
    """Return a list of text-like documents under the base path."""
    if not base_path.exists():
        return []
    return [p for p in base_path.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md"}]


def load_documents(paths: Iterable[Path]) -> List[str]:
    """Load documents as strings."""
    documents = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            documents.append(f.read())
    return documents
