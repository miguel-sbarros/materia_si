# CLAUDE.md — Captus CRM

Project instructions for Claude Code. Merge with `~/.claude/CLAUDE.md` (global). Read this before working in this repo.

## What this is

**Captus** — a CRM purpose-built for the education sector, mixed with a "Sales Context System". Client: **MR Digital**, a USP-affiliated company selling presential digital-implantology courses in limited-seat cohorts (turmas). The differentiator vs generic CRMs: leads, courses, cohorts, and seats are integrated, AI is native, and a lead can sit at **different commercial stages for different cohorts/courses** (one `deal` per lead × cohort).

Built for the discipline **PRO3151 — Laboratório de Sistemas de Informação** (Grupo 10). The requirements/grading rubric is `PRO3151 - Laboratório de Sistemas de Informações - Relatório do Trabalho da disciplina - Grupo 10.md` — treat its acceptance criteria as the source of truth and as test assertions.

## Features (priority order)

1. **Functional Kanban backed by the database** (REQF01 cadastrar leads, REQF02 pipeline + history).
2. **Import WhatsApp-exported chats** — v0 of a future WhatsApp Business API integration (REQF03).
3. **Chat analysis → structured `LeadProfile`** (persona, pains, desires, score) (REQF08).
4. **Copilot agent** — advises the *seller* how to respond, via RAG over course materials + the lead's history & profile.
5. **Campaigns** — find leads that fit a given course and message them.

## Master plan

The phased development plan lives at `~/.claude/plans/estou-construindo-um-projeto-woolly-kazoo.md`. Phases P0–P5 map to the features above; each phase ships a runnable system. **Use the `/plan` command to scope each next step** (it interviews you first).

## Build status — Phase 0 DONE (read this before the next phase)

Phase 0 (foundations + CI) is built and verified: `docker compose up` boots db+backend+frontend, `/health` is green, `pytest` is 8/8, `ruff` clean, seed is idempotent. Authoritative spec: `specs/p0-foundations.md`. P0 step plan: `~/.claude/plans/shimmering-coalescing-hedgehog.md`.

### Repo layout (enacted)

- **All deployable code under `src/`**: `src/backend/` (FastAPI app) and `src/frontend/` (React, moved via `git mv`). Root keeps context/infra: `docker-compose.yml`, `specs/`, `.github/`, `data/`, `.claude/`, `plans/`, `prototype/`, `playbook/`, docs.
- Backend tree: `src/backend/app/{core,db,models,schemas,services/llm,api/routes}` · `scripts/seed.py` · `tests/` · `alembic/`. `pyproject.toml` (deps + ruff + pytest config), `Dockerfile`, `alembic.ini`, `.env.example`.

### What exists now

- **Layered FastAPI skeleton**: `app/main.py` (`create_app()` factory + CORS), `GET /health` → `{"status":"ok","db":"ok"}`. `app/core/config.py` = `Settings` (pydantic-settings); `app/db/session.py` = sync engine + `SessionLocal` + `get_db` dependency.
- **DB schema** via migration `alembic/versions/0001_core_deal.py` (+ `CREATE EXTENSION vector`). Tables: `users, courses, cohorts, leads, deals, deal_events`. **`schemas/` and `services/` are placeholders** — request/response models and business logic land from P1 on.
- **Enums** in `app/core/constants.py`: `UserRole(seller|admin)`, `DealStage(Novo|Contatado|Negociando)`, `DealStatus(open|won|lost)`, `CohortStatus(open|active|finished)` — all `StrEnum`. Stored as **VARCHAR + CHECK** (`native_enum=False`, value-not-name) via the `enum_column()` helper in `app/db/base.py`.
- **LLM wrapper**: `app/services/llm/client.py::get_client()` (official `anthropic` SDK). No live calls yet.
- **Test harness** (`tests/conftest.py`) + 8 tests (`test_health`, `test_models`, `test_anthropic_fixture`).
- **Idempotent `scripts/seed.py`**, root **`docker-compose.yml`** (db/backend/frontend), **CI** (`.github/workflows/ci.yml`: lint+test on a pgvector service, docker build, compose-up `/health` smoke).

