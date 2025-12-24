"""Retrieval utilities for accessing indexed knowledge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer

from .index import DEFAULT_BATCH_SIZE, DEFAULT_MODEL


def retrieve_snippets(index_dir: Path, query: str, limit: int = 3) -> List[str]:
    """Embed a query and return the top matching chunks."""
    index_path = index_dir / "index.faiss"
    meta_path = index_dir / "meta.jsonl"
    if not index_path.exists() or not meta_path.exists():
        return []

    metadata = _load_metadata(meta_path)
    if not metadata:
        return []

    index = faiss.read_index(str(index_path))
    model_name = metadata[0].get("model_name", DEFAULT_MODEL)
    model = SentenceTransformer(model_name)
    query_embedding = model.encode(
        [query],
        batch_size=DEFAULT_BATCH_SIZE,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    distances, neighbors = index.search(query_embedding, min(limit, index.ntotal))

    results: List[str] = []
    for row_distances, neighbor_row in zip(distances, neighbors):
        for score, idx in zip(row_distances, neighbor_row):
            if idx == -1 or idx >= len(metadata):
                continue
            entry = metadata[idx]
            decorated = _format_snippet(entry, score)
            results.append(decorated)
            if len(results) >= limit:
                return results
    return results


def _load_metadata(meta_path: Path) -> List[dict]:
    records: List[dict] = []
    with meta_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _format_snippet(entry: dict, score: float) -> str:
    title = entry.get("title") or "Untitled"
    source = entry.get("source_path") or ""
    prefix = f"[{title}]"
    if source:
        prefix = f"[{title} — {source}]"
    snippet = entry.get("text", "").strip()
    return f"{prefix} (score={score:.3f}) {snippet}"
