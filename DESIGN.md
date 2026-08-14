# 🤖 AI Service Desk — Design & Implementation Document

**DigiPlus Technical Assessment — AI-Powered Service Desk**
Author: Harsh Kantham · Prepared: 14 Aug 2026

This document is the blueprint I will implement code against. It covers architecture, data model, the RAG pipeline, prompts/guardrails, API surface, environment configuration (including how to obtain and safely use a **Grok (xAI)** API key), and the build order for a 3.5‑hour assessment window.

---

## 1. Problem Restated

Support teams receive free‑text technical issues and need to triage, investigate, and resolve them quickly. The system must let a user create/manage incidents, get AI assistance grounded in real evidence (not hard‑coded rules), maintain a knowledge base, connect incidents to that knowledge base and to similar historical tickets, and record resolutions — with proper validation, error handling, and observability.

The differentiator: **evidence‑backed AI analysis via RAG**, not a raw "send ticket to LLM" call.

---

## 2. High‑Level Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐        ┌────────────────────┐
│   React + Vite SPA  │ <────> │   FastAPI backend (Py)   │ <────> │   MongoDB Atlas     │
│  (TypeScript, Axios)│  REST  │  services / api / ai     │  async │  (source of truth)  │
└─────────────────────┘        └───────────┬──────────────┘        └────────────────────┘
                                            │
                          ┌─────────────────┼───────────────────┐
                          │                                     │
                 ┌────────▼─────────┐                 ┌─────────▼─────────┐
                 │  Pinecone index    │                 │   Grok (xAI) LLM   │
                 │  "ai-service-desk" │                 │  chat.completions  │
                 │  ns: knowledge     │                 │  (structured JSON) │
                 │  ns: historical-   │                 └────────────────────┘
                 │      tickets       │
                 └────────────────────┘
```

**Data flow for AI analysis** (the core loop):

```
Incident → normalize → build retrieval query → Pinecone search
  (knowledge ns + historical-tickets ns, top-10 each)
  → metadata filter / fallback broadening → dedupe → lightweight rerank
  → top 5–8 evidence chunks, each given a stable evidence_id
  → grounded system+user prompt (evidence is DATA, not instructions)
  → Grok structured JSON response
  → validate schema (Pydantic) + validate every evidence_id actually exists
  → compute independent evidence_score (backend, not LLM self-report)
  → persist ai_analyses document in MongoDB
  → return analysis + evidence to UI, fully traceable
```

MongoDB is always the source of truth. Pinecone only ever stores small metadata + vector, enough to re‑locate the canonical Mongo document.

---

## 3. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | React Router, Axios, lucide-react icons, plain CSS (design tokens in `:root`) |
| Backend | FastAPI (Python 3.11+) | Pydantic v2, async lifespan for DB connections |
| Database | MongoDB Atlas | via `motor` (Async PyMongo driver) |
| Vector store | Pinecone (serverless) | one index `ai-service-desk`, namespaces `knowledge` / `historical-tickets` |
| Embeddings | Pinecone integrated inference — `llama-text-embed-v2`, cosine metric | same model for ingestion + query, never mixed |
| LLM | **Grok (xAI)** — `grok-4-fast` (configurable via `LLM_MODEL`) | OpenAI-compatible Chat Completions API at `https://api.x.ai/v1`, called with an OpenAI-SDK-compatible client or raw `httpx` |
| Testing | pytest + pytest-asyncio | Pinecone + LLM mocked, `AI_PROVIDER=mock` mode for local/dev/tests |
| Container | Docker Compose (optional) | backend, frontend, (Mongo/Pinecone stay managed cloud services) |

**Why Grok specifically:** xAI ships an OpenAI-compatible endpoint, so the same `AsyncOpenAI`-style client works by pointing `base_url` at `https://api.x.ai/v1` — this keeps the LLM client swappable (OpenAI, Groq, Grok, local) behind one thin `llm_client.py` interface, satisfying "AI must be a meaningful, non-hardcoded part of the solution" without locking the codebase to a single vendor SDK.

