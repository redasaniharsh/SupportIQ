# 🤖 AI Service Desk

> **Evidence-backed, RAG-powered IT support incident management platform**

An AI-powered Service Desk built for the **DigiPlus Technical Assessment** that helps support engineers create, manage, analyze, and resolve technical incidents using **Retrieval-Augmented Generation (RAG)**.

The system combines a curated knowledge base, historical support tickets, semantic retrieval through **Pinecone**, structured reasoning with **Grok (xAI)**, and **MongoDB** as the system of record.

Unlike rule-based support systems, AI recommendations are grounded in retrieved evidence and validated server-side before being presented to users.

> **Architecture & Design:** See [`DESIGN.md`](./DESIGN.md) for the complete architecture, data model, RAG pipeline, chunking strategy, retrieval flow, guardrails, and design decisions.

---

## ✨ Key Features

### 🎫 Incident Management

* Create, view, update, search, filter, and delete incidents
* Validated incident lifecycle:
  `OPEN → IN_PROGRESS → PENDING → RESOLVED → CLOSED`
* Priority, category, service, team, and assignee management
* Incident comments and resolution tracking
* Paginated incident listing with advanced filters

### 🤖 AI Copilot

Analyze an incident with a single action using a RAG-powered AI pipeline.

The AI combines:

* Current incident context
* Historical support tickets
* Knowledge-base articles
* Semantic retrieval
* Deterministic reranking
* Structured LLM reasoning
* Server-side evidence validation

AI output is returned as structured data rather than unrestricted text.

### 📚 Knowledge Base

Includes realistic troubleshooting content across multiple IT support categories.

Knowledge articles are:

1. Stored in MongoDB
2. Split into meaningful chunks
3. Embedded using Pinecone's integrated embedding model
4. Indexed for semantic retrieval
5. Retrieved as supporting evidence during incident analysis

### 🔎 Similar Incident Detection

Find historically similar incidents using semantic similarity.

The system supports configurable thresholds for:

* Duplicate incidents
* Related incidents

```env
SIMILARITY_DUPLICATE_THRESHOLD=0.90
SIMILARITY_RELATED_THRESHOLD=0.75
```

### 📌 Evidence-Backed AI

Every AI recommendation must be supported by retrieved evidence.

The backend validates every `evidence_id` returned by the model against the actual retrieved evidence set.

This prevents the model from:

* Inventing source IDs
* Citing unavailable documents
* Fabricating supporting evidence

### 📊 Dashboard Analytics

MongoDB aggregation pipelines provide:

* Incident status breakdown
* Priority distribution
* Category distribution
* Resolution activity
* Operational statistics

### 🛡️ AI Safety Guardrails

The AI is explicitly prevented from:

* Inventing incident or evidence IDs
* Claiming that an incident was resolved when it was not
* Automatically changing priority
* Automatically changing incident status
* Treating retrieved documents as executable instructions

Retrieved documents are treated as **untrusted reference data**, providing protection against prompt injection from knowledge-base or historical-ticket content.

### 🧪 Testable AI Architecture

The backend can run without real MongoDB, Pinecone, or Grok credentials.

```env
AI_PROVIDER=mock
```

The mock provider returns structurally valid responses for local development and automated testing.

> Mock responses must never be presented as real AI output during a demonstration.

---

# 🏗️ Architecture

```text
                    ┌─────────────────────────┐
                    │     React + Vite + TS   │
                    │                         │
                    │  Incident Dashboard     │
                    │  AI Copilot             │
                    │  Knowledge Base         │
                    │  Analytics              │
                    └────────────┬────────────┘
                                 │
                               REST
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       FastAPI           │
                    │                         │
                    │ Incident APIs           │
                    │ RAG Pipeline            │
                    │ AI Guardrails           │
                    │ Analytics               │
                    └───────┬─────────┬───────┘
                            │         │
                            │         │
                            ▼         ▼
                 ┌──────────────┐   ┌──────────────┐
                 │ MongoDB      │   │  Pinecone    │
                 │ Atlas        │   │              │
                 │              │   │ Semantic     │
                 │ Source of    │   │ Retrieval    │
                 │ Truth        │   │              │
                 └──────────────┘   └──────┬───────┘
                                           │
                                           ▼
                                  ┌────────────────┐
                                  │   Grok / xAI   │
                                  │                │
                                  │ Structured AI  │
                                  │ Reasoning      │
                                  └────────────────┘
```

