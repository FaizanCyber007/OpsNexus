# OpsNexus: Autonomous Document Intelligence & Operations Platform

OpsNexus centralizes enterprise B2B back-office document workflows — vendor risk questionnaires (SIG/CAIQ), invoice-to-ledger reconciliation, and SOC2/ISO compliance audit checks — behind an autonomous, hierarchical multi-agent swarm governed by **LangGraph** and standardized on Anthropic's **Model Context Protocol (MCP 2.0)**.

The platform is architected as a production-grade monorepo featuring a high-performance **Django 5.2 + Django REST Framework** backend and a modern, high-density **Next.js 16 (App Router) + React 19 + Tailwind CSS + Framer Motion** frontend.

---

## 🌟 Key Features & Implemented Capabilities

### 🧠 LangGraph Hierarchical Multi-Agent Swarm
- **Supervisor Agent (Google Gemini 2.5 Flash)**: Ingests raw document context, classifies intent (`sales_rfp`, `invoice_reconciliation`, `compliance_audit`, `general_intake`), and orchestrates domain-specific worker sub-agents.
- **Worker Sub-Agents (Groq `openai/gpt-oss-120b`)**: Ultra-fast ReAct agent executing targeted tool loops, querying MCP knowledge servers, and synthesizing structured outputs.
- **Deterministic Fast-Path Router**: Sub-millisecond rule-based keyword/regex routing before LLM escalation.
- **Production Guardrails & Auto-Correction**:
  - **Pydantic Auto-Correction Loops**: Catches schema validation failures (`ValidationError`) and feeds error context back to the model for self-correction up to `MAX_VALIDATION_LOOPS` (2) attempts.
  - **Tenacity Exponential Backoff Retries**: Resilient retry policy (up to 3 attempts with 2–10s backoff) catching transient rate limits (`429`) and upstream service unavailability (`503`).
  - **LLM Provider Fallback**: Automatic failover chain from Groq to Gemini if Groq exhausts retry limits.
  - **Graceful Mock Fallbacks**: Simulated deterministic pipelines when API keys are absent in development.

### 🔌 Model Context Protocol (MCP 2.0)
- **Standalone MCP Server** (`mcp_host/server.py`): Standards-compliant JSON-RPC 2.0 tool execution layer over `stdio` exposing company knowledge and internal pricing policies (`get_internal_pricing_policy`).
- **Zero Vendor Lock-In Client Bridge** (`mcp_host/client.py`): Decoupled MCP 2.0 transport client integrating external organizational tools into LangChain/LangGraph runnables without pinning legacy SDKs.

### 🔍 Dense Vector Memory & Multi-Format RAG
- **Zero-Cost Local Dense Vector Embeddings**: HuggingFace Sentence-Transformers (`all-MiniLM-L6-v2`) generating dense semantic embeddings locally with **$0 third-party embedding API costs**.
- **Multi-Format Document Parsing**: Native extraction for **PDF, DOCX, TXT, MD, CSV, and LOG** files.
- **Per-Tenant Vector Isolation**: Isolated ChromaDB collections (`org_<uuid>`) with automated lifecycle signals (`post_delete` signals prune ChromaDB embeddings when documents are removed).

### ⚔️ Interactive RAG Document Chat & Model Arena
- **Grounded Conversational RAG**: In-app document Q&A with verifiable chunk-level citations and similarity scores.
- **Model Arena (`compare=true`)**: Side-by-side concurrent execution comparing **Groq (`openai/gpt-oss-120b`)** vs. **Google Gemini (2.5 Flash)** measuring roundtrip latency (ms), token consumption, and response accuracy.
- **Redis Response Caching**: Parameterized SHA-256 query caching with 15-minute TTL (`django-redis`) for sub-5ms repeated query responses.

