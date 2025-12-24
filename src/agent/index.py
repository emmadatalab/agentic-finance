"""Indexing utilities for turning ingested content into a searchable structure."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_BATCH_SIZE = 32


@dataclass
class IndexedChunk:
    """Represents a single chunk mapped into the vector index."""

    chunk_id: str
    text: str
    doc_id: str
    title: str
    source_path: str
    start: int
    end: int


def build_index(
    kb_path: Path,
    index_dir: Path,
    model_name: str = DEFAULT_MODEL,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Path:
    """Load KB JSONL, chunk content, embed, and persist a FAISS index plus metadata."""
    _validate_chunking(chunk_size, chunk_overlap)
    documents = _load_kb(kb_path)
    chunks = _chunk_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        raise ValueError(f"No text chunks produced from {kb_path}")

    model = SentenceTransformer(model_name)
    embeddings = _encode_chunks(model, [chunk.text for chunk in chunks], batch_size=batch_size)
    faiss_index = _build_faiss_index(embeddings)

    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "index.faiss"
    meta_path = index_dir / "meta.jsonl"

    faiss.write_index(faiss_index, str(index_path))
    _write_metadata(meta_path, chunks, model_name)

    return index_path


def _load_kb(kb_path: Path) -> List[dict]:
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base file not found at {kb_path}")
    records: List[dict] = []
    with kb_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _validate_chunking(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def _chunk_documents(
    documents: Iterable[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[IndexedChunk]:
    chunks: List[IndexedChunk] = []
    for doc in documents:
        text = str(doc.get("text") or "").strip()
        if not text:
            continue
        doc_id = str(doc.get("doc_id") or "")
        title = str(doc.get("title") or "")
        source_path = str(doc.get("source_path") or "")
        for idx, (chunk_text, start, end) in enumerate(_chunk_text(text, chunk_size, chunk_overlap)):
            chunk_id = f"{doc_id}-{idx}" if doc_id else f"chunk-{len(chunks)}"
            chunks.append(
                IndexedChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    doc_id=doc_id,
                    title=title,
                    source_path=source_path,
                    start=start,
                    end=end,
                )
            )
    return chunks


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[Tuple[str, int, int]]:
    segments: List[Tuple[str, int, int]] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        segment = text[start:end]
        segments.append((segment, start, end))
        if end == length:
            break
        start = end - chunk_overlap
    return segments


def _encode_chunks(model: SentenceTransformer, texts: Sequence[str], batch_size: int) -> np.ndarray:
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    # model.encode returns a numpy array but enforce float32 for FAISS compatibility
    return np.asarray(vectors, dtype="float32")


def _build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    if embeddings.size == 0:
        raise ValueError("No embeddings to index.")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def _write_metadata(meta_path: Path, chunks: Iterable[IndexedChunk], model_name: str) -> None:
    with meta_path.open("w", encoding="utf-8") as f:
        for position, chunk in enumerate(chunks):
            payload = {
                "position": position,
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "source_path": chunk.source_path,
                "text": chunk.text,
                "start": chunk.start,
                "end": chunk.end,
                "model_name": model_name,
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
