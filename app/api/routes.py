from fastapi import APIRouter

router = APIRouter()

from app.api.endpoints.resume import router as resume_router  # noqa: E402
from app.api.endpoints.job import router as job_router  # noqa: E402
from app.api.endpoints.ai import router as ai_router  # noqa: E402

router.include_router(resume_router, prefix="/resume", tags=["resume"])
router.include_router(job_router, prefix="/job", tags=["job"])
router.include_router(ai_router, prefix="/ai", tags=["ai"])

