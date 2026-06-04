# resumenexa

Resume Analyzer & ATS Optimizer API (FastAPI)

## What it does
This service:
- Accepts **resume uploads** (PDF, DOCX)
- Extracts resume text and builds a structured **resume JSON** (contact, summary, skills, experience, projects, etc.)
- Computes a deterministic **ATS-style score** and **missing keyword recommendations** against a job description (heuristic)
- Uses **Ollama** (local LLM) to generate **resume feedback** and **section rewrites** as JSON

## Tech stack
- Backend: **Python + FastAPI**
- Parsing: **PyMuPDF**, **pdfplumber**, **python-docx**
- Scoring: heuristic rules + `rapidfuzz`
- AI: **Ollama** (via HTTP)

> Note: PostgreSQL/SQLAlchemy/Alembic are in `requirements.txt`, but the current API endpoints shown in the repo are “local v1” and do not persist to a database yet.

## Endpoints
Base path comes from `app/api/routes.py`:
- `/resume/*` for resume-related actions
- `/job/*` for job-description matching
- `/ai/*` for LLM-based feedback/rewrite

### 1) Upload & parse resume
`POST /resume/upload`

**Request** (multipart/form-data):
- `file`: PDF or DOCX

**Response** (JSON):
- `filename`
- `parsed` (resume JSON)

### 2) Analyze resume with ATS scoring
`POST /resume/analyze`

**Request** (multipart/form-data):
- `file`: PDF or DOCX
- `job_description` (optional): string

**Response** (JSON):
- `filename`
- `parsed` (resume JSON)
- `scoring`:
  - `overall_score`
  - `structure_score`
  - `skills_score`
  - `experience_score`
  - `projects_score`
  - `keyword_breakdown` (matched/missing keywords)
  - `presence` (which sections were detected)

### 3) Match resume vs job description (keywords)
`POST /job/match`

**Request** (JSON body):
- `resume_json`: dict (the parsed resume JSON you got from `/resume/upload` or `/resume/analyze`)
- `job_description` (optional): string

**Response** (JSON):
- `match` with:
  - `match_score`
  - `matched_skills`
  - `missing_skills`
  - `recommendations`

### 4) AI feedback (Ollama)
`POST /ai/feedback`

**Request** (JSON body):
- `resume`: dict (parsed resume JSON)
- `job_description` (optional): string

**Response** (JSON):
- LLM output validated as JSON (best-effort extraction)
- Expected schema (see `app/ai/prompts.py`):
  - `strengths`: []
  - `weaknesses`: []
  - `missing_keywords`: []
  - `ats_improvement_suggestions`: []
  - `section_improvements`: { summary: [], experience: [], projects: [], skills: [] }

### 5) AI rewrite (Ollama)
`POST /ai/rewrite`

**Request** (JSON body):
- `resume_section`: string (text of the section you want rewritten)
- `section_type`: one of `summary|experience|projects|skills`
- `job_description` (optional): string

**Response** (JSON):
- Expected schema (see `app/ai/prompts.py`):
  - `section_type`: string
  - `rewritten_text`: string

## Setup
### 1) Requirements
- Python 3.10+
- Ollama running locally (for `/ai/*` endpoints)

### 2) Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment variables
The app uses Pydantic settings with an optional `.env` file (`app/core/config.py`). Common variables:
- `UPLOAD_DIR` (default: `./uploads`)
- `MAX_UPLOAD_MB` (default: `20`)
- `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `OLLAMA_MODEL` (default: `llama3.1:latest`)
- `LOG_LEVEL` (default: `INFO`)

### 4) Run
```bash
uvicorn app.main:app --reload --port 8000
```

## Usage examples (curl)
> Replace `localhost:8000` with your host/port.

### Upload resume
```bash
curl -X POST "http://localhost:8000/resume/upload" \
  -F "file=@/path/to/resume.pdf"
```

### Analyze resume (with job description)
```bash
curl -X POST "http://localhost:8000/resume/analyze" \
  -F "file=@/path/to/resume.pdf" \
  -F "job_description=Senior Python Backend Engineer"
```

### Match resume JSON vs job description
```bash
# 1) First call /resume/analyze or /resume/upload to get parsed resume JSON.
# 2) Then:
curl -X POST "http://localhost:8000/job/match" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_json": {"skills": ["python", "fastapi", "sql"]},
    "job_description": "Looking for Python/FastAPI/SQL experience"
  }'
```

### AI feedback
```bash
curl -X POST "http://localhost:8000/ai/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {"skills": ["python", "fastapi"]},
    "job_description": "Software Engineer with Python and API experience"
  }'
```

### AI rewrite
```bash
curl -X POST "http://localhost:8000/ai/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_section": "Managed APIs for internal systems...",
    "section_type": "experience",
    "job_description": "Build and maintain REST APIs and services"
  }'
```

## Notes / limitations
- Resume parsing uses **heuristics** (simple contact extraction, keyword-based skills, section header slicing).
- ATS scoring is deterministic and **heuristic** (not a real ATS engine).
- `/ai/*` endpoints depend on **Ollama** returning JSON; the code attempts to extract JSON even if wrapped in extra text.

## Project structure
- `app/main.py` – FastAPI app creation
- `app/api/endpoints/*` – HTTP routes
- `app/parsers/*` – PDF/DOCX parsing and resume JSON assembly
- `app/scoring/*` – ATS-style scoring and keyword matching
- `app/ai/*` – Ollama client and prompt templates

