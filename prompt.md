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
  TypeScript types for API payloads are hand-mirrored from the DRF serializers,
  documenting the expected API contract in one place per model. This does *not*
  catch a backend field rename at compile time on its own — TypeScript has no
  visibility into `serializers.py` — it only helps if the interface is updated by
  hand alongside the rename; a real compile-time guarantee would need schema
  generation or contract tests, neither of which exist yet.
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

---

## Prompt 9

```
[SYSTEM CONTEXT]
You are the Lead AI Engineer for "OpsNexus".
- Stack: Python 3, LangGraph, Groq (Llama-3), Gemini 1.5 Flash.

[YOUR TASK: CORE AI FEATURE DEVELOPMENT]
1. LLM Client Factory (`orchestration/model_client.py`):
   - Implement `get_supervisor_llm()` using `ChatGoogleGenerativeAI` (Gemini Flash).
   - Implement `get_worker_llm()` using `ChatGroq` (Llama-3 70B).
   - Ensure graceful fallbacks or error messages if API keys are missing.
2. Tool Registry (`orchestration/tool_registry.py`):
   - Create a real LangChain `@tool` named `search_company_knowledge`. It must use the `ChromaDBClient` from Session 1 to perform semantic searches based on `organization_id`.
3. LangGraph Engine (`orchestration/agent_runner.py` & `graph.py`):
   - Replace the stubbed router. Use the Gemini Supervisor to classify the document. If it's an RFP, route to the Sales Worker.
   - Build the Sales Worker node using Groq. Equip it with the `search_company_knowledge` tool.
   - The Sales Worker must read the document, query ChromaDB for past answers, and synthesize a response.
4. Input/Output Validation:
   - Use Pydantic to strictly type the output of the LangGraph swarm to ensure it returns a structured JSON answer to save into the `Answer` database model.

[EXECUTION CONSTRAINTS]
Run `black .` and `flake8`. Ensure no API keys are hardcoded.
Commit: `git add . && git commit -m "feat: implement primary LangGraph AI feature with Gemini and Groq"`
```

