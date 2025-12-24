"""Ingestion utilities for preparing raw knowledge base content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
import json
from pathlib import Path
from typing import Iterable, List, Tuple

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


@dataclass
class ProcessedDocument:
    """Normalized document structure stored in kb.jsonl."""

    doc_id: str
    title: str
    source_path: str
    text: str
    created_at: str
    risk_level: str = "medium"

    def to_json(self) -> str:
        """Serialize to a JSON line."""
        return json.dumps(
            {
                "doc_id": self.doc_id,
                "title": self.title,
                "source_path": self.source_path,
                "text": self.text,
                "created_at": self.created_at,
                "risk_level": self.risk_level,
            },
            ensure_ascii=False,
        )


def discover_documents(base_path: Path) -> List[Path]:
    """Return a list of supported documents under the base path."""
    if not base_path.exists():
        return []
    return [
        p
        for p in base_path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def _read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _read_pdf(path: Path) -> Tuple[str, bool]:
    """Return extracted PDF text and whether it appears scanned (no text)."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError("pypdf is required to ingest PDF files") from exc
    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            texts.append(page_text)
    full_text = "\n".join(texts).strip()
    is_scanned = full_text == ""
    return full_text, is_scanned


def extract_text(path: Path) -> str | None:
    """Extract text from a supported document. Returns None when empty or scanned."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _read_text_file(path)
    if suffix == ".pdf":
        text, is_scanned = _read_pdf(path)
        if is_scanned:
            return None
        return text
    return None


def load_documents(paths: Iterable[Path]) -> List[str]:
    """Load supported documents into plain-text strings, skipping empty results."""
    documents: List[str] = []
    for path in paths:
        text = extract_text(path)
        if text:
            documents.append(text)
    return documents


def build_processed_document(raw_path: Path, base_path: Path) -> ProcessedDocument | None:
    """Create a ProcessedDocument from a raw file. Returns None when text is missing."""
    text = extract_text(raw_path)
    if not text:
        return None
    relative = raw_path.relative_to(base_path)
    doc_hash = sha1(str(relative).encode("utf-8")).hexdigest()
    created_at = datetime.fromtimestamp(raw_path.stat().st_mtime).isoformat()
    title = raw_path.stem.replace("_", " ").strip().title() or "Untitled"
    return ProcessedDocument(
        doc_id=doc_hash,
        title=title,
        source_path=str(relative),
        text=text.strip(),
        created_at=created_at,
    )


def ingest_documents(base_path: Path, output_path: Path) -> Tuple[int, int]:
    """Process documents and write kb.jsonl. Returns (processed, skipped)."""
    documents = discover_documents(base_path)
    processed: List[ProcessedDocument] = []
    skipped = 0
    for doc_path in documents:
        processed_doc = build_processed_document(doc_path, base_path)
        if processed_doc is None:
            skipped += 1
            continue
        processed.append(processed_doc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in processed:
            f.write(record.to_json() + "\n")
    return len(processed), skipped
