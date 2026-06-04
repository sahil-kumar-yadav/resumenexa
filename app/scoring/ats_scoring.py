from __future__ import annotations

import math
import re
from typing import Any

from rapidfuzz import fuzz


def _tokenize(s: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9+#.\-]{2,}", s or "")]


def _section_presence(resume: dict[str, Any]) -> dict[str, bool]:
    return {
        "contact": bool(resume.get("email") or resume.get("phone") or resume.get("name")),
        "summary": bool(resume.get("summary")),
        "skills": bool(resume.get("skills")),
        "experience": bool(resume.get("experience")),
        "projects": bool(resume.get("projects")),
        "education": bool(resume.get("education")),
        "certifications": bool(resume.get("certifications")),
    }


def score_resume(resume: dict[str, Any], job_description: str | None = None) -> dict[str, Any]:
    presence = _section_presence(resume)

    # Structure score: 0-100
    structure_points = sum(1 for v in presence.values() if v)
    structure_score = int(structure_points / len(presence) * 100)

    # Keyword/skills coverage
    resume_skills = [s.lower() for s in (resume.get("skills") or [])]

    keyword_score = 0
    missing_keywords: list[str] = []
    matched_keywords: list[str] = []

    jd = job_description or ""
    if jd.strip():
        jd_tokens = set(_tokenize(jd))

        # Prefer skills from resume + common tech tokens in JD
        candidate_skills = sorted(jd_tokens)

        for s in resume_skills:
            if s in jd_tokens:
                matched_keywords.append(s)

        # Missing: take top frequent tokens that look tech-ish
        techish = [t for t in candidate_skills if any(ch.isalpha() for ch in t) and len(t) <= 20]
        # Sample subset for scoring stability
        techish = techish[:80]

        for t in techish:
            if t not in resume_skills and t in jd_tokens:
                # approximate match (for e.g. postgres/postgresql)
                if any(fuzz.partial_ratio(t, rs) >= 90 for rs in resume_skills):
                    continue
                missing_keywords.append(t)

        missing_keywords = missing_keywords[:15]

        coverage = (len(matched_keywords) + 1) / (len(matched_keywords) + len(missing_keywords) + 1)
        keyword_score = int(coverage * 100)
    else:
        # Without JD: score based on skills richness
        keyword_score = min(100, len(resume_skills) * 4)

    # Experience quality heuristic
    exp = resume.get("experience") or []
    action_verbs = ["built", "developed", "designed", "implemented", "led", "created", "improved", "optimized", "migrated", "deployed"]
    exp_text = "\n".join(exp).lower()
    verb_hits = sum(1 for v in action_verbs if v in exp_text)
    experience_score = int(min(100, (verb_hits / 6) * 100))

    # Projects quality heuristic
    proj = resume.get("projects") or []
    proj_text = "\n".join(proj).lower()
    metric_hits = len(re.findall(r"\b\d+%|\b\d+\b", proj_text))
    project_score = int(min(100, (metric_hits + len(proj)) * 6))

    overall_score = int(
        0.3 * structure_score
        + 0.35 * keyword_score
        + 0.2 * experience_score
        + 0.15 * project_score
    )

    return {
        "overall_score": overall_score,
        "structure_score": structure_score,
        "skills_score": keyword_score,
        "experience_score": experience_score,
        "projects_score": project_score,
        "keyword_breakdown": {
            "matched_keywords": matched_keywords[:20],
            "missing_keywords": missing_keywords,
            "keyword_density_score": keyword_score,
        },
        "presence": presence,
    }


def match_job_description(resume: dict[str, Any], job_description: str) -> dict[str, Any]:
    resume_skills = [s.lower() for s in (resume.get("skills") or [])]
    jd_tokens = set(_tokenize(job_description))

    matched = [s for s in resume_skills if s in jd_tokens]

    # missing: JD tech-ish tokens not in resume
    techish = [t for t in jd_tokens if len(t) <= 20]
    missing = []
    for t in techish:
        if t in resume_skills:
            continue
        if any(fuzz.partial_ratio(t, rs) >= 90 for rs in resume_skills):
            continue
        missing.append(t)

    missing = missing[:20]

    match_score = int((len(matched) + 1) / (len(matched) + len(missing) + 1) * 100)

    recommendations = []
    if job_description:
        if missing:
            recommendations.append(f"Add/mention these keywords: {', '.join(missing[:10])}")
        else:
            recommendations.append("Great keyword coverage. Focus on impact/metrics in experience.")

    return {
        "match_score": match_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "recommendations": recommendations,
    }

