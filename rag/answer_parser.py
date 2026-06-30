"""Convert a Markdown-like RAG answer into safe presentation data."""

from __future__ import annotations

import re
from typing import Any

SECTION_TITLES = (
    "Resumo da nova demanda",
    "Projetos antigos mais semelhantes",
    "Evidências encontradas nos documentos",
    "O que pode ser reaproveitado",
    "Possível estrutura inicial do novo projeto",
    "Riscos e cuidados",
    "Perguntas para próxima reunião",
    "Próximos passos recomendados",
    "Fontes consultadas",
)

TITLE_PATTERNS = (
    r"Resumo da nova demanda",
    r"Projetos antigos mais semelhantes",
    r"Evidências encontradas(?: nos documentos)?",
    r"O que pode ser reaproveitado",
    r"Possível estrutura inicial(?: do novo projeto)?",
    r"Riscos e cuidados",
    r"Perguntas para (?:a )?próxima reunião",
    r"Próximos passos(?: recomendados)?",
    r"Fontes consultadas",
)


def _clean_inline(value: str) -> str:
    value = re.sub(r"!\[([^]]*)]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", value)
    value = re.sub(r"(`{1,3}|\*{1,2}|_{1,2}|~~)", "", value)
    return re.sub(r"[ \t]+", " ", value).strip(" \t:-")


def _content_parts(content: str) -> tuple[list[str], list[str]]:
    content = re.sub(r"\s+-\s+(?=[A-ZÀ-Ú0-9*])", "\n- ", content)
    paragraphs: list[str] = []
    items: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        bullet = re.match(r"^(?:[-*•]|\d+[.)])\s+(.+)$", line)
        cleaned = _clean_inline(bullet.group(1) if bullet else line)
        if not cleaned:
            continue
        (items if bullet else paragraphs).append(cleaned)
    return paragraphs, items


def parse_answer_sections(answer: str) -> list[dict[str, Any]]:
    """Return ordered sections without passing generated HTML to the browser."""
    if not answer or not answer.strip():
        return []

    markers: list[tuple[int, int, int, str]] = []
    for number, (title, title_pattern) in enumerate(
        zip(SECTION_TITLES, TITLE_PATTERNS, strict=True), start=1
    ):
        numbered_pattern = re.compile(
            rf"(?:^|\n|\s)\#{{0,6}}\s*{number}\s*[.)-]\s*"
            rf"{title_pattern}\s*:?[ \t]*",
            re.IGNORECASE,
        )
        standalone_pattern = re.compile(
            rf"^[ \t]*(?:\#{{1,6}}[ \t]*)?(?:[-*•][ \t]*)?"
            rf"{title_pattern}\s*:?[ \t]*$",
            re.IGNORECASE | re.MULTILINE,
        )
        match = numbered_pattern.search(answer) or standalone_pattern.search(answer)
        if match:
            markers.append((match.start(), match.end(), number, title))

    if not markers:
        paragraphs, items = _content_parts(answer)
        return [{"number": 1, "title": "Análise gerada", "paragraphs": paragraphs, "items": items}]

    markers.sort()
    sections: list[dict[str, Any]] = []
    for index, (_, content_start, number, title) in enumerate(markers):
        content_end = markers[index + 1][0] if index + 1 < len(markers) else len(answer)
        paragraphs, items = _content_parts(answer[content_start:content_end])
        sections.append(
            {
                "number": number,
                "title": title,
                "paragraphs": paragraphs,
                "items": items,
            }
        )
    return sections
