import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.parsers.resume_parser import parse_resume
from app.scoring.ats_scoring import score_resume

router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
) -> JSONResponse:
    """Upload & extract text (local v1: no DB yet)."""
    content_type = file.content_type or ""
    ext = (Path(file.filename).suffix or "").lower()

    allowed = {".pdf", ".docx"}
    if ext not in allowed:
        return JSONResponse(status_code=400, content={"error": "Only PDF and DOCX are supported"})

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    out_path = upload_dir / file.filename

    # Store file
    raw = await file.read()
    if len(raw) > settings.max_upload_bytes:
        return JSONResponse(status_code=413, content={"error": "File too large"})
    out_path.write_bytes(raw)

    parsed = parse_resume(str(out_path), original_filename=file.filename)
    return JSONResponse(content={"filename": file.filename, "parsed": parsed})


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
) -> JSONResponse:
    """Extract resume + run deterministic ATS scoring (no DB yet)."""
    # Save to disk then parse
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    out_path = upload_dir / file.filename

    raw = await file.read()
    if len(raw) > settings.max_upload_bytes:
        return JSONResponse(status_code=413, content={"error": "File too large"})
    out_path.write_bytes(raw)

    parsed = parse_resume(str(out_path), original_filename=file.filename)
    scoring = score_resume(resume=parsed, job_description=job_description)

    return JSONResponse(content={"filename": file.filename, "parsed": parsed, "scoring": scoring})

