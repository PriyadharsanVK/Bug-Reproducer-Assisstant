<p align="center">
  <img src="docs/assets/bug_reproducer_banner.png" alt="Bug Reproducer Assistant" style="height: 8em" />
</p>

<h1 align="center">Bug Reproducer Assistant</h1>

<p align="center">
  <strong>AI Platform for Automated Bug Reproduction</strong><br/>
  Transform unstructured bug reports into deterministic, machine-verifiable reproduction artifacts.
</p>

<p align="center">
<a href="#-stack"><img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"></a>
<a href="#-stack"><img src="https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js"></a>
<a href="#-stack"><img src="https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge&logo=groq&logoColor=white" alt="Groq"></a>
<a href="#-stack"><img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
</p>

---

## What is Bug Reproducer Assistant?

**Bug Reproducer Assistant** is an AI-powered platform that takes unstructured bug reports — from GitHub Issues, Jira tickets, or manual submissions — and automatically produces:

- **Structured reproduction steps** with per-step confidence scores
- **Auto-generated test skeletons** (pytest / Jest) ready to drop into your test suite
- **Root cause hypotheses** ranked by probability
- **Strict Fact / Assumption / Unknown tripartition** to prevent hallucinated file paths or stack traces
- **Markdown + JSON handoff reports** for developer and QA engineers

The backend pipeline runs fully asynchronously via Python's built-in `asyncio`, powered by **Groq's ultra-low-latency LLM API** — no Redis, no Celery, no external queue infrastructure required.

---

## 🏗️ Architecture

```
Client (Next.js Web UI / curl / CI)
        │
        ▼
FastAPI Application Server  (apps/api)
  ├── POST /issues/ingest       → Persist bug report to PostgreSQL
  ├── POST /analysis/run        → Kick off asyncio pipeline
  ├── GET  /analysis/{id}       → Poll status & confidence score
  ├── GET  /analysis/{id}/report.md  → Fetch Markdown report
  └── POST /feedback/{id}       → Submit developer feedback
        │
        ▼  asyncio.create_task()
Analysis Pipeline  (apps/worker/tasks/run_analysis.py)
  ├── EntityExtractor   → Groq llama-3.3-70b  (Facts / Assumptions / Unknowns)
  ├── HallucinationGuard → Verifies file paths exist in raw issue text
  ├── ReproPlanner      → Groq llama-3.3-70b  (Step-by-step reproduction)
  ├── TestGenerator     → Groq deepseek-r1    (pytest / Jest skeletons)
  ├── HypothesisEngine  → Groq llama-3.3-70b  (Root cause candidates)
  ├── ConfidenceEngine  → Deterministic scoring formula
  └── ReportComposer    → Markdown + JSON report
        │
        ▼
PostgreSQL (issues, analysis_runs, reports, clarifications, test_artifacts)
```

---

## 🛠️ Stack

| Layer | Technology |
|---|---|
| **API Server** | FastAPI + Uvicorn (async) |
| **Frontend** | Next.js 14 + React 18 + Three.js |
| **LLM Provider** | Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `deepseek-r1-distill-llama-70b`) |
| **Database** | PostgreSQL 15 (via SQLAlchemy async + asyncpg) |
| **Task Execution** | Python `asyncio` (inline, no external queue) |
| **Containerization** | Docker + Docker Compose |

> **Note:** Redis and Celery are **not used** in this project. The analysis pipeline runs as an async task within the FastAPI process using `asyncio.create_task()`.

---

## ⚙️ Environment Setup

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/bug-reproducer-assistant.git
cd bug-reproducer-assistant

# Copy the example env file and fill in your values
cp .env.example .env
```

### 2. Required Environment Variables

Edit `.env` with the following:

```env
# MANDATORY — Get your key at https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Groq model configuration (defaults work out of the box)
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant
GROQ_MODEL_CODE=deepseek-r1-distill-llama-70b

# PostgreSQL connection
DATABASE_URL=postgresql+asyncpg://bug_assistant:your_password@localhost:5432/bug_reproducer_db

# Optional: GitHub token for fetching private repo context
GITHUB_TOKEN=your_github_personal_access_token_here
```

---

## 🚀 Running the Application

### Option A: Local Development (Recommended)

**Prerequisites:** Python 3.11+, Node.js 18+, PostgreSQL 15 running locally.

```bash
# 1. Install Python dependencies
pip install -e .

# 2. Start the API server
python -m uvicorn apps.api.main:app --reload --port 8000