---

## 4. Getting a Grok (xAI) API Key — and Using It Safely

**Never hard-code this key.** It is read once at startup from an environment variable and never logged, returned in API responses, or committed to git.

### 4.1 Steps to obtain a key

1. Go to the xAI developer console: **https://console.x.ai** (sign in with an X/xAI account, or create one).
2. Open the **API Keys** section of the console.
3. Click **Create API Key**, give it a name (e.g. `ai-service-desk-dev`), and copy the key immediately — it is shown only once.
4. (Recommended) Set a spending limit / budget alert in the console's billing section so a bug can't run up cost.
5. Check **https://docs.x.ai** for the current model list and pricing — model names and limits change; the code should never assume a specific one is guaranteed available. As of this writing, fast/cost-efficient chat models in the `grok-4-fast` family are suitable for structured JSON tasks like this one; verify against the live docs before demo day.

### 4.2 Wiring it into the project (never hard-coded)

```
# backend/.env   (git-ignored; copy from .env.example)
LLM_PROVIDER=grok
LLM_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.x.ai/v1
LLM_MODEL=grok-4-fast
```

```python
# backend/app/core/config.py  (excerpt)
class Settings(BaseSettings):
    llm_provider: str = "grok"
    llm_api_key: str = Field(..., env="LLM_API_KEY")   # required, no default secret
    llm_base_url: str = "https://api.x.ai/v1"
    llm_model: str = "grok-4-fast"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

```python
# backend/app/ai/llm_client.py  (excerpt)
from openai import AsyncOpenAI   # xAI is OpenAI-compatible