### Core Architecture Principle

**MongoDB is the source of truth.**

Pinecone is treated as a **disposable, rebuildable retrieval index** rather than the authoritative data store.

This allows the vector index to be regenerated whenever required without compromising application state.

---

# 🔄 RAG Pipeline

The AI analysis pipeline follows this flow:

```text
Incident
   │
   ▼
Query Construction
   │
   ▼
Semantic Retrieval
   │
   ▼
Fallback Retrieval Broadening
   │
   ▼
Deterministic Reranking
   │
   ▼
Evidence Selection
   │
   ▼
Grounded Prompt
   │
   ▼
Grok / xAI
   │
   ▼
Structured JSON
   │
   ▼
Pydantic Validation
   │
   ▼
Evidence ID Validation
   │
   ▼
Backend Confidence Calculation
   │
   ▼
Persisted AI Analysis
```

### Retrieval Sources

The system retrieves evidence from:

* Knowledge-base articles
* Historical support tickets
* Previously resolved incidents

### Reranking

Retrieved results are reranked using deterministic signals including:

* Semantic similarity
* Category match
* Service match
* Resolution presence
* Lexical overlap

The current implementation intentionally uses a deterministic scoring strategy rather than a learned cross-encoder.

---

# 🧠 AI Guardrail Architecture

The model does **not** have unrestricted authority over application state.

The AI produces structured recommendations, while the backend remains responsible for validation and state changes.

```text
                ┌───────────────────┐
                │   Retrieved Data  │
                │                   │
                │ UNTRUSTED CONTENT │
                └─────────┬─────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Grounded      │
                  │ Prompt        │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   Grok / xAI  │
                  └───────┬───────┘
                          │
                    Structured JSON
                          │
                          ▼
                  ┌───────────────┐
                  │ Pydantic      │
                  │ Validation    │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Evidence ID   │
                  │ Validation    │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Backend       │
                  │ Confidence    │
                  └───────┬───────┘
                          │
                          ▼
                     User Output
```

Confidence is calculated independently by the backend using retrieval quality, evidence count, and evidence agreement rather than relying solely on the model's self-reported confidence.

---

# 🛠️ Tech Stack

| Layer            | Technology              |
| ---------------- | ----------------------- |
| Frontend         | React 18                |
| Build Tool       | Vite                    |
| Language         | TypeScript              |
| Routing          | React Router            |
| HTTP Client      | Axios                   |
| UI Icons         | lucide-react            |
| Backend          | FastAPI                 |
| Validation       | Pydantic v2             |
| Database Driver  | Motor                   |
| Database         | MongoDB Atlas           |
| Vector Database  | Pinecone                |
| Embeddings       | `llama-text-embed-v2`   |
| LLM              | Grok / xAI              |
| Testing          | pytest + pytest-asyncio |
| Containerization | Docker / Docker Compose |

---

# 📁 Project Structure

```text
ai-service-desk/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── prompts.py
│   │   │   ├── schemas.py
│   │   │   └── guardrails.py
│   │   │
│   │   └── ...
│   │
│   ├── scripts/
│   │   ├── download_dataset.py
│   │   ├── inspect_dataset.py
│   │   ├── import_dataset.py
│   │   ├── build_knowledge_base.py
│   │   ├── chunk_documents.py
│   │   ├── index_pinecone.py
│   │   ├── verify_ingestion.py
│   │   └── reset_database.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
│
├── data/
│   ├── raw/
│   └── processed/
│
├── DESIGN.md
├── .env.example
└── docker-compose.yml
```

---

# 🔐 Environment Configuration

Create your environment file from the provided example:

```bash
cp .env.example backend/.env
```

Configure the required services:

```env
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

> **Never commit `.env` or API credentials to version control.**

The repository only contains blank environment templates.

---

# 🤖 Grok / xAI Setup

The application uses the OpenAI-compatible xAI API.

### 1. Create an xAI account

Visit the xAI developer console:

https://console.x.ai

### 2. Create an API key

Open:

**API Keys → Create API Key**

Copy the key when it is displayed.

### 3. Configure the backend

Add the credentials to:

```text
backend/.env
```

Example:

```env
LLM_PROVIDER=grok
LLM_API_KEY=xai-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.x.ai/v1
LLM_MODEL=grok-4-fast
```

Model names can change over time, so verify the currently available model catalog before deployment or demonstration.

---

# 🗄️ Database Setup

## MongoDB Atlas

Create a MongoDB Atlas cluster and configure:

1. Database user
2. Network access / IP allowlist
3. Connection string
4. `MONGODB_URI`

Example:

```env
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=ai_service_desk
```

MongoDB acts as the application's **primary source of truth**.

---

# 🌲 Pinecone Setup

Create a Pinecone project and API key.

```env
PINECONE_API_KEY=
PINECONE_INDEX_NAME=ai-service-desk
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

The ingestion script automatically creates the required index when it does not already exist.

Pinecone is used specifically for **semantic retrieval** and can be rebuilt from the MongoDB-backed source data.

---

# 🚀 Installation

Clone the repository:

```bash
git clone <repo-url>
cd ai-service-desk
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Create the environment file:

```bash
cp .env.example backend/.env
```

Then configure MongoDB, Pinecone, and Grok credentials.

---

# 📥 Dataset & Knowledge Base Ingestion

Run the ingestion pipeline from the repository root.

```bash
python backend/scripts/download_dataset.py
```

Inspect the dataset:

```bash
python backend/scripts/inspect_dataset.py
```

Import historical tickets:

```bash
python backend/scripts/import_dataset.py
```

Build the knowledge base:

```bash
python backend/scripts/build_knowledge_base.py
```

Chunk documents:

```bash
python backend/scripts/chunk_documents.py
```

Index the chunks into Pinecone:

```bash
python backend/scripts/index_pinecone.py
```

Verify the complete ingestion pipeline:

```bash
python backend/scripts/verify_ingestion.py
```

### Complete Pipeline

```text
Raw Dataset
     │
     ▼
Dataset Inspection
     │
     ▼
Normalization
     │
     ▼
MongoDB
     │
     ├───────────────┐
     ▼               ▼
Knowledge Base    Historical Tickets
     │               │
     └───────┬───────┘
             ▼
        Chunking
             │
             ▼
          Pinecone
             │
             ▼
       Semantic Search
```

All ingestion operations are designed to be safely re-run.

To reset the database:

```bash
python backend/scripts/reset_database.py
```

---

# ⚡ Running the Application

## Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

Health check:

```text
http://localhost:8000/api/health
```

---

## Frontend

Open another terminal:

```bash
cd frontend
npm install
```

Create the frontend environment file:

```bash
cp .env.example .env
```

Configure:

```env
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

Application:

```text
http://localhost:5173
```

---

# 🧪 Running Tests

The backend test suite can run without real AI or vector database credentials.

```bash
cd backend
AI_PROVIDER=mock pytest -q
```

The tests mock:

* MongoDB
* Pinecone
* LLM provider

This makes the test suite deterministic and suitable for CI/local development.

---

# 🐳 Docker

Containerization is available through Docker Compose.

```bash
cp .env.example .env
```

Fill in the required credentials and run:

```bash
docker compose up --build
```

The application containers include:

* Frontend
* Backend

The following remain externally managed:

* MongoDB Atlas
* Pinecone

---

# 🔌 API Overview

FastAPI automatically exposes interactive documentation through `/docs`.

### Health

```http
GET /api/health
```

### Incidents

```http
GET    /api/incidents
POST   /api/incidents
GET    /api/incidents/{id}
PATCH  /api/incidents/{id}
DELETE /api/incidents/{id}
```

### Comments

```http
GET  /api/incidents/{id}/comments
POST /api/incidents/{id}/comments
```

### AI

```http
POST /api/incidents/{id}/analyze
```

### Resolution

```http
POST /api/incidents/{id}/resolve
```

### Similar Incidents

```http
GET /api/incidents/{id}/similar
```

### Knowledge Base

```http
GET  /api/knowledge
GET  /api/knowledge/{id}
POST /api/knowledge
```

### Search

```http
GET /api/search
```

### Dashboard

```http
GET /api/dashboard/stats
```

---

# 🔒 Security & Reliability Considerations