`orchestration/model_client.py`'s `LLMFactory` now returns real clients:
`get_supervisor_llm()` builds `ChatGoogleGenerativeAI`, `get_worker_llm()` builds
`ChatGroq`, both reading their API key from the environment only (never
hardcoded) and raising a new `LLMConfigurationError` with an actionable message
if the key is absent — checked lazily inside each getter so the app still boots
without keys. Both model names in the task spec ("Gemini 1.5 Flash", "Llama-3
70B") have since been retired by their providers; confirmed the current
equivalents live against each provider's real model-list endpoint before
picking `gemini-2.5-flash` and `llama-3.3-70b-versatile`.

`orchestration/tool_registry.py` gained `build_search_company_knowledge_tool
(organization_id)`, a factory returning a real `@tool`-decorated LangChain tool
bound to one organization, backed by `ChromaDBClient.semantic_search` from the
memory layer — bound per-run rather than pre-registered in the generic
`ToolRegistry`, since the LLM shouldn't need to know the org's UUID itself.

`orchestration/graph.py` (new) builds the real `StateGraph`: a `supervisor`
node uses the Gemini client with `.with_structured_output(ClassificationResult)`
to classify the document into one of four routes; a conditional edge sends
`sales_rfp` documents to a `sales_worker` node built with LangGraph's
`create_react_agent` (Groq client + `search_company_knowledge` tool +
`response_format=StructuredAnswer`), giving real tool-calling and strict
Pydantic-typed output in one prebuilt, with no hand-rolled tool loop needed.

`orchestration/agent_runner.py` (new) is the real entry point
(`trigger_agent_run`), replacing `orchestration.runner.trigger_mock_agent_run`
as what `documents/views.py` calls. Per your confirmed choice, only `sales_rfp`
gets the real Worker this round — the other three routes, and any failure
(including missing API keys, via `LLMConfigurationError`), fall back to the
existing `trigger_mock_agent_run` unchanged, so the pipeline always completes
and the fallback is a real functioning path, not just an error message.

Verified live end-to-end with your real `GOOGLE_API_KEY`/`GROQ_API_KEY`: the
graceful-fallback path (keys unset) produces a failed real `AgentRun` plus a
succeeded mock one; a security-questionnaire document classifies as
`sales_rfp` and the Groq worker's `search_company_knowledge` call retrieves
and cites the document's own ingested chunks in its structured answer; an
invoice-shaped document correctly classifies as `invoice_reconciliation` and
skips the worker, leaving `answer` unset so `agent_runner` delegates to the
mock path as designed.

---

## Prompt 10

```
[SYSTEM CONTEXT]
You are the Full-Stack Architect for "OpsNexus".
- Stack: Next.js 14, Django 5, Anthropic MCP SDK.

[YOUR TASK: MCP INTEGRATION & UI WIRING]
1. MCP Server Implementation (`mcp_host/server.py`):
   - Replace the MCP stub. Build a real tool `get_internal_pricing_policy()` that returns a hardcoded mock JSON string representing the company's pricing rules.
   - Create the MCP Client wrapper in Django so the Groq Worker agent can securely call this tool during the LangGraph loop.
2. User-Facing Surface Wired to Live Logic:
   - Update the Next.js Dashboard (`app/dashboard/page.tsx`).
   - Ensure the UI beautifully renders the *real* structured JSON output from the AI (e.g., displaying the generated RFP answers in a clean card layout).
   - Add error boundaries: if the AI fails (e.g., API rate limit), Next.js must catch the 400/500 error from Django and show a graceful error toast, not a crashed white screen.

[EXECUTION CONSTRAINTS]
Run `npm run lint` and `flake8`. Verify the full E2E path (Upload -> Agent -> UI).
Commit: `git add . && git commit -m "feat: integrate MCP server tools and wire live AI logic to Next.js UI"`
```

`mcp_host/server.py`'s `mock_tool` is now `get_internal_pricing_policy()`, returning a
hardcoded JSON pricing-tiers document (Starter/Growth/Enterprise). The obvious
"MCP → LangChain tool" bridge, `langchain-mcp-adapters`, turned out to pin
`mcp<2.0.0` -- incompatible with this repo's `mcp==2.0.0` (which
`mcp_host/server.py`'s `MCPServer` API requires). Installing it would have forced
a downgrade that broke the existing server, so `mcp_host/client.py` (new) hand-rolls
the bridge instead directly against `mcp.ClientSession` -- `mcp_session()` spawns
the server over stdio, `build_mcp_tools()` wraps each MCP tool as a LangChain
`@tool`. `orchestration/graph.py`'s `sales_worker_node` (now async, using `.ainvoke`
throughout) opens that session for the Worker's whole tool-calling lifetime and adds
the MCP tools alongside `search_company_knowledge`, with a try/except fallback to
just the search tool if the MCP server is unreachable -- mirroring the missing-API-key
graceful-degradation pattern already established for the LLM clients.

While reading `documents/views.py` for this task I found a real gap: if the real graph
*and* its internal mock fallback both raised, nothing ever set `Document.status =
FAILED` -- the document would stay stuck at its prior status forever with the
dashboard shimmering indefinitely, no crash but no signal either. Fixed that as part
of closing the loop on "the frontend must be able to catch and show AI failures."

The dashboard's `AnswerDisplay`/`Meter` card was already built in Week 5 to render
structured `Answer` data -- now that it's fed real Gemini/Groq output instead of the
mock, no redesign was needed there. The actual gap was error handling: request
failures were either inline-only (`Dropzone`) or silently swallowed
(`useDocumentPolling`, the `/answers/` fetch), and nothing protected against an
uncaught render crash. Added `app/dashboard/error.tsx`, a Next.js route error
boundary using the `error`/`retry` props -- confirmed against
`node_modules/next/dist/docs` per this project's `AGENTS.md` (this app's Next.js
16.3.0 stabilized `retry` recently; older docs would have said `reset`). Built a small
`ToastProvider`/`useToast()` (new `contexts/ToastContext.tsx` + `components/ui/Toast.tsx`,
reusing the existing `status-critical`/`status-warning` color tokens) and wired
`showError()` into every previously-silent fetch failure, plus the new `status ===
"failed"` transition, so a genuine AI/backend failure now surfaces as a toast instead
of a silent hang.

