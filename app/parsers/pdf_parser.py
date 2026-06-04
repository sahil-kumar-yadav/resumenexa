from __future__ import annotations

import pdfplumber
import fitz


def extract_text_from_pdf(path: str) -> str:
    # Attempt PyMuPDF first (fast). Fallback to pdfplumber.
    try:
        doc = fitz.open(path)
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n".join(parts)
    except Exception:
        with pdfplumber.open(path) as pdf:
            parts = []
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)

