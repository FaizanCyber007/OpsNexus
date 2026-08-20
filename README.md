# OpsNexus: Autonomous Document Intelligence & Operations Platform

OpsNexus centralizes enterprise B2B back-office document workflows — vendor risk questionnaires (SIG/CAIQ), invoice-to-ledger reconciliation, and SOC2/ISO compliance audit checks — behind an autonomous, hierarchical multi-agent team governed by **LangGraph** and standardized on Anthropic's **Model Context Protocol (MCP)**.

The system features a strict monorepo architecture with a high-performance **Django 5.2 + Django REST Framework** backend and a modern **Next.js 16 (App Router) + React 19 + Tailwind CSS** frontend.

---

## 🌟 Key Features & Implemented Capabilities

- 🧠 **LangGraph Hierarchical Multi-Agent Swarm**:
  - **Supervisor Agent (Google Gemini 2.5 Flash)**: Ingests raw document context, classifies intent (`sales_rfp`, `invoice_reconciliation`, `compliance_audit`, `general_intake`), and orchestrates sub-agents.
  - **Worker Sub-Agents (Groq LLaMA 3.3 70B)**: Ultra-fast ReAct agent executing targeted tool loops to extract structured answers, analyze risks, and formulate human action items.
  - **Deterministic Fast-Path**: Sub-millisecond keyword/extension routing before LLM escalation.
  - **Self-Correction Guardrails**: Pydantic schema validation loops (`ValidationError` feedback prompts) and Tenacity exponential backoff retries.

- 🔌 **Model Context Protocol (MCP 2.0)**:
  - Standardized JSON-RPC 2.0 tool execution layer (`mcp_host`) exposing organizational knowledge and tools (`search_company_knowledge`, vector store lookups) decoupled from model providers.

- 🔍 **On-Device Vector Memory & Multi-Format RAG**:
  - Ingests and extracts unstructured text from **PDF, DOCX, TXT, MD, CSV, and LOG** files.
  - Local dense vector embeddings via HuggingFace Sentence-Transformers (`all-MiniLM-L6-v2`) with **zero third-party embedding API costs**.
  - Per-tenant isolated **ChromaDB** collections (`org_<uuid>`) with automated cleanup signal lifecycles.

- ⚔️ **Interactive RAG Document Chat & Model Arena**:
  - In-app grounded document Q&A with verifiable chunk-level citations.
  - **Model Arena (`compare=true`)**: Side-by-side concurrent execution comparing **Groq (LLaMA 3.3 70B)** vs. **Google Gemini (2.5 Flash)** measuring roundtrip latency (ms), token consumption, and response accuracy.
  - **Redis Response Caching**: SHA-256 parameterized query caching with 15-minute TTL for sub-5ms cached queries.

- 📊 **Granular Observability & Audit Trail**:
  - Comprehensive relational tracking of every `AgentRun`, chronological `ToolCall` trace, `Answer` structure (Executive Summary, Risk Matrix, Action Items), and ground-truth text `Citation`.

- 💻 **Next.js 16 Modern UI Dashboard**:
  - Drag-and-drop file ingestion with immediate HTTP 202 acknowledgment and live polling telemetry.
  - Interactive **Document Detail** view with Executive Summary, Risk Matrix, and Action Items.
  - **Agent Intelligence & Trace Viewer** panel rendering the complete LangGraph execution graph and tool calls.
  - Integrated **Document Preview Pane** and side-by-side **RAG Model Arena**.

- 📖 **OpenAPI 3.0 / Swagger UI & ReDoc**:
  - Auto-generated, strongly-typed OpenAPI schemas powered by `drf-spectacular` at `/api/v1/docs/` and `/api/v1/redoc/`.

- 🐳 **Production Containerization & Cloud Extensibility**:
  - Multi-stage Docker deployment (`docker-compose.prod.yml`) featuring Gunicorn WSGI workers, WhiteNoise static compression, Next.js standalone build, PostgreSQL 16, Redis, and ChromaDB persistence.
  - Dual-storage engine supporting local filesystem and AWS S3 (`django-storages` + `boto3`).

