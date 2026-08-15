
# 🤖 AI Service Desk

An evidence-backed, RAG-powered support incident desk — built for the DigiPlus Technical Assessment.

Support engineers can create and manage incidents, get AI analysis grounded in a real knowledge base and historical tickets (not hard-coded rules), find similar past incidents, and record resolutions — all persisted in MongoDB with a Pinecone-backed semantic retrieval layer and Grok (xAI) as the reasoning LLM.

> 📄 Full architecture, data model, RAG pipeline and design rationale: [`DESIGN.md`](./DESIGN.md).

---

## Features

- 🎫 Create, list, filter, search, update and resolve incidents with a validated lifecycle (`OPEN → IN_PROGRESS → PENDING → RESOLVED → CLOSED`)
- 🤖 **AI Copilot**: one click analyzes an incident using Retrieval-Augmented Generation over a curated knowledge base + historical support tickets
- 📚 Knowledge base with realistic troubleshooting articles across 8 IT support categories
- 🔎 Similar/duplicate incident detection with configurable similarity thresholds
- 📌 Every AI recommendation is traceable to the specific KB article or historical ticket that supports it (evidence IDs, validated server-side — the model can never cite a source that wasn't actually retrieved)
- 📊 Dashboard analytics (status/priority/category breakdowns, resolution activity) via MongoDB aggregation
- ⚠️ Guardrails: the AI never invents IDs, never claims a resolution happened, never auto-changes priority/status, and treats retrieved content as untrusted data (not instructions) — a `AI_PROVIDER=mock` mode exists purely for tests/offline dev and is clearly labeled as such
- ✅ Backend test suite (pytest) — passes with zero real Mongo/Pinecone/Grok credentials

## Architecture

```
React + Vite + TS  ──REST──▶  FastAPI  ──async──▶ MongoDB Atlas (source of truth)
                                  │
                     ┌────────────┴────────────┐
                     ▼                          ▼
             Pinecone (semantic          Grok / xAI LLM
             retrieval only)             (structured JSON analysis)
```

See [`DESIGN.md`](./DESIGN.md) for the full RAG pipeline (chunking → retrieval → fallback broadening → rerank → grounded prompt → guardrail-validated structured output → persisted analysis).

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React 18, Vite, TypeScript, React Router, Axios, lucide-react |
| Backend | FastAPI, Pydantic v2, Motor (async MongoDB driver) |
| Database | MongoDB Atlas |
| Vector store | Pinecone (serverless, integrated embeddings — `llama-text-embed-v2`) |
| LLM | Grok (xAI), OpenAI-compatible API — model configurable via `LLM_MODEL` |
| Tests | pytest, pytest-asyncio (Mongo/Pinecone/LLM all mocked) |

---

## AI Configuration — Getting a Grok (xAI) API Key

**The key is never hard-coded anywhere in this repo.** It's read from an environment variable at startup.

1. Go to **https://console.x.ai** and sign in / create an account.
2. Open **API Keys** → **Create API Key**. Copy it immediately (shown once).
3. Optionally set a spending limit in the billing section.
4. Check **https://docs.x.ai** for the current model catalog before your demo — model availability/names change over time; don't assume a specific one is permanent.
5. Put the key in `backend/.env` (copied from `.env.example`, which is git-ignored for the real `.env`):

```
LLM_PROVIDER=grok
LLM_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.x.ai/v1
LLM_MODEL=grok-4-fast
```

For local development/tests without a key, set `AI_PROVIDER=mock` (see `.env.example`) — this returns a structurally valid but clearly mock-labeled response. **Never present mock output as real AI in a demo.**

Secrets hygiene: `.env` is git-ignored; only `.env.example` (blank placeholders) is committed; logs redact `LLM_API_KEY`, `MONGODB_URI`, `PINECONE_API_KEY`; CORS is restricted to `FRONTEND_URL`, not `*`.

---

## Environment Variables

Copy `.env.example` to `.env` at the repo root (and/or `backend/.env` — the backend loads `backend/.env`) and fill in:

```
MONGODB_URI=
MONGODB_DATABASE=ai_service_desk
PINECONE_API_KEY=
PINECONE_INDEX_NAME=ai-service-desk
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
LLM_PROVIDER=grok
LLM_API_KEY=
LLM_BASE_URL=https://api.x.ai/v1
LLM_MODEL=grok-4-fast
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
SIMILARITY_DUPLICATE_THRESHOLD=0.90
SIMILARITY_RELATED_THRESHOLD=0.75
AI_PROVIDER=grok
```

- **MongoDB Atlas**: create a free cluster at https://www.mongodb.com/cloud/atlas, add your IP to the network access list, create a DB user, and use the connection string as `MONGODB_URI`.
- **Pinecone**: create a free project/API key at https://app.pinecone.io — the index itself (`ai-service-desk`) is created automatically by `scripts/index_pinecone.py` if it doesn't exist.

---

## Installation & Setup

```bash
git clone <repo-url>
cd ai-service-desk

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

cp .env.example backend/.env     # then edit backend/.env with your real credentials
```

## Dataset Ingestion Pipeline

Run in order from the repo root (each step is idempotent / safe to re-run):

```bash
python backend/scripts/download_dataset.py     # pulls mindweave/help-desk-tickets CSVs into data/raw/
python backend/scripts/inspect_dataset.py      # prints schema, nulls, duplicates, distributions — sanity-check before importing
python backend/scripts/import_dataset.py       # normalizes tickets → incidents/comments/agents/categories in MongoDB
python backend/scripts/build_knowledge_base.py # seeds 10+ realistic knowledge articles into MongoDB
python backend/scripts/chunk_documents.py      # section-aware chunking of KB articles + historical tickets → data/processed/
python backend/scripts/index_pinecone.py       # creates/upserts vectors into Pinecone (idempotent, deterministic IDs)
python backend/scripts/verify_ingestion.py     # prints a ✅/❌ health report across Mongo + Pinecone + a live semantic query
```

To start over: `python backend/scripts/reset_database.py`.

## Running the Backend

```bash
cd backend
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs · Health check: http://localhost:8000/api/health

## Running the Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```
App: http://localhost:5173

## Running Tests

```bash
cd backend
AI_PROVIDER=mock pytest -q
```
All tests mock Pinecone and the LLM client — no real credentials or network access required.

## Containerization (optional)

```bash
cp .env.example .env   # fill in real credentials
docker compose up --build
```
MongoDB Atlas and Pinecone remain external managed services (not containerized) — only the backend and frontend are containerized.

---

## API Documentation

Interactive OpenAPI docs are auto-generated by FastAPI at `/docs` and `/redoc` once the backend is running. Key endpoints:

```
GET    /api/health
GET    /api/incidents                 (paginated + filterable: status, priority, category, service, team, assignee, date range, q)
POST   /api/incidents
GET    /api/incidents/{id}
PATCH  /api/incidents/{id}
DELETE /api/incidents/{id}
GET    /api/incidents/{id}/comments
POST   /api/incidents/{id}/comments
POST   /api/incidents/{id}/analyze     (RAG-driven AI analysis)
POST   /api/incidents/{id}/resolve
GET    /api/incidents/{id}/similar
GET    /api/knowledge
GET    /api/knowledge/{id}
POST   /api/knowledge
GET    /api/search
GET    /api/dashboard/stats
```

## AI Prompt Design & Guardrails

Summarized here; full detail in `DESIGN.md` §6 and `backend/app/ai/prompts.py` / `guardrails.py`:

- Retrieved KB/ticket content is explicitly framed as **untrusted reference data, not instructions** (prompt-injection defense).
- The model must return structured JSON validated against a Pydantic schema (`backend/app/ai/schemas.py`).
- Every `evidence_id` the model cites is checked against the actual retrieved evidence set server-side — unknown/invented IDs are stripped, never trusted.
- Confidence shown to the user is computed independently by the backend (`evidence_score` from retrieval quality/count/agreement), not the model's self-report alone.
- The AI never claims a resolution occurred, never auto-changes priority/status, and always carries a "verify before applying" disclaimer in the UI.

## Known Limitations

- No authentication/authorization layer (explicitly out of scope for the time budget; single-tenant, trusted-user assumption).
- Reranking uses a deterministic scoring formula (semantic score + category/service match + resolution presence + lexical overlap), not a learned cross-encoder.
- `/api/search` combines MongoDB text search with the same structured filters used elsewhere; deep semantic search is concentrated in `/analyze` and `/similar` where it adds the most value.
- Incident/article ID sequencing queries the current max ID rather than using an atomic counters collection — fine at this scale, would move to atomic counters in production.
- Dataset column-name mapping in `import_dataset.py` uses alias-matching against the Hugging Face CSV headers; re-run `inspect_dataset.py` after any dataset schema change to confirm the mapping still holds.

## Design Decisions

See `DESIGN.md` for the full rationale, including why Grok/xAI's OpenAI-compatible API was chosen (keeps the LLM client swappable behind one interface), why Pinecone integrated embeddings were used (guarantees ingestion and query never drift onto different embedding models), and why MongoDB is the sole source of truth while Pinecone is treated as a disposable, rebuildable retrieval index.

## Future Improvements

- Authentication/RBAC for multi-agent teams
- Real-time notifications (WebSocket) when an incident is reassigned or an SLA is at risk
- A learned reranker / cross-encoder for evidence ranking
- Conversational follow-up chat on top of a completed analysis (multi-turn Copilot)
- Atomic ID counters and optimistic concurrency control on incident updates