### 🛡️ Enterprise Security, SOC2 Audit Logging & Rate Limiting
- **Custom Rate Throttling**: DRF rate limiting protecting AI endpoints from abuse (`5 requests/minute` on `/documents/` upload and `/chat/` arena endpoints).
- **Hardened Security Headers**: `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS: DENY`, `CSRF_COOKIE_HTTPONLY`.
- **SOC2 Audit Trail**: Relational `AuditLog` model and automated Django signals recording every `CREATE`, `UPDATE`, and `DELETE` action performed by Organization Admins on documents, health rules, and playbooks.
- **Auditable Admin API**: Dedicated `GET /api/v1/audit-logs/` endpoint for compliance review.
- **Dual-Storage Backend**: Switchable media engine supporting local filesystem and AWS S3 (`django-storages` + `boto3`) via `USE_S3`.

### 💻 Next.js 16 Premium B2B Dashboard
- **Modern Dark Aesthetic**: Deeply premium near-black theme (`#0c0c10` / `#111116`), Glassmorphism (`backdrop-blur-2xl`), subtle 1px borders (`border-white/10`), and Three.js 3D dynamic visual background.
- **Drag-and-Drop Ingestion**: Sub-second HTTP 202 async intake acknowledgment with live polling telemetry (`useDocumentPolling`).
- **High-Density Workbench**: Split-pane layout featuring an integrated **Document Preview Pane**, **RAG Model Arena**, and **Agent Intelligence & Trace Viewer**.
- **Granular Observability**: Interactive timeline rendering all `AgentRun` tool calls, intermediate reasoning steps, confidence meters, risk matrices, and action item checklists.
- **Advanced State UX**: Skeleton and shimmer loaders matching real UI geometries, actionable Toast notifications, and empty states with AI quick-start CTAs.

### 📖 OpenAPI 3.0 / Swagger UI & ReDoc
- Auto-generated, strongly-typed OpenAPI schemas powered by `drf-spectacular` at `/api/v1/docs/` and `/api/v1/redoc/`.

---

## 🏗️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Frontend["Frontend (Next.js 16 App Router + React 19 + Framer Motion)"]
        UI["Dashboard & Upload Dropzone"]
        Workbench["Document Detail & Preview Pane"]
        TraceUI["Agent Intelligence & Trace Viewer"]
        ArenaUI["RAG Chat & Model Arena"]
    end

    subgraph API["Backend API Gateway (Django 5.2 + DRF)"]
        Ingest["Async Document Ingestion (HTTP 202)"]
        ChatAPI["Document Chat & Model Arena Endpoint"]
        AuditAPI["SOC2 Audit Logs Endpoint (/api/v1/audit-logs/)"]
        Swagger["OpenAPI / Swagger UI (/api/v1/docs/)"]
        Throttle{"Rate Throttles (5 req/min)"}
    end

    subgraph Memory["Vector Memory Layer"]
        Extractor["Multi-Format Parser (PDF, DOCX, TXT, CSV, LOG, MD)"]
        Embedder["Sentence-Transformers (all-MiniLM-L6-v2)"]
        Chroma[("ChromaDB (Per-Org Collections)")]
    end

    subgraph Agents["LangGraph Multi-Agent Swarm"]
        FastRouter{"Deterministic Fast Router"}
        Supervisor["Supervisor Agent (Gemini 2.5 Flash)"]
        Guardrails{"Pydantic Auto-Correction & Tenacity Retries"}
        SalesWorker["Sales Worker Sub-Agent (Groq gpt-oss-120b)"]
        Fallback["Gemini Fallback Chain"]
        MCPClient["MCP Client Bridge (JSON-RPC)"]
        MCPHost["MCP Tool Server (Internal Pricing & Knowledge)"]
    end

    subgraph Storage["Data, Cache & Observability Layer"]
        PG[("PostgreSQL 16 Relational DB (Multi-Tenant)")]
        Redis[("Redis Response Cache & Broker")]
        S3[("AWS S3 / Local Media Storage")]
    end

    UI -->|POST /api/v1/documents/| Throttle --> Ingest
    Ingest --> Extractor --> Embedder --> Chroma
    Ingest --> S3
    Ingest --> FastRouter
    FastRouter -->|Complex / Ambiguous| Supervisor
    Supervisor --> Guardrails
    Supervisor -->|sales_rfp| SalesWorker
    SalesWorker --> Guardrails
    SalesWorker -->|On Groq Outage| Fallback
    SalesWorker --> MCPClient --> MCPHost
    SalesWorker -->|StructuredAnswer| PG
    Supervisor -->|Classification & Reasoning| PG
    
    ArenaUI -->|POST /api/v1/documents/:id/chat/| Throttle --> ChatAPI
    ChatAPI --> Redis
    ChatAPI -->|Semantic Search| Chroma
    ChatAPI -->|Concurrent Benchmark| SalesWorker
    ChatAPI -->|Concurrent Benchmark| Supervisor

    UI -.->|Live Polling & Trace Telemetry| PG
    TraceUI -.->|GET /api/v1/agent-runs/:id/tool-calls/| PG
    AuditAPI -.->|GET /api/v1/audit-logs/| PG
