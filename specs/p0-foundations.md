# Spec — P0: Fundações de backend/infra + CI

> Plano-fonte: `~/.claude/plans/shimmering-coalescing-hedgehog.md`.
> Princípios de avaliação exercidos: **Dockerização, Arquitetura em camadas, TDD,
> CI/CD, Spec-Driven Development**.

## Requisito / contexto

Transforma o protótipo mock (Ciclo 1) em um sistema **dockerizado em camadas**
(front / back / db). Esta etapa entrega só a **fundação**: esqueleto FastAPI, modelo
de dados core+deal, migração Alembic, seed, harness de testes (com fixture
mock-Anthropic) e CI. Sem endpoints de feature nem chamadas LLM (isso é P1–P5).

- **REQF01** (cadastrar leads): `leads` carrega nome/email/telefone/origem; índice
  único parcial em `email` impede duplicidade "quando aplicável" (rubric l.163).
- **REQF02** (gerenciar pipeline): a posição no funil é por **deal** (lead × cohort,
  e portanto por curso); `deal_events` registra cada mudança no histórico (l.171).
- **REQF05** (controle de vagas, futuro): grão `deal → cohort` faz a ocupação da turma
  = contagem de deals `won` daquela turma.

## Escopo

**Entra:** `src/` (código separado de contexto/IA), backend em camadas
(`api → services → models/db`), tabelas `users, courses, cohorts, leads, deals,
deal_events` + extensão `vector`, migração `0001_core_deal`, `seed.py` idempotente,
`docker-compose.yml` (db+backend+frontend), CI (ruff + pytest + docker build + smoke
`/health`).

**Não entra (diferido):** wiring do frontend (API client, TanStack Query, Login/auth)
→ próxima etapa; tabelas `conversations/messages/lead_profiles/lead_course_fit/
knowledge_chunks/campaigns` → suas fases; `sentence-transformers` + pacote `pgvector`
→ P4; REQNF04 (JWT) / REQNF05 (RLS) → conforme decisão do projeto.

## Schema (DB)

Enums armazenados como VARCHAR + CHECK (`native_enum=False`), guardando o `.value`.

- **`users`** — `id, name, role UserRole(seller|admin), email UNIQUE, initials, active, created_at`.
- **`courses`** — `id, name UNIQUE, description, modality, price Numeric(10,2), duration, active`.
- **`cohorts`** — `id, course_id FK, name, start_date, end_date, capacity, price_per_slot Numeric, status CohortStatus(open|active|finished)`.
- **`leads`** — `id, name, email?, phone, source, assignee_id FK→users, external_user_id? UNIQUE, created_at, updated_at`. Índice único parcial em `email WHERE email IS NOT NULL`. **Sem campo de funil.**
- **`deals`** — `id, lead_id FK, cohort_id FK, stage DealStage(Novo|Contatado|Negociando), status DealStatus(open|won|lost), lost_reason?, created_at, updated_at`. `UNIQUE(lead_id, cohort_id)`; CHECK `status<>'lost' OR lost_reason IS NOT NULL`. **Sem `course_id`** (via `deal.cohort.course`).
- **`deal_events`** — `id, deal_id FK, from_stage?, to_stage?, from_status?, to_status?, reason?, user_id FK→users, ts`.

## Critérios de aceitação → casos de teste

| # | Critério | Teste |
|---|----------|-------|
| 1 | `GET /health` → 200 `{"status":"ok","db":"ok"}` | `tests/test_health.py::test_health_ok` |
| 2 | CRUD básico (user/course/cohort/lead); cohort default `open` | `tests/test_models.py::test_create_core_entities` |
| 3 | `deals` `UNIQUE(lead, cohort)` rejeita duplicado | `tests/test_models.py::test_deal_unique_lead_cohort` |
| 4 | 1 lead, 2 turmas (mesmo curso) → 2 deals em estágios diferentes; curso via `deal.cohort.course` | `tests/test_models.py::test_lead_multiple_deals` |
| 5 | `status=lost` sem `lost_reason` viola CHECK; com motivo OK | `tests/test_models.py::test_lost_requires_reason` |
| 6 | `deal_events` persiste e é consultável em ordem (histórico REQF02) | `tests/test_models.py::test_deal_events_history` |
| 7 | dedupe de email: dois não-nulos iguais falham; dois nulos OK | `tests/test_models.py::test_lead_email_dedupe` |
| 8 | fixture mock-Anthropic devolve instância Pydantic real, sem rede | `tests/test_anthropic_fixture.py::test_mock_anthropic_returns_pydantic` |

## Verificação

```
docker compose up -d
curl -f http://localhost:8000/health      # ⇒ {"status":"ok","db":"ok"}
docker compose exec backend pytest        # ⇒ verde
docker compose exec backend python scripts/seed.py   # idempotente (re-run sem duplicar)
```
CI verde em PR (lint + test + docker build + smoke).
