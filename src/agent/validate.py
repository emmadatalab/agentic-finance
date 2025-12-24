"""Validation helpers for generated financial content."""

from typing import List


def check_compliance(text: str) -> List[str]:
    """Return warnings that would need human review."""
    warnings: List[str] = []
    if "guaranteed" in text.lower():
        warnings.append("Avoid promising guaranteed returns.")
    if len(text.split()) < 20:
        warnings.append("Content may be too short to be useful.")
    return warnings
