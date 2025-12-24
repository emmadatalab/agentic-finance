"""SEO rules helpers for financial content."""

from __future__ import annotations

from typing import List


def apply_seo_rules(content: str, keyword: str | None = None) -> str:
    """Apply structural SEO rules and keyword placement.

    Rules enforced:
    - Ensure the document contains an H1, at least one H2, and at least one H3 heading.
    - If a keyword is provided, ensure it appears in the first and last substantive paragraphs.
    """

    structured = _ensure_heading_structure(content)
    if keyword:
        structured = _ensure_keyword_placement(structured, keyword)
    return structured


def _ensure_heading_structure(content: str) -> str:
    lines = [line.rstrip() for line in content.strip().splitlines()]
    if not lines:
        lines = ["# Article"]

    first_nonempty = next((idx for idx, line in enumerate(lines) if line.strip()), None)
    if first_nonempty is None:
        lines = ["# Article"]
    elif not lines[first_nonempty].startswith("# "):
        title = lines[first_nonempty].lstrip("# ").strip() or "Article"
        lines.insert(0, f"# {title}")

    if not any(line.startswith("## ") for line in lines):
        lines.append("")
        lines.append("## Key Insights")

    if not any(line.startswith("### ") for line in lines):
        lines.append("")
        lines.append("### Details")

    return "\n".join(lines)


def _ensure_keyword_placement(content: str, keyword: str) -> str:
    paragraphs = _split_paragraphs(content)
    if not paragraphs:
        return content

    text_paragraph_indices = [
        idx
        for idx, para in enumerate(paragraphs)
        if para.strip() and not para.strip().startswith("#")
    ]
    if not text_paragraph_indices:
        return content

    first_idx = text_paragraph_indices[0]
    last_idx = text_paragraph_indices[-1]
    paragraphs[first_idx] = _inject_keyword(paragraphs[first_idx], keyword)
    paragraphs[last_idx] = _inject_keyword(paragraphs[last_idx], keyword)

    return "\n\n".join(paragraphs)


def _split_paragraphs(content: str) -> List[str]:
    paragraphs: List[str] = []
    current: List[str] = []
    for line in content.splitlines():
        if line.strip():
            current.append(line)
        else:
            if current:
                paragraphs.append("\n".join(current))
                current = []
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def _inject_keyword(paragraph: str, keyword: str) -> str:
    if keyword.lower() in paragraph.lower():
        return paragraph
    suffix = "" if paragraph.endswith((".", "!", "?")) else "."
    return f"{paragraph}{suffix} {keyword}"
