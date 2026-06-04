from __future__ import annotations

import docx


def extract_text_from_docx(path: str) -> str:
    d = docx.Document(path)
    parts: list[str] = []
    for p in d.paragraphs:
        if p.text and p.text.strip():
            parts.append(p.text.strip())
    return "\n".join(parts)