Verified end-to-end: standalone graph invocation confirmed the Worker actually calls
`get_internal_pricing_policy` and cites its exact figures in the generated answer;
the full HTTP-upload path (through the real `DocumentViewSet` and background thread)
produced a correct `ToolCall` + `Answer` in the database; temporarily pointing the MCP
client at a nonexistent server script confirmed the graceful fallback still produces
a valid (if less complete) answer using only `search_company_knowledge`; `npm run
build` and `npx tsc --noEmit` both pass clean. Browser automation (`gstack`'s
`/browse`) is blocked by this machine's Windows Application Control policy, matching
what was already found earlier in this project -- verified the rendered dashboard
HTML directly via `curl` instead.

---

## Prompt 11

```
[SYSTEM CONTEXT]
You are the QA Lead for "OpsNexus". We are finalizing Week 6.
- Stack: Python 3, Pytest, `pytest-django`, `factory_boy`.

[YOUR TASK: TESTING & RUBRIC FINALIZATION]
1. Pytest Suite (≥70% Core Logic Coverage):
   - Write comprehensive tests in `orchestration/tests/` and `documents/tests/`.
   - Test the Document Upload API endpoint (mocking the file).
   - Test the Deterministic Router / Supervisor logic (mocking the LLM response).
   - Test the Pydantic Output Validation logic (pass invalid JSON and assert it fails gracefully).
2. Error Handling Audit:
   - Scan the `agent_runner.py`. Ensure `try/except` blocks wrap all LLM invocations. If Groq times out, the `Document` status must be updated to "failed", and a clean error saved to the database.
3. Prompt Log Update:
   - Append to `prompts.md`. Add a "Week 6: Core Feature Development" section. Log the implementation of LangGraph, the ChromaDB ingestion pipeline, and the Pytest suite.

[EXECUTION CONSTRAINTS]
Run `pytest --cov=orchestration --cov=documents` (or standard `pytest` if coverage plugin is missing) to ensure tests pass. Run `black .` and `flake8`.
Commit: `git add . && git commit -m "test: implement core logic test suite and finalize week 6 documentation"`
```

The audit surfaced a real bug: `sales_worker_node`'s `try/except` wrapped both the MCP
session setup *and* the actual Groq agent call in one block, so a Groq failure got
mislogged as "MCP server unavailable" and triggered a pointless retry of the same
failing call before it finally propagated. Fixed by restructuring with
`contextlib.AsyncExitStack` -- the MCP session enter + tool listing gets its own narrow
`try/except` (graceful fallback to `search_company_knowledge` alone), while the actual
agent invocation is now unambiguous and wraps its own failure into a new
`SalesWorkerError`, never conflated with MCP availability.

That surfaced a policy question, confirmed with you: two sessions ago, *any* AI failure
(Gemini or Groq) fell back to the mock pipeline so `Document.status` still landed on
`completed`. This task explicitly wants a Groq failure to mark the document `failed`.
Resolution: only a **Worker** (Groq) failure now marks `Document.status = FAILED` with a
clean error message -- this only fires *after* the Supervisor already classified the
document `sales_rfp`, so a real answer was owed and didn't silently get swapped for a
generic mock one. A **Supervisor** (Gemini) failure, or anything unexpected before the
route is even known, still falls back to mock exactly as before.