---

## 🏗️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Frontend["Frontend (Next.js 16 App Router)"]
        UI["Dashboard & Upload Dropzone"]
        TraceUI["Agent Trace & Intelligence Viewer"]
        ArenaUI["RAG Chat & Model Arena"]
    end

    subgraph API["Backend API Gateway (Django 5.2 + DRF)"]
        Ingest["Async Document Ingestion (HTTP 202)"]
        ChatAPI["Document Chat & Arena Endpoint"]
        Swagger["OpenAPI / Swagger UI (/api/v1/docs/)"]
    end

    subgraph Memory["Vector Memory Layer"]
        Extractor["Multi-Format Parser (PDF, DOCX, TXT, CSV)"]
        Embedder["Sentence-Transformers (all-MiniLM-L6-v2)"]
        Chroma[("ChromaDB (Per-Org Collections)")]
    end

    subgraph Agents["LangGraph Multi-Agent Swarm"]
        FastRouter{"Deterministic Fast Router"}
        Supervisor["Supervisor Agent (Gemini 2.5 Flash)"]
        SalesWorker["Sales Worker Sub-Agent (Groq LLaMA 3.3 70B)"]
        MCPClient["MCP Client (JSON-RPC)"]
        MCPHost["MCP Tool Server (Company Knowledge)"]
    end

    subgraph Storage["Data & Cache Layer"]
        PG[("PostgreSQL 16 Relational DB")]
        Redis[("Redis Response Cache & Broker")]
    end

    UI -->|POST /api/v1/documents/| Ingest
    Ingest --> Extractor --> Embedder --> Chroma
    Ingest --> FastRouter
    FastRouter -->|Complex / Ambiguous| Supervisor
    Supervisor -->|sales_rfp| SalesWorker
    SalesWorker --> MCPClient --> MCPHost --> Chroma
    SalesWorker -->|StructuredAnswer| PG
    Supervisor -->|Classification| PG
    
    ArenaUI -->|POST /api/v1/documents/:id/chat/| ChatAPI
    ChatAPI --> Redis
    ChatAPI -->|Semantic Search| Chroma
    ChatAPI -->|Concurrent Benchmark| SalesWorker
    ChatAPI -->|Concurrent Benchmark| Supervisor

    UI -.->|Live Polling & Trace Telemetry| PG
    TraceUI -.->|GET /api/v1/agent-runs/:id/tool-calls/| PG