```

---

## 💻 Tech Choices & Status Matrix

| Layer | Technology | Purpose | Status |
|---|---|---|---|
| **Backend Framework** | Django 5.2.16 + Django REST Framework 3.17 | Multi-tenant REST API, async ingestion & ORM | ✅ Implemented |
| **Frontend Framework** | Next.js 16.3 (App Router) + React 19.2 + TypeScript 5 | Reactive dashboard, live telemetry & Arena UI | ✅ Implemented |
| **Styling & Animation** | Tailwind CSS 4 + Framer Motion 13 + Three.js | Dark mode, micro-interactions & 3D background | ✅ Implemented |
| **Agent Orchestration** | LangGraph 1.2 + LangChain Core | State machine graphs, cyclical routing & guardrails | ✅ Implemented |
| **Supervisor LLM** | Google Gemini 2.5 Flash (`langchain-google-genai`) | High-reasoning document classification & routing | ✅ Implemented |
| **Worker Sub-Agents** | Groq `openai/gpt-oss-120b` (`langchain-groq`) | Ultra-fast ReAct tool execution & structured output | ✅ Implemented |
| **Tool Protocol** | Model Context Protocol (Anthropic `mcp` 2.0.0 SDK) | Decoupled JSON-RPC 2.0 tool execution layer | ✅ Implemented |
| **Vector Database / RAG** | ChromaDB 1.5.9 + `sentence-transformers` 5.5 | Local dense embeddings (`all-MiniLM-L6-v2`) | ✅ Implemented |
| **Relational Database** | PostgreSQL 16 (Alpine) + `psycopg3` | Multi-tenant document, run, trace & audit persistence | ✅ Implemented |
| **Cache & Broker** | Redis 7+ (Alpine) + `django-redis` 5.4 | 15-minute response cache for RAG / Model Arena | ✅ Implemented |
| **API Documentation** | `drf-spectacular` 0.28 (OpenAPI 3.0 / Swagger / ReDoc) | Interactive documentation & schema export | ✅ Implemented |
| **Storage Layer** | Local Filesystem / AWS S3 (`django-storages` + `boto3`) | Document media attachment storage | ✅ Implemented |
| **Production Serving** | Gunicorn 23 + WhiteNoise 6.9 + Next.js Standalone | Production WSGI web server & static compression | ✅ Implemented |

---

## 📁 Monorepo Layout

```
OpsNexus/
├── backend/
│   ├── agents/                   # AgentProfile, AgentRun, ToolCall, Answer, Citation models & APIs
│   │   ├── models.py             # Relational agent models & audit tracking
│   │   ├── serializers.py        # Serializers for runs, tool traces, answers, citations
│   │   ├── views.py              # AgentRunViewSet with tool-calls trace endpoint
│   │   └── tests/                # Test suite for agent run persistence and traces
│   ├── core/                     # Multi-tenant Organization, UserProfile, HealthRule, Playbook, AuditLog
│   │   ├── middleware.py         # AuditLogContextMiddleware capturing IP and active user
│   │   ├── models.py             # Multi-tenant base models & SOC2 AuditLog
│   │   ├── signals.py            # Automatic SOC2 audit logging signals
│   │   ├── throttling.py         # Custom DRF rate throttling classes (5 req/min)
│   │   ├── views.py              # AuditLogViewSet (read-only compliance audit API)
│   │   └── tests/                # Tests for multi-tenancy, throttling, security & audit logs
│   ├── documents/                # Document model, ingestion views, soft deletion & signals
│   │   ├── models.py             # Document model with UUIDv4, status, and file field
│   │   ├── tasks.py              # Background ingestion runner with LangGraph trigger
│   │   ├── views.py              # DocumentViewSet with upload throttling & prefetching
│   │   └── tests/                # Tests for ingestion pipeline, soft delete & signals
│   ├── mcp_host/                 # Standalone Model Context Protocol (MCP 2.0) Server & Client
│   │   ├── server.py             # JSON-RPC stdio MCP tool server
│   │   ├── client.py             # Asynchronous MCP client bridge wrapping LangChain tools
│   │   └── tests/                # MCP protocol and tool integration tests
│   ├── memory/                   # ChromaDB vector client, multi-format text parsers & cleanup
│   │   ├── vector_client.py      # Multi-format extractors & tenant-isolated ChromaDB client
│   │   └── tests/                # Parsers, vector indexing, and collection pruning tests
│   ├── orchestration/            # LangGraph StateGraph, Gemini/Groq model clients, guards & Arena
│   │   ├── agent_runner.py       # Pipeline entry point bridging DB with LangGraph
│   │   ├── graph.py              # LangGraph Supervisor & Sales Worker state graph
│   │   ├── model_client.py       # LLMFactory with Tenacity retries and Gemini fallback
│   │   ├── schemas.py            # Pydantic schemas (ClassificationResult, StructuredAnswer)
│   │   ├── tool_registry.py      # LangChain tool bindings (search_company_knowledge)
│   │   ├── views.py              # DocumentChatView (RAG Chat + Model Arena with Redis cache)
│   │   └── tests/                # Guardrails, schema validation, arena & chat tests
│   ├── opsnexus_backend/         # Django settings, WSGI, URLs & drf-spectacular configuration
│   ├── Dockerfile                # Multi-stage production backend container (Gunicorn + WhiteNoise)
│   ├── requirements.txt          # Python dependencies
│   └── pytest.ini                # Pytest test configuration
├── frontend/
│   ├── src/app/                  # Next.js App Router
│   │   ├── dashboard/            # Main ingestion dashboard & document detail workbench
│   │   │   ├── page.tsx          # Dashboard page
│   │   │   └── document/[id]/    # Split-pane document workbench route
│   │   ├── globals.css           # Tailwind CSS 4 theme tokens & custom glass utilities
│   │   ├── layout.tsx            # Global layout with ToastProvider & dark backdrop
│   │   └── page.tsx              # Root redirect to /dashboard
│   ├── src/components/
│   │   ├── features/             # Ingestion Dropzone, DocumentDetail, AgentTraceViewer,
│   │   │                         # DocumentChatPanel (Model Arena), AnswerDisplay, RecentRunsTable
│   │   ├── layout/               # Sidebar navigation with active Framer Motion layout pill
│   │   └── ui/                   # Card, Button, StatTile, StatusBadge, RiskBadge, ActionItemChecklist,
│   │                             # Meter, Skeleton, Shimmer, EmptyState, ThreeBackground, Toast
│   ├── src/contexts/             # TenantContext, ToastContext & notification management
│   ├── src/hooks/                # useDocumentPolling for live async ingestion status
│   ├── src/lib/                  # apiClient, TypeScript types & Zod schema definitions
│   ├── Dockerfile                # Multi-stage production frontend container (Next.js standalone)
│   └── package.json              # Next.js 16, React 19, Framer Motion, Three.js dependencies
├── docker-compose.yml            # Development infrastructure (PostgreSQL 16 + Redis)
├── docker-compose.prod.yml       # Full-stack production stack (Postgres, Redis, Backend, Frontend)
├── presentation_outline.md       # Slide-by-slide 20-min capstone presentation & technical defense guide
└── prompt.md                     # Chronological prompt log of system iterations
```

---

## 🚀 Running the System

### Option 1: Full-Stack Production Stack via Docker Compose (Recommended)

To launch the complete containerized production environment (PostgreSQL 16, Redis, Django Backend via Gunicorn/WhiteNoise, Next.js Frontend, ChromaDB persistence):

```bash
# 1. Clone the repository and navigate to root
cd OpsNexus

