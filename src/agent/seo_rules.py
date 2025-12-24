"""SEO rules helpers for financial content."""

from typing import List


DEFAULT_KEYWORDS = ["finance", "investment", "risk management", "compliance"]


def apply_keywords(content: str, keywords: List[str] | None = None) -> str:
    """Append keywords for search optimization."""
    use_keywords = keywords or DEFAULT_KEYWORDS
    keyword_line = ", ".join(use_keywords)
    return f"{content}\n\nKeywords: {keyword_line}"