# 3. In a new terminal — Start the web dashboard
cd apps/web
npm install
npm run dev
```

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Web Dashboard**: http://localhost:3000

### Option B: Docker Compose (PostgreSQL + API together)

```bash
docker-compose -f infra/docker/docker-compose.yml up --build
```

This starts:
- **PostgreSQL** on port `5432` (with schema auto-applied)
- **API Server** on port `8000`

---

## 🔌 API Reference

### Health Check
```bash
GET /health
```
```json
{ "status": "healthy", "service": "bug-reproducer-api", "primary_model": "llama-3.3-70b-versatile" }
```

### 1. Ingest a Bug Report
```bash
POST /issues/ingest
Content-Type: application/json

{
  "source": "github",          # "github" | "jira" | "manual"
  "source_id": "GH-409",
  "repository_url": "https://github.com/acme/user-service",
  "title": "KeyError when scope array is empty in /v1/auth/token",
  "body": "When requesting a JWT with scope=[], the service crashes with KeyError: default_scope",
  "raw_logs": "Traceback (most recent call last):\n  File 'services/token.py', line 88 ...\nKeyError: 'default_scope'"
}
```
**Response:** `201 Created` → `{ "issue_id": "<uuid>", "status": "ingested" }`

### 2. Trigger Analysis
```bash
POST /analysis/run
Content-Type: application/json

{ "issue_id": "<uuid-from-step-1>" }
```
**Response:** `202 Accepted` → `{ "run_id": "<uuid>", "status": "queued" }`

### 3. Poll Status
```bash
GET /analysis/<run_id>
```
**Response:** `{ "status": "completed", "overall_confidence": 0.87 }`

### 4. Fetch Generated Report
```bash
GET /analysis/<run_id>/report.md    # Markdown report
GET /analysis/<run_id>/report.json  # Structured JSON
```

### 5. Submit Clarifications (if status = `needs_input`)
```bash
POST /analysis/<run_id>/clarifications
{ "answers": [{ "question_id": "q1", "target_field": "runtime_version", "answer": "Python 3.11" }] }
```

---

## 🧪 Running Tests

```bash
pytest tests/test_bug_reproducer_api.py -v
```

To run the full evaluation suite against sample data:

```bash
python -m packages.evals.run_eval
```

---

## 📂 Project Structure

```
bug-reproducer-assistant/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── db/                 # SQLAlchemy models & session
│   │   ├── routes/             # issues, analysis, feedback endpoints
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # Core AI pipeline services
│   │   │   ├── groq_client.py       # Groq HTTP client
│   │   │   ├── model_router.py      # Multi-model routing logic
│   │   │   ├── extractor.py         # Entity extraction (Facts/Assumptions/Unknowns)
│   │   │   ├── guardrails.py        # Hallucination guard
│   │   │   ├── repro_planner.py     # Reproduction step planner
│   │   │   ├── test_generator.py    # Test skeleton generator
│   │   │   ├── hypothesis_engine.py # Root cause hypothesis engine
│   │   │   ├── confidence.py        # Deterministic confidence scoring
│   │   │   └── report_composer.py   # Markdown/JSON report composer
│   │   └── main.py             # FastAPI app entrypoint
│   ├── web/                    # Next.js 14 frontend dashboard
│   └── worker/
│       └── tasks/
│           └── run_analysis.py # Async analysis pipeline (asyncio)
├── packages/
│   ├── evals/                  # Evaluation metrics & benchmark dataset
│   ├── prompts/                # LLM system prompt templates
│   └── schemas/                # JSON Schema for report validation
├── infra/
│   ├── docker/                 # Dockerfile.api + docker-compose.yml
│   └── postgres/               # schema.sql + seed.sql
├── docs/                       # Architecture blueprints & documentation
├── tests/                      # pytest test suite
├── .env.example                # Environment variable template
└── pyproject.toml              # Python project metadata & dependencies
```

---

## 🔑 Key Design Decisions

### No Redis / No Celery
The analysis pipeline is triggered via Python's native `asyncio.create_task()` within the FastAPI process. This keeps the deployment footprint minimal — just **PostgreSQL + the API server**. For teams needing distributed workers at scale, the `_async_run_pipeline` function in `apps/worker/tasks/run_analysis.py` is ready to be wrapped in any task queue of your choice.

### Hallucination Guard
All file paths and stack traces that the LLM extracts as "Facts" are cross-referenced against the original issue body and raw logs. Anything not found in the source text is automatically demoted to "Inferred Assumptions" with a 0.50 confidence score.

### Deterministic Confidence Scoring
The overall confidence score is computed by a transparent, formula-based engine (not a second LLM call):
```
Overall Confidence = 0.35 × Fact_Completeness
                   + 0.25 × Step_Quality
                   + 0.20 × Log_Evidence_Presence
                   − 0.15 × Unknown_Penalty
                   + 0.05 × Consistency_Bonus
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).
