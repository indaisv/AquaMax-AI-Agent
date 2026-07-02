"""Reusable utility helpers."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return str(uuid.uuid4())


def sanitize_input(text: str | None) -> str:
    """Sanitize user input: strip, normalize whitespace, basic XSS guard."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    # Basic XSS guard: strip script tags and dangerous attributes
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    return text


def extract_json(text: str) -> dict[str, Any] | None:
    """Extract a JSON object from text that may contain markdown fences."""
    # Try fenced code block first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    else:
        # Try bare JSON object
        match = re.search(r"(\{[\s\S]*\})", text)
        if match:
            text = match.group(1)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as Indian Rupees with comma separators."""
    return f"{currency}{amount:,.2f}"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def deduplicate_by_key(items: list[dict], key: str) -> list[dict]:
    """Deduplicate a list of dicts by a given key, preserving order."""
    seen = set()
    result = []
    for item in items:
        val = item.get(key)
        if val not in seen:
            seen.add(val)
            result.append(item)
    return result


def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d
