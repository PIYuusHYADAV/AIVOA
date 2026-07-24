# AIVOA — AI-Powered Customer Complaint Management System

Round 1 Full Stack Developer Assessment — pharmaceutical (API/FDF) manufacturing QMS.

An AI complaint intake workflow: a customer describes a problem in plain, vague language
(email, phone note, portal message, PDF/DOCX attachment) and an AI assistant extracts
structured fields onto the official Customer Complaint Log, flags missing mandatory data,
classifies severity/priority, checks for duplicates, and suggests root cause + CAPA — all
editable by the QA officer before saving.

---

## 1. Architecture

```
┌────────────────────────────┐        ┌──────────────────────────────────────────┐
│  FRONTEND (React + Redux)  │  HTTP  │  BACKEND (FastAPI)                        │
│                             │◄──────►│                                            │
│  Left:  Complaint Form      │        │  POST /api/extract/text                   │
│         (workflow rail +    │        │  POST /api/extract/file                   │
│          4 QMS sections)    │        │  POST /api/chat                           │
│                             │        │  CRUD /api/complaints                     │
│  Right: AI Chat Assistant   │        │                                            │
│         (upload / paste /   │        │  ┌──────────────────────────────────────┐ │
│          progress / chat /  │        │  │        LangGraph StateGraph          │ │
│          AI insights)       │        │  │                                      │ │
│                             │        │  │  extract → completeness_check →      │ │
│  Redux slices:               │        │  │  severity_priority → duplicate_check │ │
│    complaintSlice (fields,   │        │  │  → root_cause → capa → summary       │ │
│    AI confidence, insights)  │        │  │                                      │ │
│    chatSlice (messages,      │        │  │  Groq LLMs:                          │ │
│    extraction progress)      │        │  │   gemma2-9b-it   (primary, fast)     │ │
│                             │        │  │   llama-3.3-70b-versatile (fallback, │ │
│                             │        │  │   used for JSON-parse retries and    │ │
│                             │        │  │   the heavier reasoning nodes)       │ │
│                             │        │  └──────────────────────────────────────┘ │
│                             │        │                                            │
│                             │        │  Postgres/MySQL via SQLAlchemy             │
└────────────────────────────┘        └──────────────────────────────────────────┘
```

### Why this shape
- **One LangGraph pipeline, two entry points.** The exact same graph (`app/agents/graph.py`)
  runs whether the trigger was a fresh document upload/paste or a follow-up chat message that
  adds more detail ("actually the batch number is B-118"). This keeps extraction, severity,
  duplicate-check, root-cause and CAPA logic in one place instead of duplicating it between
  an "upload" path and a "chat" path.
- **Two-model Groq strategy.** `gemma2-9b-it` is fast/cheap and handles the bulk of the
  structured-JSON calls. `llama-3.3-70b-versatile` is used (a) as an automatic retry when the
  smaller model's JSON fails to parse, and (b) for the reasoning-heavy root-cause/CAPA/summary
  nodes where a larger model gives noticeably better QMS-style reasoning.
- **AI vs. official-record separation in the UI.** Any field the AI filled gets a small violet
  "AI" badge and tint until the user edits it — once a human touches a field it's treated as
  the authoritative value. This matters a lot in a regulated QMS context.

---

## 2. LangGraph workflow, node by node