Built the actual pytest suite: `backend/pytest.ini` (nothing configured
`DJANGO_SETTINGS_MODULE` before this, so bare `pytest` couldn't even run), `core/factories.py` /
`documents/factories.py` / `agents/factories.py` (`factory_boy`, used across every test
rather than hand-built model instances), and two new test packages --
`orchestration/tests/` (router, Pydantic schema validation with malformed JSON, the
Supervisor/Worker LangGraph nodes with the LLM mocked, `LLMFactory`'s missing-key
errors, the tool registry, `trigger_mock_agent_run`, and `trigger_agent_run`'s full
branching -- Worker failure, Supervisor failure, unexpected failure, successful
`sales_rfp`, and non-`sales_rfp` fallback) and `documents/tests/` (replacing the old
stub `tests.py` -- the upload endpoint with a mocked `SimpleUploadedFile` and the
background thread patched out, the `answers` action, and the background-thread
function's own success/ingestion-failure/total-failure paths). 61 tests, 99% coverage
on `orchestration`/`documents` combined -- well past the 70% target.

### Week 6: Core Feature Development

Summary of what Week 6 (this session plus the two before it) actually built, since
this task asked for it logged explicitly:

- **LangGraph engine** (`orchestration/graph.py`, `agent_runner.py`, `model_client.py`,
  `tool_registry.py`): a real Gemini Supervisor node classifies uploaded documents into
  one of four routes; for `sales_rfp`, a real Groq Sales Worker (LangGraph
  `create_react_agent`, Pydantic-typed `response_format`) drafts a response using two
  tools -- `search_company_knowledge` (backed by the org's ChromaDB collection) and the
  MCP-hosted `get_internal_pricing_policy`. Every other route, and any Supervisor-side
  failure, falls back to the pre-existing deterministic mock pipeline so the system
  always completes; a Worker-side failure now fails cleanly instead.
- **ChromaDB ingestion pipeline** (`memory/vector_client.py`): uploaded documents are
  text-extracted (PDF/docx/plain-text), chunked, embedded locally via
  `HuggingFaceEmbeddings` (no paid API), and stored in a per-organization Chroma
  collection, run automatically in the background right after upload and before the
  agent pipeline -- this is what `search_company_knowledge` actually searches.
- **Pytest suite** (this task): `orchestration/tests/` and `documents/tests/`, 61 tests,
  99% coverage on the two target packages, using `pytest-django` + `factory_boy` as
  specified.

---

## Prompt 12

```
[SYSTEM CONTEXT]
You are the Lead Full-Stack Engineer for "OpsNexus".
- Stack: Next.js 14, Tailwind, Zod, Django 5, DRF.
- Goal: Fulfill the "Complete CRUD operations" and "Input validation" requirements for Week 6.

[YOUR TASK: COMPLETE CRUD & ZOD VALIDATION]
1. Backend CRUD Operations (`documents/views.py`):
   - Ensure the `DocumentViewSet` supports `list`, `retrieve`, and `destroy`.
   - Update the `list` method to return documents ordered by newest first (`-created_at`). Ensure soft-deletes are respected (if implemented).
2. Frontend File Validation (Zod):
   - In the Next.js Dropzone component, implement strict client-side validation using Zod.
   - Constraints: Accept ONLY `.pdf`, `.csv`, or `.xlsx`. Max file size: 10MB.
   - Display beautiful, red inline error toasts if the user tries to upload an invalid format or oversized file.
3. Frontend Historical Dashboard (`app/dashboard/page.tsx`):
   - Build a "Recent Runs" data table below the dropzone.
   - Use `apiClient.ts` to `GET /api/v1/documents/` and list historical document runs, showing their `doc_type`, `status`, and upload date.
   - Add a "Delete" (trash can) button next to each row that sends a `DELETE` request to the backend and dynamically removes the row from the UI.

[EXECUTION CONSTRAINTS]
Run `npm run lint`, `black .`, and `flake8`.
Commit: `git add . && git commit -m "feat: implement complete document CRUD UI and strict Zod file validation"`
```

Two things needed clarifying before touching code, confirmed with you: the task
referenced `GET /api/v1/documents/`, but the app has always used `/api/documents/`
(no version prefix) and every existing frontend caller depends on that path -- kept
it unversioned rather than doing an unrequested, wide routing refactor for a single
consumer. And `deleted_at` (inherited by every model from `BaseModel` since the very
first scaffolding session) had never actually been wired up anywhere -- confirmed
implementing real soft-delete rather than a literal hard `DELETE`, since that's
clearly what the field was scaffolded for and means a delete click doesn't destroy
the file/answer trail.

`documents/views.py`'s `DocumentViewSet` gained a `get_queryset()` (excludes
soft-deleted rows, orders `-created_at`, optionally filters by `?organization=<uuid>`
-- necessary so the new frontend table doesn't leak another tenant's documents,
a real isolation concern given this app's multi-tenant `BaseModel` design) and a
`destroy()` override that sets `deleted_at` instead of removing the row. `list`,
`retrieve`, and the existing `answers` action all now route through the same
soft-delete-aware queryset.

Added `zod` as a direct dependency (previously only present transitively via
`eslint-config-next`) and `lib/fileValidation.ts`: an extension-based schema (not
MIME-type, which browsers report inconsistently for `.csv`/`.xlsx`) plus a 10MB size
check. `Dropzone.tsx` runs this before ever building the `FormData` -- an invalid
file gets the existing inline red error treatment *and* a toast via the toast system
built two sessions ago, with zero network request made.

New `RecentRunsTable.tsx` mounted in `DashboardContent.tsx` below the upload card:
fetches `GET /documents/?organization=<id>`, refetching whenever the org changes or a
`refreshKey` counter (bumped on every successful upload) changes, so a fresh upload
appears without a manual reload. Each row has a trash-can button
(`apiClient.delete()`, new method added to `apiClient.ts`) that removes the row from
local state immediately on success -- no refetch -- matching the task's literal
"dynamically removes the row" ask.

Extended `documents/tests/test_views.py` with new `TestDocumentListEndpoint`,
`TestDocumentRetrieveEndpoint`, and `TestDocumentDestroyEndpoint` classes covering
ordering, organization filtering, soft-delete exclusion from list/retrieve, and that
the row survives with `deleted_at` set rather than actually being removed. Full
suite: 70 tests, 99% coverage on `orchestration`+`documents`. Verified live via curl
against the real Postgres-backed server: two documents under one org list
newest-first, a second org's document never leaks into the first org's filtered
list, and deleting one confirms all three soft-delete properties end-to-end (gone
from list, 404s on direct retrieve, row still present in the database with
`deleted_at` populated).

---

## Prompt 13

```
[SYSTEM CONTEXT]
You are the UX/UI Architect for "OpsNexus".
- Stack: Next.js 14, Django 5, DRF.
- Goal: We are preparing for a Live Mentor Demo. The mentor needs to physically see the AI's "Chain of Thought" and tool executions on the screen.

[YOUR TASK: VISUALIZING THE AGENT TRACING LAYER]
1. Backend Tracing Exposure (`agents/views.py`):
   - Create an endpoint `GET /api/v1/agent-runs/{id}/tool-calls/`.
   - This endpoint must return all `ToolCall` database records associated with an `AgentRun`, ordered chronologically. This includes the `tool_name`, `tool_input` (JSON), and `tool_output` (JSON).
2. Frontend Trace Component (`src/components/features/AgentTraceViewer.tsx`):
   - Build a sleek, expandable "Agent Thought Process" accordion or sidebar component.
   - When a document is processing (or completed), fetch and render the `ToolCall` logs.
   - Use premium UI styling: e.g., a timeline view showing `[Supervisor routed to Sales Worker] -> [Sales Worker executed ChromaDB search] -> [Sales Worker called MCP Server]`.
3. Final Polish:
   - Integrate this component into the `Customer 360` or `Dashboard` detail view.
   - Review `prompts.md`. Append a log stating we implemented Full CRUD operations, Zod input validation, and an Agent Trace UI to finalize Week 6.

[EXECUTION CONSTRAINTS]
Run `npm run lint`. Fix any TypeScript type mismatches for the new JSON logs.
Commit: `git add . && git commit -m "feat: expose tool-call tracing logs to frontend for live agent visualization"`

---

## Prompt 14

```
[SYSTEM CONTEXT]
You are a Lead Backend Architect for "OpsNexus".
- Stack: Django 5, DRF, PostgreSQL, ChromaDB.
- Goal: Fix critical memory desync bugs and abstract the file storage for cloud readiness (Core Week 6).
- Constraints: No Celery/Redis yet. Use `black` and `flake8` for linting.

[YOUR TASK: MEMORY SYNC & CLOUD STORAGE ABSTRACTION]
1. ChromaDB Desync Fix (`documents/signals.py`):
   - When a `Document` is deleted (or soft-deleted) via the DRF API, its vectors remain in ChromaDB, causing the agent to retrieve ghost data.
   - Implement a Django `post_delete` (and/or `post_save` for soft-deletes) signal. 
   - When triggered, this signal must call the `ChromaDBClient` to permanently delete all vector embeddings associated with that specific `document_id`.
2. Cloud Storage Abstraction (`settings.py` & `requirements.txt`):
   - Local file uploads will break on ephemeral cloud servers. Add `django-storages` to requirements.
   - Refactor the Django settings to use a custom storage backend. Use `FileSystemStorage` for local development, but structure the code so we only need to flip an environment variable (`USE_S3=True`) to switch to Amazon S3 in the upcoming deployment phase.
   - Ensure the `Document` model's `FileField` utilizes this abstracted storage.

[EXECUTION CONSTRAINTS]
Run `black .` and `flake8`. Write a quick Pytest in `documents/tests/` to verify that deleting a Document also triggers the ChromaDB deletion method.

---

## Prompt 15

```
[SYSTEM CONTEXT]
You are a Lead AI Engineer for "OpsNexus".
- Stack: Python 3, LangGraph, Django 5.
- Goal: Upgrade the Agent's structured output to enterprise B2B standards (Core Week 6).

[YOUR TASK: GRANULAR STRUCTURED OUTPUTS]
1. Pydantic Schema Upgrade (`orchestration/schemas.py`):
   - The final Sub-Agent output must be highly structured. Update the Pydantic schema to include:
     - `executive_summary` (str)
     - `risk_flags` (list of strings, e.g., ["High Churn Risk", "Missing SOC2 Policy"])
     - `action_items` (list of strings, e.g., ["Email CFO", "Request updated invoice"])
     - `confidence_score` (float)
2. Database Mapping (`agents/models.py`):
   - Update the `Answer` model to physically store these fields (use `JSONField` for lists). 
3. LangGraph Enforcement:
   - Update the Groq Sub-Agents to strictly conform to this new Pydantic schema using the `.with_structured_output()` method (or equivalent tool-calling enforcement).
   - When the agent finishes, ensure the Django runner saves these granular fields into the `Answer` row correctly.

[EXECUTION CONSTRAINTS]
Run `black .` and `flake8`. Run `python manage.py makemigrations` and `migrate` for the new `Answer` model fields. Ensure no data is lost during migration.

---

## Prompt 16

```
[SYSTEM CONTEXT]
You are a Lead UI/UX Architect for "OpsNexus".
- Stack: Next.js 14, Tailwind CSS, TypeScript.
- Goal: Elevate the UI to Enterprise SaaS standards, utilizing the new structured AI data (Core Week 6).

[YOUR TASK: SPLIT-PANE UI & STRUCTURED RENDERING]
1. Integrated Split-Pane Viewer (`app/dashboard/document/[id]/page.tsx`):
   - Replace the basic document view with an Enterprise Split-Pane layout (e.g., using Tailwind grid/flex).
   - Left Pane: Embed an `iframe` or PDF Viewer component that displays the raw uploaded document directly in the browser. (Ensure it uses the secure file URL from Django).
   - Right Pane: The "Agent Intelligence" panel.
2. Structured Data Rendering:
   - Update `apiClient.ts` and the frontend TypeScript interfaces to expect the new `risk_flags` and `action_items` arrays.
   - In the Right Pane, do not just render text. 
   - Render `risk_flags` as prominent red/yellow warning badges (Chips).
   - Render `action_items` as a beautiful Checklist UI (with empty circles next to them, mimicking a task manager).
   - Render the `executive_summary` as the main text block.

[EXECUTION CONSTRAINTS]
Run `npm run lint`. Ensure the split-pane layout is fully responsive (stacks vertically on mobile, side-by-side on desktop). Maintain the premium dark-mode, glassmorphic design system.