```

---

## 💻 Tech Choices & Status Matrix

| Layer | Technology | Purpose | Status |
|---|---|---|---|
| **Backend Framework** | Django 5.2 + Django REST Framework | Multi-tenant REST API, ORM, and async pipeline | ✅ Implemented |
| **Frontend Framework** | Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS | Reactive dashboard, live telemetry & Arena UI | ✅ Implemented |
| **Agent Orchestration** | LangGraph 1.2+ | State machines, cyclical routing & guardrails | ✅ Implemented |
| **Supervisor LLM** | Google Gemini 2.5 Flash (`langchain-google-genai`) | High-reasoning document classification & routing | ✅ Implemented |
| **Worker Sub-Agents** | Groq LLaMA 3.3 70B (`langchain-groq`) | Ultra-fast ReAct tool execution & synthesis | ✅ Implemented |
| **Tool Protocol** | Model Context Protocol (Anthropic `mcp` 2.0 SDK) | Decoupled JSON-RPC tool integration | ✅ Implemented |
| **Vector Database / RAG** | ChromaDB 1.5+ + `sentence-transformers` | On-device semantic embedding & chunk retrieval | ✅ Implemented |
| **Relational Database** | PostgreSQL 16 (Alpine) | Multi-tenant document, run, and trace persistence | ✅ Implemented |
| **Cache & Broker** | Redis 7+ (Alpine) + `django-redis` | 15-minute response cache for RAG / Model Arena | ✅ Implemented |
| **API Documentation** | `drf-spectacular` (OpenAPI 3.0 / Swagger UI / ReDoc) | Interactive documentation & schema export | ✅ Implemented |
| **Storage Layer** | Local Filesystem / AWS S3 (`django-storages` + `boto3`) | Document media attachment storage | ✅ Implemented |
| **Production Serving** | Gunicorn + WhiteNoise + Next.js Standalone Runner | Production WSGI web server & static compression | ✅ Implemented |

---

## 📁 Monorepo Layout

```
OpsNexus/
├── backend/
│   ├── agents/               # AgentProfile, AgentRun, ToolCall, Answer, Citation models & APIs
│   ├── core/                 # Multi-tenant Organization, UserProfile & BaseModel
│   ├── documents/            # Document model, ingestion views, soft deletion & lifecycle signals
│   ├── mcp_host/             # Standalone Model Context Protocol (MCP 2.0) Server & Client
│   ├── memory/               # ChromaDB vector client, multi-format text parsers & cleanup tasks
│   ├── orchestration/        # LangGraph StateGraph, Gemini/Groq model clients, guards & Arena chat
│   ├── opsnexus_backend/     # Django settings, WSGI, URLs & drf-spectacular configuration
│   ├── Dockerfile            # Multi-stage production backend container (Gunicorn + WhiteNoise)
│   ├── requirements.txt      # Python dependencies
│   └── pytest.ini            # Pytest test suite configuration
├── frontend/
│   ├── src/app/              # Next.js App Router (/dashboard, /dashboard/document/[id])
│   ├── src/components/       # UI primitives (Card, Button, Badge) & Layout components
│   ├── src/components/features/ # Dropzone, DocumentDetail, AgentTraceViewer, DocumentChatPanel (Arena)
│   ├── src/contexts/         # Organization / Tenant Context Provider
│   ├── src/hooks/            # Polling hooks (useDocumentPolling) & client telemetry
│   ├── src/lib/              # Typed API clients & Zod / TypeScript schemas
│   ├── Dockerfile            # Multi-stage production frontend container
│   └── package.json          # Next.js 16 & React 19 dependencies
├── docker-compose.yml        # Development infrastructure (PostgreSQL 16 + Redis)
├── docker-compose.prod.yml   # Full-stack production deployment (Postgres, Redis, Backend, Frontend)
├── presentation_outline.md   # Comprehensive slide-by-slide presentation & technical defense guide
└── prompt.md                 # Running chronological log of system prompts
```

---

## 🚀 Running the System

### Option 1: Full-Stack Production Stack via Docker Compose (Recommended)

To run the entire containerized production stack (PostgreSQL, Redis, Django Backend via Gunicorn/WhiteNoise, Next.js Frontend, ChromaDB persistence):

```bash
# 1. Clone the repository and navigate to root
cd OpsNexus

# 2. Build and launch all production services in the background
docker compose -f docker-compose.prod.yml up --build -d