### Schema as built (authoritative — `deal: lead → cohort`)

- `users(id, name, role UserRole, email UNIQUE, initials, active, created_at)`.
- `courses(id, name UNIQUE, description, modality, price Numeric(10,2), duration, active)`.
- `cohorts(id, course_id FK, name, start_date, end_date, capacity, price_per_slot Numeric, status CohortStatus)`.
- `leads(id, name, email?, phone, source, assignee_id FK→users, external_user_id? UNIQUE, created_at, updated_at)` — **no funnel field**; partial-unique index `uq_leads_email_present` on `email WHERE email IS NOT NULL` (REQF01 dedupe).
- `deals(id, lead_id FK, cohort_id FK, stage DealStage, status DealStatus, lost_reason?, created_at, updated_at)` — `UNIQUE(lead_id, cohort_id)`; CHECK `status<>'lost' OR lost_reason IS NOT NULL`; **no `course_id`** (use `deal.cohort.course`).
- `deal_events(id, deal_id FK, from_stage?, to_stage?, from_status?, to_status?, reason?, user_id FK→users, ts)` — captures both stage moves and terminal won/lost transitions (REQF02 history); `Deal.events` ordered by `id`.

### Decisions locked in P0 (do not silently change)

- **Stage + status split.** The Kanban contract (`mock.js`) shows flat columns; the **API must map `status=won → "Matriculado"` and `status=lost → "Perdido"`**, otherwise show `stage`. The Funil board renders **deals** (cards), filter-by-course = join `deals→cohorts→courses`, filter-by-turma = `cohort_id`. P1 must implement this mapping so the frontend contract stays byte-identical.
- **Schema breadth**: only core+deal tables now. `conversations, messages, lead_profiles, lead_course_fit, knowledge_chunks, campaigns` are **additive future migrations** (`down_revision` chains off `0001_core_deal`).
- **Roles**: seeded `admin` = Prof. Marcelo Romano, `seller` = Dra. Ana Costa (the mock's `currentUser`). Role enforcement is part of the deferred auth.
- **Test DB**: real Postgres/pgvector. `conftest` derives `<db>_test` from `DATABASE_URL` (or `TEST_DATABASE_URL`), auto-creates it, enables `vector`, and uses `Base.metadata.create_all` (not migrations) for the test schema.
- **Migration** `0001_core_deal` is hand-written with frozen literals (don't autogenerate over it).
- **Deferred to P4 (not installed yet)**: `pgvector` Python package + `sentence-transformers`. Only the DB extension is enabled. Anthropic SDK resolved to `0.111.x` at build; the wrapper + test mock are version-agnostic.

### Patterns the next phase MUST follow

- **New model** → add the file under `app/models/`, **import it in `app/models/__init__.py`** (so `create_all` + Alembic autogenerate see it), then write a **new Alembic revision** (`down_revision="0001_core_deal"`).
- **New endpoints** → thin router in `app/api/routes/`, included in `create_app()`; all DB/LLM logic in `app/services/`.
- **Tests (TDD, write first)** use these fixtures: `db_session` (savepoint-rollback isolation — for `IntegrityError` cases use `with db_session.begin_nested():` so the session stays usable), `client` (FastAPI `TestClient`; `/health` hits the real DB), `mock_anthropic` (monkeypatches `app.services.llm.client.get_client`; call `mock_anthropic.set_return(<pydantic instance>)` to script `messages.parse`).
- Conventions section below still holds: PT in user-facing strings/docstrings, English identifiers, money `Decimal`/`Numeric`, idempotent imports.

### Immediate next step

Frontend foundation + P1 Kanban: typed API client + TanStack Query + Login/auth context in `src/frontend/`, and the `GET/POST /leads`, `GET /leads/{id}`, deal-stage `PATCH` (writes `deal_events`) endpoints. Scope it with `/plan`.

### Copiloto page (Feature 4 UI — built ahead, mock-only)

The `/copiloto` page was adapted from the Claude-Design prototype (`prototype/Copiloto WhatsApp.dc.html` + `prototype/PRD Copiloto WhatsApp.dc.html`) ahead of its backend phase. **Frontend-only, runs entirely on mocks; the real LLM backend is P4.** Spec: `specs/copilot.md`.

- Lives in `src/frontend/src/`: `pages/Copiloto.jsx` (container) · `hooks/useCopilot.js` (useReducer state) · `components/copiloto/{EmptyState,Composer,MentionMenu,CommandMenu,LeadContextChip,MessageList,DraftCard}.jsx` · `data/copilot.js` (mock leads/drafts/KB/commands) · `lib/copilotApi.js`.
- **`lib/copilotApi.js` is the backend-swap seam** — async fns mirroring the PRD routes/contracts: `searchLeads(q)` → `GET /api/leads?q=`, `getLeadContext(id)` → `GET /api/leads/{id}/context`, `postCopilotChat({messages,leadId,command})` → `POST /api/copilot/chat`. P4 replaces the mock bodies with real fetches (LLM-generated `drafts` = Análise + tone variants); the page/components don't change. Contracts `Lead`/`Message`/`Draft` are JSDoc'd in the seam + `specs/copilot.md`. **Note:** this advisory copilot is distinct from the seller `SellerAdvice` planned in the master plan P4 — reconcile the two when P4 is scoped.
- Behavior: `@` attaches a lead (profile + history → context), `/` runs slash-commands, responses are KB text or draft cards (3 tones, copy-to-clipboard).
- The committed `.vite/` build cache was untracked + gitignored during this work; `eslint.config.js` now ignores `.vite`.

## Design principles (non-negotiable for grading)

- **Dockerization** — everything runs via `docker compose up`.
- **Layered architecture** — front / back / db; within the backend: `api → services → models/db`. Routers stay thin; services own DB + LLM access. No `repositories/` layer (SQLAlchemy is the data layer at this scale).
- **TDD** — write or extend a test for **every** change. Red → green → refactor.
- **CI/CD** — GitHub Actions: `ruff` + `pytest` + `docker build` + a compose-up `/health` smoke test.
- **Spec-Driven Development** — before building a feature, write `specs/<feature>.md` (acceptance criteria + schema + test cases). The spec's criteria become pytest assertions.

## Stack

- **Backend**: Python · FastAPI · SQLAlchemy 2.0 (**sync**) · Alembic · Pydantic v2 · pgvector. Bulk import/analysis via `FastAPI BackgroundTasks` (no Celery/Redis).
- **DB**: PostgreSQL with the `pgvector` extension (`pgvector/pgvector:pg16` image).
- **Frontend**: React 19 · Vite · React Router 7 · Tailwind v4 · Recharts · @dnd-kit · TanStack Query (server state) · lucide-react. Lives in `src/frontend/` (all deployable code lives under `src/`; backend in `src/backend/`).
- **LLM**: Anthropic Claude via the official `anthropic` SDK.
- **Embeddings**: `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`, 384-dim). Dim is a config constant (`EMBEDDING_DIM`).

## Reuse from `sales_context_system/` (the old "Octo" project)

That sibling project targeted the same client with a multi-agent SPIN pipeline on Neo4j + LangGraph (Neo4j was a dead end). **Port the assets, not the runtime:**

| Asset | Path | Use |
|-------|------|-----|
| Pydantic schemas | `app/models/graph_schemas.py` | `ExtractedEntities`, `PersonaAssessment`, `PersonaType` (4 personas), `StrategicPlan`, `SPINStage` — port verbatim. |
| Prompts | `app/agents/prompts.py` | Extraction prompt + 7 PT few-shots (reuse as-is); Tactical/Writer prompts (reframe auto-responder → **seller-advisory**). |
| Knowledge graph | `neo4j_query_table_data_2025-9-21.json` | 112 nodes (incl. 20 persona-tagged `Script`s) + 162 relationships → chunk into the pgvector RAG store. |
| WhatsApp parser | `export_msgs/wpp2db.py` | `_chat.txt` regex `[DD/MM/YYYY, HH:MM:SS] ~Sender: msg` (tilde = lead); drop SQLite/Whisper. |
| DB design | `app/prisma/schema.prisma` | Entity reference: `Pipeline`/`EventoPipeline` → re-implemented in SQLAlchemy as **`deals`/`deal_events`** with grain `deal: lead → cohort` (course via cohort); `LeadCursoFit` + `Campanha` land in later phases. |

The frontend `src/frontend/src/data/mock.js` is the **API contract** every endpoint must satisfy.

## Data (import corpora)

- `data/Chats_21-01-2026/` — **real** WhatsApp exports (`.zip` with `_chat.txt` + media PDFs, some pre-extracted). Format `[DD/MM/YYYY, HH:MM:SS] ~Sender: msg` (tilde = lead). **Carry timestamps** → use for time-series Analytics. Parse via the ported `wpp2db.py` path.
- `all_chats.json` — 75 conversations as `[{user_id, messages:[{role,content}]}]` (role `user`=lead, `assistant`=seller). Structured, **no timestamps** — quick import demo alternative.

## Domain model: two distinct "stage" concepts (never conflate)

- **Commercial deal stage** (Kanban/Funil): the funnel position, per **deal** — and a `deal: lead → cohort` (the course is reached *through* the cohort; no `course_id` on the deal). `stage` ∈ Novo → Contatado → Negociando; terminal `status` **won** (API maps → Matriculado) / **lost** (→ Perdido, + required `lost_reason`); `UNIQUE(lead_id, cohort_id)`. Lives on `deals`; every change is logged to `deal_events` (REQF02). A lead holds **multiple deals over time** across cohorts of the same or different courses. (Locked in `specs/p0-foundations.md`.)
- **SPIN stage** (conversation/message analysis): Situação → Problema → Implicação → Necessidade. A property of the *dialogue*, produced by analysis & copilot (`SPINStage`, ported from Octo). Lives on the conversation / `lead_profiles` / `SellerAdvice` side — **never** on the Kanban.

## LLM rules

- Use the **official `anthropic` Python SDK** — never raw HTTP, never an OpenAI-compatible shim.
- Default model **`claude-opus-4-8`** (copilot/advisory). Use **`claude-haiku-4-5`** for cheap, high-volume extraction.
- Structured output: `client.messages.parse(model=..., output_format=<PydanticModel>)`. Validate against the schema — do not raw-string-parse tool/JSON output.
- Adaptive thinking for hard reasoning: `thinking={"type": "adaptive"}`. Stream when `max_tokens` is large.
- **Never hardcode keys.** `ANTHROPIC_API_KEY` from env/`.env` (gitignored).
- **Tests mock the Anthropic client** (return real Pydantic instances); live calls go behind `@pytest.mark.integration`.

## Conventions

- **Language**: Portuguese in user-facing strings, domain docstrings, and CLI/log messages; English in code identifiers (snake_case / CamelCase). Mirrors the sibling repos.
- **Encoding**: UTF-8 always.
- **Idempotency**: imports and the knowledge-base ingestion must be safely re-runnable (upsert on natural keys).
- **Money**: `Decimal`, never float.
- **Surgical changes**: every changed line traces to the requested task; don't refactor adjacent code unasked.

## Common commands

```bash
docker compose up                 # boot db (pgvector) + backend + frontend
docker compose exec backend pytest            # run tests
docker compose exec backend pytest -m integration   # live-LLM tests (needs key)
docker compose exec backend alembic upgrade head    # migrate
docker compose exec backend python scripts/seed.py            # seed demo data
docker compose exec backend python scripts/ingest_knowledge.py # build RAG store
cd src/frontend && npm run dev    # frontend dev server
cd src/frontend && npm run lint   # eslint
```

## Deferred / noted (don't silently "fix")

- **REQNF04 (JWT) / REQNF05 (RLS)** are deferred — auth is a simple login demo, no JWT, per decision. Cheap later upgrade: real JWT from `/auth/login` + one `org_id` RLS policy. Flag before final submission.
- **Analytics time-series** (REQF08 "tempo de resposta") degrade gracefully — `all_chats.json` has no timestamps; only `_chat.txt` imports carry them.
- **BM25 + RRF retrieval** is deferred; the `tsvector` column is built ahead so it's an additive query, not a migration.
