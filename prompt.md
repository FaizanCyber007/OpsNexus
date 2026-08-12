# Prompts Used to Build OpsNexus

This file logs every prompt (user instruction) given to the AI assistant during
the build of this system, in the order they were given. New prompts should be
appended to the end of this file, labeled sequentially.

---

## Prompt 1

```
[SYSTEM CONTEXT]
You are a Staff Software Architect scaffolding "OpsNexus" (Phase 3 Build).
- Monorepo structure: `/frontend` and `/backend` must be strictly separated.
- Stack: Django 5, DRF, PostgreSQL. (Linter: `black` and `flake8` ONLY).
- Constraint: We must maintain a flawless Git history. You will commit frequently.

[YOUR TASK: BACKEND FOUNDATION & MODULAR APPS]
Execute these steps sequentially. Do not proceed to the next step until the current one is committed to Git.

1. Project Init: 
   - Initialize a Git repository if one does not exist.
   - Create the `/backend` directory. Initialize a Django project named `opsnexus_backend`.
   - Setup `requirements.txt` (`django`, `djangorestframework`, `psycopg`, `django-environ`, `django-cors-headers`, `black`, `flake8`). Set up `.env.example`.
   - Action: `git add .` and `git commit -m "chore: init backend monorepo and django dependencies"`

2. App 1 - `core` (Foundation & Tenancy):
   - Create app `core`. 
   - Implement an abstract `BaseModel` (UUID, created_at, updated_at, deleted_at).
   - Implement `Organization` and `UserProfile` (linking to Django User).
   - Action: Run `black`/`flake8`. `git add .` and `git commit -m "feat(core): implement abstract base model and multi-tenant user models"`

3. App 2 - `documents` (Data Ingestion):
   - Create app `documents`.
   - Implement `Document` model (FK -> Organization). Fields: `doc_type`, `status` (pending, processing, completed, failed), `file_path`.
   - Action: Run `black`/`flake8`. `git add .` and `git commit -m "feat(documents): implement document ingestion models"`

4. App 3 - `agents` (Observability & State):
   - Create app `agents`.
   - Implement `AgentProfile` (system_prompt, model_name, temperature).
   - Implement `AgentRun` (FK -> Document, 1:N). 
   - Implement `ToolCall` (FK -> AgentRun) with JSONFields for input/output.
   - Implement `Answer` and `Citation` models.
   - Action: Run `black`/`flake8`. `git add .` and `git commit -m "feat(agents): implement agent execution and observability models"`

[EXECUTION CONSTRAINTS]
Run `python manage.py makemigrations` and `migrate`. Ensure strict modularity (models in their respective apps).
```

---

## Prompt 2