| Node | Purpose |
|---|---|
| `extract` | Groq extracts the 11 form fields + per-field confidence from raw text (pasted / OCR'd doc). Merges with whatever is already on the form. |
| `completeness_check` | Flags which of the 5 mandatory fields (customer name, product name, batch/lot, complaint type, description) are still missing. |
| `severity_priority` | Classifies **Severity** (Critical / Major / Minor) and **Priority** (High / Medium / Low) using GxP/ICH-Q10-style risk reasoning. |
| `duplicate_check` | Compares product + batch + complaint type against the 25 most recent complaints in the DB; flags a likely duplicate above a similarity threshold. |
| `root_cause` | Suggests a preliminary root-cause category (5M+E: Man/Machine/Material/Method/Environment) — explicitly framed as a suggestion for the QA officer, not a determination. |
| `capa` | Drafts one corrective + one preventive action suggestion. |
| `summary` | Produces the plain-language summary, next steps, immediate precautions, and the chat message shown to the user. |

## 3. Bonus AI features implemented
- ✅ Complaint Completeness Checker
- ✅ AI Risk Classification (Severity + Priority)
- ✅ Duplicate Complaint Detection
- ✅ Root Cause Recommendation
- ✅ CAPA Recommendation
- ✅ Complaint Summary + Next Steps + Immediate Precautions
- ✅ Conversational follow-up: the chat can both add more complaint detail (re-runs the
  pipeline and updates the form live) and answer general questions ("why is this Critical?").

---

## 4. Setup

### Prerequisites
- Docker + Docker Compose
- A Groq API key: https://console.groq.com/keys
- (Only needed for Option B / local frontend dev) Python 3.11+, Node.js 18+

### Option A — Docker Compose (everything, one command)
```bash
cp .env.example .env        # then edit .env and set GROQ_API_KEY

docker compose up --build
```
This builds and runs the full stack:

| Service | URL | What it is |
|---|---|---|
| `frontend` | http://localhost:3000 | React app, built and served via nginx; nginx reverse-proxies `/api/*` to `backend` |
| `backend` | http://localhost:8000 | FastAPI + LangGraph; `/docs` for Swagger UI |
| `postgres` | localhost:5432 | Postgres 16, db `aivoa_complaints`, user/pass `postgres`/`postgres`, persisted in the `aivoa_pg_data` volume |
| `adminer` | http://localhost:8080 | Optional DB browser (server: `postgres`, user/pass `postgres`/`postgres`, db `aivoa_complaints`) |

Notes:
- `backend`'s Dockerfile runs `uvicorn --reload` and the compose file bind-mounts `./backend/app`
  into the container, so backend code edits take effect immediately without rebuilding.
- `frontend` is a **production build** served by nginx (no hot reload) — for active frontend
  development use Option B's `npm run dev` instead, which has instant hot-reload.
- Tables auto-create on backend startup — `backend` waits for `postgres`'s healthcheck before
  starting, so there's no manual migration step.
- Tear down: `docker compose down` (add `-v` to also wipe the Postgres data volume).
- Rebuild after changing dependencies: `docker compose up --build`.

### Option B — Manual / local dev (faster frontend iteration)
Start just Postgres (and Adminer) via Docker, run backend and frontend natively:
```bash
docker compose up -d postgres adminer
```

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set GROQ_API_KEY
# DATABASE_URL already defaults to the docker-compose Postgres above (localhost:5432) --
# no change needed unless you changed the compose credentials/ports.

uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs` (FastAPI auto-generated Swagger UI).

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Vite proxies `/api/*` to `http://localhost:8000` (see
`vite.config.js`), so no CORS setup is needed in dev.

### Demo content
`backend/sample_complaints/` has three ready-to-use vague, realistic complaint texts
(packaging/minor, broken-seal/major, adverse-event/critical) — paste their contents into the
chat panel or save as `.txt` and drag-and-drop them to see the full pipeline run, including
severity classification and duplicate detection (submit sample 3 twice to see the duplicate
flag trigger).

---

## 5. Project structure
```
docker-compose.yml       Full stack: postgres, adminer, backend, frontend
.env.example              Root env for docker-compose (GROQ_API_KEY, model overrides)

backend/
  Dockerfile               Backend container image
  .dockerignore
  app/
    main.py              FastAPI app, CORS, startup (creates tables)
    config.py             Settings (env vars)
    db.py                 SQLAlchemy engine/session
    models.py              Complaint ORM model
    schemas.py             Pydantic request/response models
    agents/
      state.py             LangGraph state shape
      nodes.py             All 7 pipeline nodes + prompts
      graph.py             StateGraph wiring
    llm/
      groq_client.py       Groq wrapper (primary + fallback model, JSON parsing)
      ingest.py            PDF/DOCX/EML/TXT -> plain text
    routers/
      extract.py           POST /api/extract/text, /api/extract/file
      chat.py              POST /api/chat
      complaints.py        CRUD /api/complaints
  sample_complaints/       Demo complaint texts
  requirements.txt
  .env.example

frontend/
  Dockerfile               Multi-stage build (vite build -> nginx)
  nginx.conf                Serves SPA + reverse-proxies /api to backend
  .dockerignore
  src/
    App.jsx                Two-panel layout + header
    components/
      ComplaintForm.jsx     Left panel: 4 QMS sections + workflow rail
      ChatAssistant.jsx     Right panel: upload/paste/progress/chat/AI insights
      formConfig.js          Single source of truth for field metadata + sections
    store/
      complaintSlice.js      Form fields, AI confidence, insights, save state
      chatSlice.js            Chat messages, extraction progress
      store.js
    api/client.js            Fetch wrappers for all backend endpoints
    styles/
      tokens.css              Design tokens (color/radius/shadow)
      app.css                 Component styles
  index.html                Google Inter font import
  package.json
  vite.config.js
```

---

## 6. Design notes
The left-hand **workflow rail** (numbered dots connecting the 4 form sections, filling in
teal as each section's fields are populated) is the one deliberate signature element: it
turns the reference UI's static numbered headers into a live progress indicator that mirrors
what the LangGraph pipeline is actually doing behind the scenes — origin/customer, then
product/batch, then complaint detail, then assessment. AI-filled fields get a small violet
tint + badge so a QA reviewer can see at a glance which values came from the model vs. a human,
which matters for an auditable QMS record.

## 7. What's intentionally out of scope (per assignment)
- Production-grade OCR/document parsing (assignment explicitly says not required — native
  text-layer PDF/DOCX/EML/TXT is supported).
- Authentication/roles, since the assignment focuses on the AI intake workflow itself.
- A vector DB for duplicate detection — a lightweight field-similarity heuristic against
  recent complaints is used instead, which is sufficient for the demo scale and is called out
  in the code as the place to swap in embeddings for production.