# 2. Build and launch all production services in the background
docker compose -f docker-compose.prod.yml up --build -d

# 3. View running container logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Access Endpoints:
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

# IN A NEW TERMINAL: Start the RQ Worker (Required for processing documents!)
# On Windows:
python manage.py rqworker default --worker-class rq.worker.SimpleWorker
# On macOS / Linux:
python manage.py rqworker default
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

## 🔑 Environment Variables Reference

### Backend (`backend/.env` or Docker Environment)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | Django secret cryptographic key |
| `DEBUG` | `True` (Dev) / `False` (Prod) | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed HTTP host headers |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Allowed CORS origins for frontend requests |
| `DATABASE_URL` | `postgres://opsnexus:opsnexus@127.0.0.1:5432/opsnexus` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://127.0.0.1:6379/1` | Redis connection URL for caching & broker |
| `GOOGLE_API_KEY` | *(Optional)* | Google Gemini API key (Supervisor Agent, Fallback & Arena) |
| `GROQ_API_KEY` | *(Optional)* | Groq API key (Sales Worker Sub-Agent & Arena LLaMA 3.3) |
| `USE_S3` | `False` | Toggle AWS S3 storage instead of local disk |
| `AWS_ACCESS_KEY_ID` | *(Optional)* | AWS credentials (only when `USE_S3=True`) |
| `AWS_SECRET_ACCESS_KEY`| *(Optional)* | AWS credentials (only when `USE_S3=True`) |
| `AWS_STORAGE_BUCKET_NAME` | *(Optional)* | Target S3 bucket name |
| `AWS_S3_REGION_NAME` | `us-east-1` | AWS S3 region |

