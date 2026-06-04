from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.docx_parser import extract_text_from_docx
from app.utils.text import normalize_text


SECTION_HINTS = {
    "summary": ["summary", "professional summary", "profile"],
    "skills": ["skills", "technical skills", "core competencies"],
    "experience": ["experience", "work experience", "employment"],
    "projects": ["projects", "project"],
    "education": ["education", "academics", "university", "college"],
    "certifications": ["certifications", "certification", "licenses", "license"],
}


def _extract_contact(text: str) -> dict[str, str | None]:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}", text)

    # Very lightweight name heuristic: first non-empty line with letters
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = None
    for ln in lines[:10]:
        if re.search(r"[A-Za-z]", ln) and len(ln) <= 45:
            # avoid emails
            if "@" not in ln:
                name = ln
                break

    return {"name": name, "email": email_match.group(0) if email_match else None, "phone": phone_match.group(0) if phone_match else None}


def _extract_skills(text: str) -> list[str]:
    # Heuristic: look for skills-like sections; fallback to keyword bank scan.
    normalized = normalize_text(text)

    keyword_bank = [
        "python",
        "fastapi",
        "django",
        "flask",
        "sql",
        "postgres",
        "postgresql",
        "redis",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "react",
        "next.js",
        "javascript",
        "typescript",
        "tailwind",
        "html",
        "css",
        "pydantic",
        "sqlalchemy",
        "alembic",
        "pytest",
        "git",
        "ci/cd",
        "rest",
        "graphql",
        "nlp",
        "llm",
        "gemini",
        "ollama",
        "openai",
    ]

    found = []
    for kw in keyword_bank:
        if kw in normalized:
            found.append(kw)

    # If none found, extract frequent proper nouns-ish tokens (fallback)
    if not found:
        tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9+#._-]{1,}\b", text)
        freq: dict[str, int] = {}
        for t in tokens:
            tt = t.lower()
            if 2 < len(tt) < 25:
                freq[tt] = freq.get(tt, 0) + 1
        found = [k for k, v in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:12]]

    # de-dup preserving order
    seen = set()
    out: list[str] = []
    for s in found:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return out[:20]


def parse_resume(file_path: str, original_filename: str) -> dict[str, Any]:
    if original_filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif original_filename.lower().endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")

    contact = _extract_contact(text)
    skills = _extract_skills(text)

    # Simple section extraction: grab lines around section headers.
    sections = {k: "" for k in SECTION_HINTS.keys()}
    lower_lines = [ln.strip() for ln in text.splitlines()]

    # Find indices for each header
    header_to_section: dict[int, str] = {}
    for i, ln in enumerate(lower_lines):
        l = ln.lower()
        for section, hints in SECTION_HINTS.items():
            if any(h in l for h in hints):
                header_to_section[i] = section
                break

    # Slice until next header
    header_idxs = sorted(header_to_section.keys())
    for idx_pos, start in enumerate(header_idxs):
        section = header_to_section[start]
        end = header_idxs[idx_pos + 1] if idx_pos + 1 < len(header_idxs) else len(lower_lines)
        snippet = "\n".join([x for x in lower_lines[start:end] if x.strip()])
        sections[section] = snippet

    def _bullets_from_block(block: str) -> list[str]:
        items: list[str] = []
        for ln in block.splitlines():
            if re.match(r"^\s*([•\-*]|\d+\.|\u2022)\s+", ln.strip()):
                items.append(re.sub(r"^\s*([•\-*]|\d+\.|\u2022)\s+", "", ln.strip()))
        # fallback: sentences
        if not items:
            sentences = [s.strip() for s in re.split(r"[\n\.]", block) if s.strip()]
            items = sentences[:8]
        return items[:12]

    summary = "\n".join(sections["summary"].splitlines()[:20]).strip() if sections["summary"] else ""

    experience = _bullets_from_block(sections["experience"])
    projects = _bullets_from_block(sections["projects"])
    education_items = _bullets_from_block(sections["education"])
    cert_items = _bullets_from_block(sections["certifications"])

    return {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education_items,
        "certifications": cert_items,
        "raw_text_excerpt": text[:5000],
    }