# 3. View running container logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Access URLs:
- 🌐 **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- 🔌 **Backend REST API**: [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/)
- 📖 **Interactive Swagger UI**: [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
- 📚 **ReDoc Documentation**: [http://localhost:8000/api/v1/redoc/](http://localhost:8000/api/v1/redoc/)
- ⚙️ **Django Admin Portal**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

To tear down the production stack:
```bash
docker compose -f docker-compose.prod.yml down
```

---

### Option 2: Local Development Setup

#### 1. Start Infrastructure Services (Postgres & Redis)
From the repository root:
```bash
docker compose up -d
```
*Starts PostgreSQL 16 on `localhost:5432` and Redis on `localhost:6379`.*

#### 2. Configure & Run Backend (Django 5.2)
```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Apply database migrations
python manage.py migrate

# (Optional) Create an admin superuser
python manage.py createsuperuser

# Start the Django development server
python manage.py runserver 8000
```
*Backend runs at [http://localhost:8000](http://localhost:8000).*

#### 3. Configure & Run Frontend (Next.js 16)
In a new terminal:
```bash
cd frontend

# Configure environment variables
cp .env.local.example .env.local

# Install Node packages
npm install

# Start the Next.js development server
npm run dev
```
*Frontend dashboard is live at [http://localhost:3000](http://localhost:3000).*

---

## 🔑 Environment Variables Configuration

### Backend (`backend/.env` or Docker Environment)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | Django secret cryptographic key |
| `DEBUG` | `True` (Dev) / `False` (Prod) | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed HTTP host headers |
| `DATABASE_URL` | `postgres://opsnexus:opsnexus@127.0.0.1:5432/opsnexus` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://127.0.0.1:6379/1` | Redis connection URL for caching & broker |
| `GOOGLE_API_KEY` | *(Optional)* | Google Gemini API key (Supervisor Agent & Arena) |
| `GROQ_API_KEY` | *(Optional)* | Groq API key (Sales Worker & Arena LLaMA 3.3) |
| `USE_S3` | `False` | Toggle AWS S3 storage instead of local disk |
| `AWS_ACCESS_KEY_ID` | *(Optional)* | AWS credentials (only when `USE_S3=True`) |
| `AWS_SECRET_ACCESS_KEY`| *(Optional)* | AWS credentials (only when `USE_S3=True`) |
| `AWS_STORAGE_BUCKET_NAME` | *(Optional)* | Target S3 bucket name |

> **Note on Free-Tier / Missing Keys**: OpsNexus is designed with graceful resilience. If API keys are omitted in development, the system smoothly falls back to simulated outputs and deterministic routing without crashing.

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Base URL pointing to the Django REST backend |

---

## 🧪 Testing & Quality Assurance

### Running Backend Test Suite (150+ Passing Tests)
From the `backend/` directory:

```bash
# Run all tests with pytest
pytest

# Run tests with verbose output and test names
pytest -v

# Run tests with coverage analysis
pytest --cov=. --cov-report=term-missing

# Run specific test modules
pytest orchestration/tests/test_guardrails.py
pytest documents/tests/test_e2e_pipeline.py
```

### Running Frontend Linters & Build Validation
From the `frontend/` directory:

```bash
# Run ESLint validation
npm run lint

# Validate production Next.js App Router build
npm run build
```

---

## 📋 End-to-End Walkthrough Guide

1. **Create an Organization UUID**:
   ```bash
   cd backend
   python manage.py shell -c "
   from core.models import Organization
   org, _ = Organization.objects.get_or_create(slug='demo', defaults={'name': 'Demo Enterprise'})
   print(f'Organization ID: {org.id}')
   "
   ```
2. **Open the Dashboard**: Navigate to [http://localhost:3000/dashboard](http://localhost:3000/dashboard) and paste the Organization ID.
3. **Upload a Document**: Drag and drop any RFP, questionnaire, compliance report, or invoice (`.pdf`, `.docx`, `.txt`, `.csv`, `.md`).
4. **Live Polling Telemetry**: The document status shows `processing` immediately and updates automatically to `completed` upon LangGraph resolution.
5. **Inspect the Document Details**: Click the document to view the extracted **Executive Summary**, **Risk Flags**, **Action Items**, and **Confidence Meter**.
6. **Trace Viewer**: Inspect the **Agent Intelligence & Trace Viewer** to examine every intermediate Supervisor and Worker tool call.
7. **RAG Model Arena**: Open the Document Chat panel, toggle **Arena Compare Mode**, and ask questions (e.g., *"What are the data retention and encryption requirements?"*) to benchmark **Groq vs. Gemini** latency and answers side-by-side with verified citations.
8. **Explore the OpenAPI Docs**: Open [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/) to test all REST endpoints interactively.

---

## 📜 Prompt Log

Every prompt used throughout the iterative development and architecture of OpsNexus is logged chronologically in [`prompt.md`](./prompt.md).
