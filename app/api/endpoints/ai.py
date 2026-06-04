from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from app.ai.ollama_client import OllamaClient
from app.ai.prompts import (
    build_resume_feedback_prompt,
    build_section_rewrite_prompt,
)

router = APIRouter()


class FeedbackRequest(BaseModel):
    resume: dict
    job_description: str | None = None


class RewriteRequest(BaseModel):
    resume_section: str
    section_type: str  # summary|experience|projects|skills
    job_description: str | None = None


@router.post("/feedback")
async def resume_feedback(req: FeedbackRequest) -> JSONResponse:
    client = OllamaClient()
    prompt = build_resume_feedback_prompt(req.resume, req.job_description)
    data = await client.generate_json(prompt, response_schema="resume_feedback")
    return JSONResponse(content=data)


@router.post("/rewrite")
async def rewrite_section(req: RewriteRequest) -> JSONResponse:
    client = OllamaClient()
    prompt = build_section_rewrite_prompt(req.section_type, req.resume_section, req.job_description)
    data = await client.generate_json(prompt, response_schema="section_rewrite")
    return JSONResponse(content=data)