*(Answers given to the assistant's clarifying questions before Step 1 of the plan above was executed.)*

1. **Database setup** — "No local PostgreSQL server is installed/running... How should the DB be configured for this scaffold?"
   > Postgres is installed in the docker. Docker is running just check it and set everything up for that.

2. **AgentRun fields** — "Should I add observability fields (status, started_at/finished_at, error_message) and a FK to AgentProfile?"
   > Yes, add observability fields (Recommended)

3. **Answer/Citation model** — "Answer and Citation models have no specified relationships/fields. What structure should they have?"
   > Choose the best approach you think should be for a system with this description: "B2B companies bleed capital through manual, unstructured data processing across disjointed departments. Sales teams spend hundreds of hours manually filling out security questionnaires; finance teams manually cross-reference PDF invoices against internal ledgers; and compliance teams manually check configuration logs for SOC2 audits. OpsNexus centralizes these operations into a single platform by utilizing an autonomous Supervisor Agent that classifies incoming unstructured documents and routes them to specialized Sub-Agents for automated resolution."

4. **UserProfile role** — "Should UserProfile include a role field?"
   > Yes, add a role field (Recommended)

---

## Prompt 3

*(Answer given after the assistant reported that bringing up the OpsNexus Docker Compose project had accidentally removed an unrelated project's `foresight_postgres` container, and asked how to restore it.)*

> create a new database based on this project requirements

---

## Prompt 4

```
[SYSTEM CONTEXT]
You are scaffolding the AI Integration Layer for "OpsNexus".
- Stack: Python 3, Django 5, Anthropic MCP SDK.

[YOUR TASK: AI MODULARITY & API STUBS]
Execute sequentially and commit after each step.

1. App 4 - `orchestration` (The AI Brain):
   - Create app `orchestration`.
   - Create `router.py`: Write a `DeterministicRouter` class that checks a document's extension/name and returns a mock route (e.g., "sales_rfp").
   - Create `runner.py`: Write an async stub `trigger_mock_agent_run(document_id)`. It should wait 2 seconds, create a mock `AgentRun`, `ToolCall`, and `Answer` in the DB, and update the Document status to "completed".
   - Action: Run `black`/`flake8`. `git commit -m "feat(orchestration): stub deterministic router and async agent runner"`

2. App 5 - `mcp_host` (Model Context Protocol):
   - Create app `mcp_host`.
   - Create `server.py`. Import the `mcp` SDK. Stub an empty resource and one empty tool (`@mcp.tool() def mock_tool(): pass`).
   - Action: Run `black`/`flake8`. `git commit -m "feat(mcp_host): scaffold standalone mcp server skeleton"`

3. API Wiring:
   - In the `documents` app, create a DRF `ModelViewSet` for Documents. 
   - Override `create()`: Save the document, securely spawn a background thread/task calling `trigger_mock_agent_run`, and instantly return a 202 Accepted with `{"status": "processing", "document_id": id}`.
   - Action: Run `black`/`flake8`. `git commit -m "feat(api): implement asynchronous document upload endpoint"`

[EXECUTION CONSTRAINTS]
Zero code redundancy. Ensure imports between apps are clean and circular-dependency free.
```

---

## Prompt 5

```
[SYSTEM CONTEXT]
You are the Lead Frontend Architect for "OpsNexus".
- Stack: Next.js App Router, TypeScript, Tailwind CSS.

[YOUR TASK: FRONTEND MODULARITY & SCAFFOLD]
Execute sequentially and commit after each step.

1. Next.js Init & Structure:
   - Create `/frontend` directory. Initialize Next.js (TypeScript, Tailwind).
   - Create a strict modular folder structure: `src/components/ui` (buttons, cards), `src/components/layout` (sidebar, nav), `src/components/features` (complex logic), `src/lib`, `src/hooks`.
   - Action: `git commit -m "chore(frontend): initialize next.js with strict modular folder architecture"`

2. API Client & Types (`src/lib`):
   - Create `apiClient.ts`. Build a reusable fetch wrapper pointing to `NEXT_PUBLIC_API_URL`. Ensure it handles JSON errors gracefully.
   - Create `types.ts` mirroring our Django models (Document, Answer, ToolCall).
   - Action: `git commit -m "feat(frontend): implement robust api client and typescript interfaces"`

3. Premium UI Components:
   - In `components/ui`, create a glassmorphic `Card`, a primary `Button`, and a `LoadingSpinner`.
   - In `components/layout`, build a premium dark-mode `Sidebar`.
   - Action: `git commit -m "feat(frontend): build reusable dark-mode glassmorphic ui components"`

4. The Dropzone Feature (`src/components/features/Dropzone.tsx`):
   - Build a drag-and-drop file upload component.
   - Wire it so `onChange`, it POSTs to our Django `/documents/` endpoint using `apiClient`.
   - Action: `git commit -m "feat(frontend): implement document dropzone with backend api integration"`

[EXECUTION CONSTRAINTS]
Run `npm run lint`. No messy `page.tsx` files—everything must be composed of smaller modular components.
```

---

## Prompt 6

```
[SYSTEM CONTEXT]
You are finalizing the Week 5 Scaffold for "OpsNexus". 

[YOUR TASK: END-TO-END POLISH & DOCUMENTATION]
Execute sequentially and commit after each step.

1. Dashboard Assembly (`app/dashboard/page.tsx`):
   - Assemble the `Sidebar`, `Dropzone`, and an `AnswerDisplay` component into the main Dashboard layout.
   - Implement UI state polling: After upload, if status is "processing", show a beautiful shimmer effect. Once Django updates to "completed", fetch and display the mock `Answer`.
   - Action: Run `npm run lint`. `git commit -m "feat(frontend): assemble e2e dashboard flow with polling and loading states"`

2. The Architecture README:
   - In the root directory, generate a comprehensive `README.md`.
   - Include: 
     a. Text-based architecture diagram (Next.js -> Django -> Deterministic Router -> Supervisor (Gemini) -> Workers (Groq) -> MCP Server).
     b. Tech choices (Django, Next.js, LangGraph, MCP, ChromaDB, Postgres).
     c. Model selection rationale (Free tier optimization using Groq and Gemini).
   - Action: `git commit -m "docs: generate architectural readme with model selection rationale"`

3. Prompt Logging (`prompts.md`):
   - Ensure `prompts.md` exists in the root. 
   - Add a detailed entry for "Phase 3: Scaffold & Architecture". Log that we used a modular, multi-app Django structure and a strictly typed Next.js component hierarchy to prepare for Agentic integration.
   - Action: `git commit -m "docs: update prompts log for week 5 scaffolding"`

[EXECUTION CONSTRAINTS]
Ensure the system is fully runnable. Provide me a brief summary of how to test the E2E mock upload flow locally.
```

### Phase 3: Scaffold & Architecture

Summary of the approach taken across Prompts 1-6 to prepare this codebase for the
coming agentic integration work:

- **Modular, multi-app Django structure.** The backend is split into five focused
  apps rather than one monolith: `core` (tenancy/BaseModel), `documents` (ingestion),
  `agents` (execution/observability models: `AgentProfile`, `AgentRun`, `ToolCall`,
  `Answer`, `Citation`), `orchestration` (routing + the async agent-runner stub), and
  `mcp_host` (a standalone MCP server skeleton, deliberately kept out of the Django
  request cycle). Each app owns its own models/migrations, and cross-app imports are
  one-directional (e.g. `orchestration` and `documents.views` import `agents`/
  `documents` models, never the reverse) so the dependency graph stays acyclic as more
  apps get added.
- **Strictly typed Next.js component hierarchy.** The frontend enforces the same
  separation on the client: `components/ui` (presentational primitives: `Card`,
  `Button`, `LoadingSpinner`, `Shimmer`), `components/layout` (`Sidebar`),
  `components/features` (business logic: `Dropzone`, `DocumentUploadCard`,
  `AnswerDisplay`), `lib` (typed `apiClient` + `types.ts` mirroring the Django models),
  and `hooks` (`useDocumentPolling`). `page.tsx` files stay thin compositions; all
  TypeScript types for API payloads are hand-mirrored from the DRF serializers so a
  backend field rename is a visible type error on the frontend, not a silent runtime
  bug.
- **Why this matters for what's next:** the mock `DeterministicRouter` /
  `trigger_mock_agent_run` stub in `orchestration` is intentionally isolated behind a
  single async function boundary — swapping it for a real LangGraph-orchestrated
  Supervisor (Gemini) + Worker (Groq) pipeline should mean replacing that one module's
  internals, not restructuring the apps around it. Likewise, the `mcp_host` skeleton
  and the `agents` observability models (`ToolCall`, `Citation`) already have the
  shape a real tool-calling agent loop needs to log into, before any LLM is wired up.

---

## Prompt 7

```
[SYSTEM CONTEXT]
You are the Lead Staff Architect finalizing the Week 5 Scaffold for "OpsNexus".
- Stack: Python 3, Django 5, PostgreSQL.
- Goal: Implement the final missing rubric requirements: Tool Registry, Model Client, Memory stubs, and local Dev infrastructure.

[YOUR TASK: FINAL SCAFFOLD COMPLIANCE & INFRASTRUCTURE]
Execute sequentially and commit after each phase.

1. App 6 - `memory` (Vector Store Stub):
   - Create app `memory`.
   - Create `vector_client.py`. Write a stubbed class `ChromaDBClient`. It should contain stubbed methods for `initialize_collection()`, `add_documents()`, and `semantic_search()`. 
   - Add comments explaining this will interface with local HuggingFace embeddings in Week 6.
   - Action: Run `black .` and `flake8`. `git add .` && `git commit -m "feat(memory): stub chromadb vector memory client"`

2. Tool Registry & Model Client (`orchestration` app):
   - In the `orchestration` app, create `model_client.py`. Write a stubbed `LLMFactory` class that returns mock initializations for `get_supervisor_llm()` (Gemini) and `get_worker_llm()` (Groq).
   - Create `tool_registry.py`. Write a stubbed `ToolRegistry` class that acts as a centralized dictionary to register and fetch LangChain/MCP tools before passing them to the LangGraph agents.
   - Action: Run `black .` and `flake8`. `git add .` && `git commit -m "feat(orchestration): stub centralized tool registry and model client factory"`

3. Local Infrastructure (`docker-compose.yml`):
   - At the root of the repository, create a `docker-compose.yml` file.
   - Configure a `postgres:16` service to run locally for development (mapping port 5432 and setting default dev credentials).
   - Configure a `redis:alpine` service (prep for Week 6/7 Celery background processing).
   - Action: `git add .` && `git commit -m "chore(infra): add docker-compose for local postgres and redis scaffolding"`

4. Final Rubric Verification:
   - Append to `prompts.md`. Note that the Tool Registry, Model Client, and Memory layers were explicitly modularized to separate concerns before Week 6 feature development.
   - Action: `git commit -m "docs: finalize week 5 stub requirements in prompt logs"`

[EXECUTION CONSTRAINTS]
Ensure zero code redundancy. The `docker-compose.yml` must use standard, secure local defaults matching the Django `.env.example`.
```

### Final rubric compliance note

The Tool Registry (`orchestration/tool_registry.py`), Model Client (`orchestration/model_client.py`),
and Memory layer (`memory/vector_client.py`) were explicitly modularized into their
own files/app — rather than, say, inlined into `orchestration/runner.py` — to
separate concerns before Week 6 feature development: which model a role uses
(`LLMFactory`), which tools an agent can call (`ToolRegistry`), and how it retrieves
prior context (`ChromaDBClient`) are three independent axes that Week 6's real
LangGraph agents will each depend on separately, so keeping them as distinct,
independently-swappable stubs now avoids a refactor later.

Local dev infrastructure was also consolidated to a single root-level
`docker-compose.yml` (Postgres + Redis, prepping Week 6/7 Celery background
processing) rather than leaving a second, redundant compose definition inside
`backend/` — one canonical source for local infra, matching the "zero code
redundancy" constraint.

---

## Prompt 8

```
[SYSTEM CONTEXT]
You are the Lead Full-Stack Engineer for "OpsNexus".
- Stack: Next.js 14, Django 5, DRF, ChromaDB. (Linter: `black` and `flake8`).

[YOUR TASK: FIX UPLOADER & IMPLEMENT MEMORY LAYER]
1. Fix Document Uploader (Frontend & Backend):
   - Analyze the Next.js Dropzone component and `apiClient.ts`. Ensure it correctly constructs a `FormData` object and omits the `Content-Type` header (so the browser sets the multipart boundary automatically).
   - Analyze the Django `Document` model and ViewSet. Ensure `MEDIA_URL` and `MEDIA_ROOT` are configured in `settings.py` and `urls.py`. Ensure the ViewSet handles `request.FILES` correctly via a `MultiPartParser`.
2. Memory Layer Integration (`memory/vector_client.py`):
   - Replace the stubbed ChromaDB client with real logic.
   - Use `PyPDFLoader` and `RecursiveCharacterTextSplitter` to extract text from the uploaded `Document.file_path`.
   - Embed the chunks using the free `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`) and store them in a local Chroma collection specific to the `organization_id`.
3. End-to-End Trigger:
   - When a `Document` is uploaded successfully, run the embedding process before calling the agent runner stub.

[EXECUTION CONSTRAINTS]
Run `black .` and `flake8`. Fix any bugs autonomously.
Commit: `git add . && git commit -m "fix: resolve document uploader and implement ChromaDB memory ingestion"`
```

The Dropzone never actually uploaded a file before this: it sent a JSON body with
`file_path` set to just the browser-visible filename string, no bytes ever left
the client, and `Document` had no `FileField` to receive them on the backend even
if it had. Fixed end-to-end: `Dropzone.tsx` now builds a real `FormData` (file
included) and `apiClient.ts` skips the JSON `Content-Type` header for `FormData`
bodies so the browser sets the multipart boundary; `Document` gained a `file`
`FileField` (`file_path` is now derived from it rather than client-supplied), and
`MEDIA_URL`/`MEDIA_ROOT` are wired up in `settings.py`/`urls.py`.

`memory/vector_client.py`'s `ChromaDBClient` is no longer a stub: it wraps a
per-organization `Chroma` collection (`langchain-chroma`, persisted under
`backend/chroma_data/`) embedded locally via `HuggingFaceEmbeddings`
(`all-MiniLM-L6-v2`, `langchain-huggingface`) — no paid API calls. A new
`ingest_document()` function extracts text (`PyPDFLoader` for `.pdf`,
`Docx2txtLoader` for `.docx`, a plain UTF-8 read for other text-bearing files,
skipping undecodable/binary files with a logged warning rather than failing the
upload — confirmed with the user that ingestion should cover any file with
extractable text, not just PDFs), splits it with `RecursiveCharacterTextSplitter`,
and upserts the chunks into a collection named `org_<organization_id>`. This runs
in the existing background thread in `documents/views.py`, wrapped in its own
try/except so an ingestion failure never blocks the existing mock `AgentRun`
pipeline, and executes before `trigger_mock_agent_run` as specified.
