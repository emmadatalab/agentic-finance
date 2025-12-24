"""Content generation utilities leveraging retrieved snippets."""

from __future__ import annotations

from textwrap import dedent
from typing import Iterable, List

from .retrieve import RetrievedChunk

STRICT_PROMPT_TEMPLATE = dedent(
    """
    You are a financial content writer producing a Markdown article about "{topic}".

    Rules:
    - Use ONLY the provided context; do not invent facts.
    - Every claim must include an inline citation in the form [{doc_id} — {source_path}].
    - If the context does not contain enough evidence, respond exactly with: Not enough evidence in KB
    - Keep the output as Markdown with a clear heading and bullet points.

    Context:
    {context_block}

    Output only the article.
    """
).strip()


def build_strict_prompt(topic: str, chunks: Iterable[RetrievedChunk]) -> str:
    """Render the strict prompt with contextual evidence."""
    context_block = "\n".join(_format_context_line(chunk) for chunk in chunks)
    if not context_block:
        context_block = "No evidence retrieved."
    return STRICT_PROMPT_TEMPLATE.format(topic=topic, context_block=context_block)


def generate_article(topic: str, chunks: List[RetrievedChunk]) -> str:
    """Generate a Markdown article grounded exclusively in retrieved context."""
    if not chunks:
        return "Not enough evidence in KB"

    lines: List[str] = [f"# {topic}", "", "## Evidence-backed points"]
    for idx, chunk in enumerate(chunks, start=1):
        citation = f"[{chunk.doc_id} — {chunk.source_path}]"
        snippet = " ".join(chunk.text.split())
        lines.append(f"{idx}. {snippet} {citation}")

    lines.append("")
    lines.append("## Source references")
    seen: set[tuple[str, str]] = set()
    for chunk in chunks:
        key = (chunk.doc_id, chunk.source_path)
        if key in seen:
            continue
        seen.add(key)
        title = chunk.title or "Untitled"
        lines.append(f"- {title} — {chunk.source_path} (doc_id: {chunk.doc_id})")
    return "\n".join(lines)


def draft_response(query: str, chunks: List[RetrievedChunk]) -> str:
    """Return a Markdown article answer grounded in retrieved KB chunks."""
    return generate_article(query, chunks)


def _format_context_line(chunk: RetrievedChunk) -> str:
    citation = f"[{chunk.doc_id} — {chunk.source_path}]"
    snippet = " ".join(chunk.text.split())
    return f"- {citation} {snippet}"