> **Graceful Degradation Note**: If `GOOGLE_API_KEY` or `GROQ_API_KEY` are omitted during evaluation, OpsNexus automatically falls back to simulated deterministic responses and routing without crashing.

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Base URL pointing to the Django REST backend |

---

## 🧪 Testing & Quality Assurance

### Running Backend Test Suite (170+ Passing Unit & Integration Tests)
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
pytest core/tests/test_throttling_and_security.py
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

1. **Create an Organization Tenant**:
   ```bash
   cd backend
   python manage.py shell -c "
   from core.models import Organization
   org, _ = Organization.objects.get_or_create(slug='demo', defaults={'name': 'Demo Enterprise'})
   print(f'Organization ID: {org.id}')
   "
   ```
2. **Access the Dashboard**: Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard). The default tenant UUID `00000000-0000-0000-0000-000000000001` or your created Org ID can be selected.
3. **Upload a Document**: Drag and drop any RFP, questionnaire, invoice, or compliance report (`.pdf`, `.docx`, `.txt`, `.csv`, `.md`, `.log`).
4. **Live Ingestion Telemetry**: The upload returns an instant HTTP 202 acknowledgment. The document status updates from `pending` -> `processing` -> `completed` via background polling.
5. **Inspect the Document Workbench**: Click on the processed document row to enter the split-pane workbench:
   - **Left Pane**: Interactive document file preview.
   - **Right Pane (Tab 1 - RAG Chat & Model Arena)**: Ask grounded questions and toggle **Arena Compare Mode** to benchmark Groq vs. Gemini Flash latency (ms), token metrics, and chunk citations.
   - **Right Pane (Tab 2 - Agent Intelligence & Trace)**: Inspect the LangGraph execution trace, Supervisor classification reasoning, risk matrix flags, action items checklist, and confidence score meter.
6. **Verify SOC2 Audit Logs**: Review recorded administrative actions at `GET http://localhost:8000/api/v1/audit-logs/`.
7. **Explore OpenAPI Documentation**: Navigate to [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/) or [http://localhost:8000/api/v1/redoc/](http://localhost:8000/api/v1/redoc/) for interactive Swagger testing.

---

## 📽️ Presentation & System Prompts

- 🎤 **Capstone Presentation Guide**: Detailed slide-by-slide talk tracks, visual diagrams, and Q&A defense strategies are documented in [`presentation_outline.md`](./presentation_outline.md).
- 📜 **Prompt Log**: The chronological log of all engineering and architectural prompts used in building OpsNexus is available in [`prompt.md`](./prompt.md).
