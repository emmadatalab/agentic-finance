"""Validation helpers for generated financial content."""

from __future__ import annotations

import re
from typing import List


_CITATION_PATTERN = re.compile(r"\[[^\[\]]+—[^\[\]]+\]")
_UNSUPPORTED_PREDICTION_PATTERN = re.compile(r"\bwill\s+(?:double|triple|skyrocket|explode|guarantee)\b", re.IGNORECASE)
_PROHIBITED_PHRASES = (
    "guaranteed profit",
    "guaranteed return",
    "risk-free",
)


def check_compliance(text: str) -> List[str]:
    """Return validation failures that should block publishing."""
    failures: List[str] = []
    lower_text = text.lower()

    for phrase in _PROHIBITED_PHRASES:
        if phrase in lower_text:
            failures.append(f"Prohibited promise detected: {phrase}.")

    if "predict" in lower_text or "prediction" in lower_text or _UNSUPPORTED_PREDICTION_PATTERN.search(text):
        failures.append("Unsupported predictions are not allowed.")

    if not _CITATION_PATTERN.search(text):
        failures.append("Missing citations for claims.")

    return failures


def validate_or_raise(text: str) -> None:
    """Raise a ValueError if validation fails."""
    failures = check_compliance(text)
    if failures:
        joined = "; ".join(failures)
        raise ValueError(f"Validation failed: {joined}")