def get_llm_client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
```

If `AI_PROVIDER=mock` (used in tests / no-key local dev), `llm_client.py` returns a deterministic mock implementation that produces a structurally valid `AIAnalysisResponse` — this is explicitly labeled in the UI as **not real AI** and is only for CI/tests, per the assessment's own instructions not to fake production behavior.

### 4.3 Security checklist

- `.env` is in `.gitignore`; only `.env.example` (with blank/placeholder values) is committed.
- Key is loaded once via `Settings` (pydantic-settings) and never re-read from request bodies.
- Structured logs redact `llm_api_key`, `mongodb_uri`, `pinecone_api_key` explicitly via a logging filter.
- CORS is restricted to `FRONTEND_URL`, not `*`.

---

## 5. Data Model (MongoDB)

Collections: `incidents`, `comments`, `agents`, `categories`, `knowledge_articles`, `ai_analyses`, `audit_events`, `ingestion_runs`.

### 5.1 `incidents`
```json
{
  "_id": "ObjectId",
  "incident_id": "INC-000001",
  "title": "VPN connection failure after password reset",
  "description": "...",
  "status": "open",
  "priority": "P3",
  "category": { "id": 3, "name": "Network & VPN", "service": "network" },
  "assignment": { "team": "network", "assignee_id": null },
  "source": { "type": "dataset", "dataset": "mindweave/help-desk-tickets", "record_id": "123" },
  "ai": { "last_analysis_id": null, "analyzed_at": null, "confidence": null },
  "resolution": { "root_cause": null, "description": null, "resolved_by": null, "resolved_at": null },
  "created_at": "ISODate", "updated_at": "ISODate"
}
```
Indexes: `incident_id` (unique), `status+created_at`, `priority+created_at`, `category.name+created_at`, `assignment.team+created_at`, `source.record_id`.

### 5.2 `comments`
Separate documents (not embedded), indexed on `incident_id+created_at`.

### 5.3 `knowledge_articles`
At least 10 realistic articles across: Access Management, Laptop/Endpoint, Network & VPN, Email & Collaboration, ERP/WMS, Printers & Devices, Security, Telephony, plus dedicated MFA / password-reset / account-lockout articles. Each has `symptoms`, `root_causes`, `troubleshooting_steps`, `resolution`, `escalation_conditions`, `version`.

### 5.4 `ai_analyses`
Stores `analysis_id`, `incident_id`, `prompt_version` (`service-desk-analysis-v1`), `model`, full structured response, `evidence` (list of evidence_ids with source refs), `confidence` (model + computed), `retrieval_count`, `latency_ms`, `created_at`.

### 5.5 `ingestion_runs`
Tracks each pipeline run: rows read, incidents created, chunks created, vectors upserted, errors — proof of a reproducible pipeline rather than manually copied data.

Full JSON shapes for every collection, plus the knowledge-chunk and ticket-chunk formats, are specified in section 6 and mirror the schemas given in the assessment brief exactly (evidence-ID format `KB-001::chunk-003`, `INC-000123::chunk-001`).

---

## 6. RAG Pipeline Detail

### 6.1 Chunking
- **Knowledge articles**: section-aware chunking (never split mid-step / mid-procedure), 300–500 tokens, 50–80 overlap. Each chunk text is prefixed with `Title / Category / Section / Symptoms` context so it's self-contained when retrieved in isolation.
- **Historical tickets**: one retrieval document per ticket built from `title + description + category + service + priority + resolution + filtered comments` (noise comments like "thanks"/"ok"/"done" are dropped by a short deny-list + length heuristic — this is a data-cleaning rule, not an AI classifier, so it doesn't violate "no hardcoded AI"). Target 350–600 tokens, 50–100 overlap, single chunk if it fits.
- Deterministic chunk IDs: `KB-001::chunk-000`, `INC-000123::chunk-000` — reruns of the pipeline never duplicate vectors (idempotent upsert keyed by this ID, no random UUIDs).

### 6.2 Pinecone
- One index `ai-service-desk`, cosine metric, integrated embedding (`llama-text-embed-v2`) so ingestion and query always use the identical model.
- Namespaces: `knowledge`, `historical-tickets`.
- Metadata per vector kept small: `document_id, document_type, category, service, priority?, chunk_index, source, title`. Never the full Mongo document.

### 6.3 Retrieval + fallback
1. Query built from incident title/description/category.
2. Search both namespaces, top 10 each, with metadata filter by category/service where known.
3. If filtered results are thin, progressively broaden: drop category filter → drop service filter → global search. (Never return empty just because the guessed category was wrong.)
4. Deduplicate by `document_id`.
5. Lightweight deterministic rerank combining semantic score, category/service match, presence of a resolution, and lexical overlap — this reranker only re-orders retrieved evidence; it never invents an answer.
6. Top 5–8 chunks go to the LLM, each tagged with its evidence_id.

### 6.4 Similar-incident detection
Cosine similarity against the `historical-tickets` namespace, bucketed by env-configurable thresholds:
```
SIMILARITY_DUPLICATE_THRESHOLD=0.90
SIMILARITY_RELATED_THRESHOLD=0.75
```
UI distinguishes "likely duplicate" vs "similar" vs not shown at all below the related threshold.

### 6.5 Prompting & guardrails
- **System prompt** explicitly states retrieved content is untrusted reference data, never instructions (prompt-injection defense), forbids inventing KB/incident IDs, forbids claiming a resolution happened, requires separating evidence vs inference vs uncertainty, and forbids auto-changing priority/status.
- **User prompt** is built from the current incident plus two clearly labeled evidence blocks (`HISTORICAL INCIDENT EVIDENCE`, `KNOWLEDGE BASE EVIDENCE`), each item tagged with its evidence_id.
- **Output** is a single structured JSON object validated against a Pydantic schema (`summary, category, priority, probable_causes[], recommended_actions[], similar_incidents[], knowledge_articles[], escalation_required, confidence, uncertainties[], final_recommendation`).
- **Guardrail pass after the LLM call**: every `evidence_ids` value returned by the model is checked against the actual retrieved-evidence set; unknown IDs are stripped, not trusted.
- **Confidence**: the model's self-reported confidence is treated only as a presentation signal. The backend independently computes an `evidence_score` from retrieval quality/count/agreement and classifies High/Medium/Low — this is the number actually shown as the primary confidence badge.
- If the LLM call fails or times out, the API returns `{"status": "ai_unavailable", "retryable": true}` — incident creation and the rest of the lifecycle never depend on AI succeeding.

---

## 7. API Surface

```
GET    /api/health
GET    /api/incidents                (paginated, filterable)
POST   /api/incidents
GET    /api/incidents/{id}
PATCH  /api/incidents/{id}
DELETE /api/incidents/{id}
GET    /api/incidents/{id}/comments
POST   /api/incidents/{id}/comments
POST   /api/incidents/{id}/analyze
POST   /api/incidents/{id}/resolve
GET    /api/incidents/{id}/similar
GET    /api/knowledge
GET    /api/knowledge/{id}
POST   /api/knowledge
GET    /api/search
GET    /api/dashboard/stats
```
Pagination: `page`/`page_size` (default 1/20, max 100), consistent envelope `{items, page, page_size, total, total_pages}`. Filtering by status/priority/category/service/team/assignee/date range/search uses indexed Mongo queries, never full-collection scans in Python.

Errors use a consistent envelope:
```json
{ "error": { "code": "INCIDENT_NOT_FOUND", "message": "Incident INC-123 was not found." } }
```

---

## 8. Incident Lifecycle & Resolution Rules

```
OPEN → IN_PROGRESS → PENDING → RESOLVED → CLOSED
```
Backward transitions (e.g. `CLOSED → IN_PROGRESS`) require an explicit reopen action, not an implicit PATCH. Marking `RESOLVED` requires `root_cause`, `resolution_description`, `resolved_by` — validated server-side (rule-based validation is explicitly allowed by the brief; it's state validation, not a fake AI classifier). The AI can *recommend* a resolution but the response schema and prompt explicitly forbid it claiming a resolution already happened.

---

## 9. Frontend Structure

Routes: `/` (dashboard), `/incidents`, `/incidents/new`, `/incidents/:id`, `/knowledge`, `/search`.

Incident detail is a two-column layout: left = incident facts/comments/timeline; right = **🤖 AI Copilot** panel (summary, classification, priority reasoning, probable causes, recommended actions with clickable evidence chips, similar incidents with similarity %, confidence bar, uncertainty callouts). API calls are centralized in `services/api.ts` + per-domain modules (`incidents.ts`, `ai.ts`, `knowledge.ts`, `dashboard.ts`); state lives in small custom hooks (`useIncidents`, `useIncident`, `useAIAnalysis`, `useKnowledge`, `useDashboardStats`) rather than Redux.

---

## 10. Environment Variables (`.env.example`)

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
`AI_PROVIDER=mock` switches to the deterministic mock LLM for tests/offline dev only.

---

## 11. Build Order (fits the 3.5h envelope)

1. Skeleton: FastAPI health + Mongo connection + project structure.
2. Dataset download/inspect/import scripts → `incidents`/`comments`/`agents`/`categories` populated from the Hugging Face dataset.
3. Incident/Comment/Knowledge CRUD APIs + validation.
4. Pinecone index setup, chunking scripts, ingestion script (idempotent), verification script.
5. Grok client, prompts, structured schema, guardrail validation, `/analyze` endpoint, similar-incidents endpoint.
6. React shell: dashboard, incident list, create incident, incident detail.
7. AI Copilot panel + evidence UI + knowledge base UI.
8. Resolution workflow + dashboard analytics + error/empty/loading states.
9. Tests (mocked Pinecone/LLM) + README + final demo run-through.

---

## 12. Known Trade-offs (up front)

- No auth/RBAC in the base build (out of scope for the time budget; noted as a future improvement).
- Reranking is a deterministic scoring formula, not a learned cross-encoder — appropriate for this scale and keeps latency low.
- Grok model name is configurable because xAI's available models change; the code never assumes one is permanently available and reads it from `LLM_MODEL`.
- Full 34k-row dataset ingestion is supported by the pipeline but the default demo run uses the smaller sample set for speed; both paths are identical code.

---

*Next artifact: full source tree implementation following this design, delivered as a downloadable project plus a README with setup/run/demo instructions.*
