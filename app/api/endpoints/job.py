from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.scoring.ats_scoring import match_job_description

router = APIRouter()


@router.post("/match")
async def job_match(resume_json: dict, job_description: Optional[str] = None) -> JSONResponse:
    if not job_description:
        return JSONResponse(status_code=400, content={"error": "job_description is required"})
    match = match_job_description(resume=resume_json, job_description=job_description)
    return JSONResponse(content={"match": match})

