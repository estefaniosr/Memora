"""Utilities for converting Confluence storage HTML to plain text."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def clean_confluence_html(html: str) -> str:
    """Return readable plain text while retaining basic line boundaries."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator="\n")
    lines = (re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines())
    cleaned = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()
