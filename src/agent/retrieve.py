"""Retrieval utilities for accessing indexed knowledge."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer

from .index import DEFAULT_BATCH_SIZE, DEFAULT_MODEL


@dataclass
class RetrievedChunk:
    """A retrieved chunk with score and metadata."""

    chunk_id: str
    doc_id: str
    source_path: str
    text: str
    title: str
    start: int
    end: int
    score: float

    def to_dict(self) -> dict:
        """Serialize the chunk to a JSON-friendly dict."""
        return asdict(self)


def retrieve_chunks(index_dir: Path, query: str, top_k: int = 3) -> List[RetrievedChunk]:
    """Embed a query and return the top matching chunks with metadata."""
    index_path = index_dir / "index.faiss"
    meta_path = index_dir / "meta.jsonl"
    if top_k <= 0 or not index_path.exists() or not meta_path.exists():
        return []

    metadata = _load_metadata(meta_path)
    if not metadata:
        return []

    index = faiss.read_index(str(index_path))
    if index.ntotal == 0:
        return []

    model_name = metadata[0].get("model_name", DEFAULT_MODEL)
    query_embedding = _embed_query(model_name, [query])
    limit = min(top_k, index.ntotal)
    distances, neighbors = index.search(query_embedding, limit)

    results: List[RetrievedChunk] = []
    for score, idx in zip(distances[0], neighbors[0]):
        if idx == -1 or idx >= len(metadata):
            continue
        entry = metadata[idx]
        results.append(
            RetrievedChunk(
                chunk_id=str(entry.get("chunk_id") or ""),
                doc_id=str(entry.get("doc_id") or ""),
                source_path=str(entry.get("source_path") or ""),
                text=str(entry.get("text") or ""),
                title=str(entry.get("title") or "Untitled"),
                start=int(entry.get("start") or 0),
                end=int(entry.get("end") or 0),
                score=float(score),
            )
        )
        if len(results) >= top_k:
            break
    return results


def retrieve_snippets(index_dir: Path, query: str, limit: int = 3) -> List[str]:
    """Embed a query and return the top matching chunks as decorated strings."""
    chunks = retrieve_chunks(index_dir=index_dir, query=query, top_k=limit)
    return [_format_snippet(chunk) for chunk in chunks]


def _embed_query(model_name: str, queries: Sequence[str]):
    model = SentenceTransformer(model_name or DEFAULT_MODEL)
    return model.encode(
        queries,
        batch_size=DEFAULT_BATCH_SIZE,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )


def _load_metadata(meta_path: Path) -> List[dict]:
    records: List[dict] = []
    with meta_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _format_snippet(chunk: RetrievedChunk) -> str:
    prefix = f"[{chunk.title}]"
    if chunk.source_path:
        prefix = f"[{chunk.title} — {chunk.source_path}]"
    snippet = chunk.text.strip()
    return f"{prefix} (score={chunk.score:.3f}) {snippet}"