The application implements several safeguards around AI-generated output.

### Evidence Validation

Model-generated evidence IDs are validated against the actual retrieval results.

### Prompt Injection Defense

Retrieved content is explicitly treated as:

> **Reference data, not instructions.**

### Structured Output

LLM responses are validated against Pydantic schemas before being consumed by the application.

### Backend-Controlled Confidence

AI confidence is not blindly accepted from the model.

The backend calculates an evidence-based score using retrieval quality and evidence agreement.

### No Autonomous State Changes

AI recommendations do not automatically:

* Resolve incidents
* Change priorities
* Change statuses
* Claim completed actions

Final application state remains under backend/user control.

### Secret Management

Sensitive credentials are:

* Environment-based
* Excluded from Git
* Redacted from application logs

---

# ⚠️ Known Limitations

The current implementation intentionally has several limitations.

### Authentication

Authentication and authorization are not implemented.

The application assumes a trusted, single-tenant environment.

### Reranking

The reranker uses deterministic scoring rather than a learned cross-encoder.

### Search

`/api/search` primarily combines MongoDB search with structured filters.

Deep semantic retrieval is concentrated in:

```text
/analyze
/similar
```

### ID Generation

Incident/article IDs currently use the current maximum ID rather than an atomic counter.

This is acceptable at the current scale but should be replaced with atomic counters for production workloads.

### Dataset Schema Mapping

The dataset importer uses alias-based column matching against source CSV headers.

If the source dataset schema changes, run:

```bash
python backend/scripts/inspect_dataset.py
```

before importing again.

---

# 🧩 Design Decisions

The architecture intentionally separates responsibilities:

| Component | Responsibility               |
| --------- | ---------------------------- |
| MongoDB   | Source of truth              |
| Pinecone  | Semantic retrieval           |
| Grok      | AI reasoning                 |
| FastAPI   | Business logic & validation  |
| React     | User interface               |
| Pydantic  | Structured output validation |

### Why Pinecone?

Pinecone provides scalable semantic retrieval and integrated embeddings while keeping the retrieval layer independent from the application's primary database.

### Why MongoDB?

MongoDB provides flexible document storage for incidents, comments, knowledge articles, agents, categories, and AI analyses.

### Why Grok / xAI?

The xAI API exposes an OpenAI-compatible interface, allowing the LLM provider to remain replaceable behind a common application interface.

### Why Rebuildable Vector Indexes?

Pinecone is intentionally treated as a derived data layer.

If the vector index is lost or rebuilt, the application can regenerate it from authoritative MongoDB data.

---

# 🚧 Future Improvements

Potential production enhancements include:

* 🔐 Authentication and role-based access control
* 👥 Multi-agent team support
* 🔔 Real-time incident notifications
* ⏱️ SLA monitoring and escalation
* 🧠 Learned cross-encoder reranking
* 💬 Multi-turn AI Copilot conversations
* 🔄 Optimistic concurrency control
* ⚡ Atomic ID counters
* 📈 Advanced operational analytics
* 🔍 Hybrid semantic + keyword retrieval improvements

---

# 📄 Documentation

| Document                   | Description                                                 |
| -------------------------- | ----------------------------------------------------------- |
| [`README.md`](./README.md) | Project overview and setup                                  |
| [`DESIGN.md`](./DESIGN.md) | Architecture, RAG pipeline, data model and design decisions |

---

# 👨‍💻 Project Summary

**AI Service Desk** demonstrates how an enterprise support workflow can combine traditional incident management with evidence-grounded generative AI.

The key design principle is:

> **The LLM recommends. The retrieval system provides evidence. The backend validates. The user decides.**

This architecture keeps AI useful while maintaining traceability, deterministic validation, and control over application state.

---

## ⭐ Technical Highlights

* Retrieval-Augmented Generation
* Semantic similarity search
* Knowledge-base retrieval
* Historical incident retrieval
* Deterministic reranking
* Structured LLM output
* Server-side evidence validation
* Prompt-injection-aware retrieval
* MongoDB aggregation analytics
* FastAPI REST APIs
* React + TypeScript frontend
* Pinecone vector search
* Grok / xAI integration
* Mock AI provider for testing
* Dockerized deployment
* Automated backend tests
