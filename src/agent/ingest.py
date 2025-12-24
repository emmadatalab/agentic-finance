"""Ingestion utilities for preparing raw knowledge base content."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import importlib
from pathlib import Path
from typing import Iterable, List


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}


@dataclass
class IngestedDocument:
    """Structured representation of a processed document."""

    doc_id: str
    title: str
    source_path: str
    text: str
    created_at: str
    risk_level: str = "unknown"


def discover_documents(base_path: Path) -> List[Path]:
    """Return a list of supported documents under the base path."""
    if not base_path.exists():
        return []
    return [p for p in base_path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES]


def load_documents(paths: Iterable[Path]) -> List[str]:
    """Load documents as strings (text, markdown, and readable PDFs)."""
    documents = []
    for path in paths:
        if path.suffix.lower() == ".pdf":
            text = _extract_pdf_text(path)
            if text:
                documents.append(text)
            continue
        with path.open("r", encoding="utf-8") as f:
            documents.append(f.read())
    return documents


def ingest_knowledge_base(raw_dir: Path, output_path: Path) -> List[IngestedDocument]:
    """Transform raw KB files into a normalized JSONL file."""

    documents = []
    for path in discover_documents(raw_dir):
        text = _load_text(path)
        if not text:
            continue
        record = _build_document_record(path, raw_dir, text)
        documents.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")

    return documents


def _load_text(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        with path.open("r", encoding="utf-8") as f:
            text = f.read()
        return text.strip() or None
    if suffix == ".pdf":
        text = _extract_pdf_text(path)
        return text.strip() or None
    return None


def _extract_pdf_text(path: Path) -> str:
    pdf_reader = _get_pdf_reader()
    try:
        reader = pdf_reader(str(path))
    except Exception as exc:  # pragma: no cover - defensive logging path
        print(f"Skipping PDF {path}: unable to read ({exc})")
        return ""

    texts: List[str] = []
    for page_index, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception:  # pragma: no cover - defensive logging path
            page_text = ""
        if page_text.strip():
            texts.append(page_text)

    if not texts:
        print(f"Skipping PDF {path}: detected as scanned (no extractable text).")
        return ""

    return "\n".join(texts)


def _get_pdf_reader():
    """Return the PdfReader class, raising a clear error if unavailable."""
    spec = importlib.util.find_spec("pypdf")
    if spec is None:
        raise RuntimeError(
            "PDF ingestion requires the optional dependency 'pypdf'. "
            "Install it with `pip install pypdf` and rerun the ingest command."
        )
    module = importlib.import_module("pypdf")
    return module.PdfReader


def _build_document_record(path: Path, base_path: Path, text: str) -> IngestedDocument:
    relative_path = path.relative_to(base_path) if path.is_absolute() or base_path in path.parents else path
    doc_id = hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()
    created_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    title = path.stem.replace("_", " ").strip() or str(relative_path)
    return IngestedDocument(
        doc_id=doc_id,
        title=title,
        source_path=str(relative_path),
        text=text,
        created_at=created_at,
    )
