from __future__ import annotations


def build_resume_feedback_prompt(resume: dict, job_description: str | None) -> str:
    jd_block = job_description or ""
    return f"""You are an expert resume reviewer and ATS optimizer.
Return ONLY valid JSON.

Resume JSON:
{resume}

Job Description:
{jd_block}

Tasks:
- Provide strengths (array)
- Provide weaknesses (array)
- Provide missing_keywords (array)
- Provide ats_improvement_suggestions (array)
- Provide section_improvements: object with keys [summary, experience, projects, skills], each value is array of suggestions.

Schema:
{{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_keywords": ["..."],
  "ats_improvement_suggestions": ["..."],
  "section_improvements": {{
    "summary": ["..."],
    "experience": ["..."],
    "projects": ["..."],
    "skills": ["..."],
  }}
}}
"""


def build_section_rewrite_prompt(section_type: str, resume_section: str, job_description: str | None) -> str:
    jd_block = job_description or ""
    return f"""Rewrite the following resume section to be recruiter-friendly AND ATS-friendly.
Return ONLY valid JSON.

Section type: {section_type}
Job Description:
{jd_block}

Original section:
{resume_section}

Guidelines:
- Use action verbs and specific outcomes
- Preserve meaning, but improve clarity
- Add relevant keywords when job description suggests them

Schema:
{{
  "section_type": "{section_type}",
  "rewritten_text": "..."
}}
"""

