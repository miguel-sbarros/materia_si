# Spec — P1: Kanban funcional com DB (REQF01, REQF02)

> Plano-fonte: `~/.claude/plans/vast-squishing-firefly.md`.
> Princípios exercidos: **Arquitetura em camadas, TDD, Spec-Driven Development**.

## Requisito / contexto

Transforma o Funil mock (Ciclo 1) no **#1 feature real**: quadro Kanban persistido no
banco. Stack de fundação front↔back (API client + TanStack Query) é levantada aqui.

- **REQF01** (cadastrar leads): `POST /leads` cria lead (nome/email/telefone/origem) +
  deal inicial `Novo`/`open` na turma escolhida; dedupe de email quando informado (409).
- **REQF02** (gerenciar pipeline): a posição vive por **deal** (lead × cohort, curso via
  `deal.cohort.course`). `PATCH /deals/{id}` move/transiciona um deal; **cada mudança
  gera um registro em `deal_events`** (histórico).

**Auth diferida:** o seller seedado (Dra. Ana Costa) é o usuário corrente implícito;
novos deals/eventos são atribuídos a ele. Sem tela de Login nesta etapa.

## Escopo

**Entra:** endpoints `GET /courses`, `GET /deals` (feed do quadro, com filtros),
`POST /leads`, `GET /leads/{id}`, `PATCH /deals/{id}`; schemas Pydantic; services
`catalog/leads/deals`; fixture `api_client` (override de `get_db` com isolamento por
savepoint); fundação frontend (`@tanstack/react-query` + `QueryClientProvider` + seam
`src/lib/api.js`); wiring do `Funil.jsx` (quadro do DB, drag persiste, modal Perdido,
modal Novo Lead com curso→turma reais, filtro por curso).

**Não entra (diferido):** Login/auth (stand-in do seller seedado); filtro por turma na
UI (endpoint já aceita `cohort_id`); wiring de `GET /leads/{id}` na UI (endpoint + teste
só, serve a Conversas em P2); páginas Analytics/Conversas; `value`/`lastContact` são
best-effort (`price_per_slot` e `updated_at`; tempo de contato real chega em P2).

## Contrato de API (routers finos → services)

| Método e rota | Propósito | Retorno |
|---|---|---|
| `GET /courses` | Dados de referência para o filtro e o seletor de turma do "Novo Lead". | `list[CourseOut]` (cada um com `cohorts`). |
| `GET /deals?course_id=&cohort_id=` | **Feed do quadro.** Todos os deals como cards, mapeados em colunas. Filtros opcionais. | `list[DealCard]` |
| `POST /leads` | Cria lead + deal inicial `Novo`/`open` na `cohort_id` + `DealEvent` inicial. | `DealCard` (em Novo) — `201` |
| `GET /leads/{id}` | Detalhe do lead com seus deals. (Endpoint + teste só; não plugado no Funil nesta etapa.) | `LeadDetail` |
| `PATCH /deals/{id}` | Move/transiciona um deal para a coluna alvo; grava `DealEvent`. | `DealCard` atualizado |

## Schemas Pydantic (`app/schemas/`)

- `CohortOut`: `id, course_id, name, status, price_per_slot: Decimal|None`
- `CourseOut`: `id, name, price: Decimal|None, cohorts: list[CohortOut]`
- `DealCard`: `id` (id do deal — alvo do drag/PATCH), `leadId`, `name` (lead.name),
  `course` (deal.cohort.course.name), `cohortId`, `cohortName`, `source|None`,
  `column` ("Novo"|"Contatado"|"Negociando"|"Matriculado"|"Perdido"), `stage`,
  `status`, `value: Decimal|None` (= `cohort.price_per_slot ?? course.price`),
  `assignee: str|None` (iniciais), `updatedAt` (ISO).
- `DealBrief`: `id, course, cohortName, column, stage, status`
- `LeadCreate`: `name: str` (obrigatório), `email: str|None`, `phone: str|None`,
  `source: str|None`, `cohort_id: int` (obrigatório).
- `LeadDetail`: `id, name, email, phone, source, deals: list[DealBrief]`
- `DealMove`: `column: str` (uma das 5 colunas), `lost_reason: str|None`.

## Mapeamento Coluna ↔ (stage, status) — em `app/services/deals.py`

- **card → coluna** (`card_column`): `status==won → "Matriculado"`; `status==lost →
  "Perdido"`; senão `stage.value`.
- **move(column, lost_reason)** (`move_deal`):
  - `Novo|Contatado|Negociando` → `stage=column`, `status=open`, limpa `lost_reason`.
  - `Matriculado` → `status=won` (mantém stage), limpa `lost_reason`.
  - `Perdido` → `status=lost`; **exige `lost_reason`** (senão `422`); mantém stage.
  - coluna inválida → `422`.
  - Sempre grava `DealEvent(from_stage,to_stage,from_status,to_status,reason,
    user_id=lead.assignee_id, ts=now())`.

## Critérios de aceitação → casos de teste (TDD — escrever antes)

| # | Critério (REQ) | Teste |
|---|---|---|
| 1 | `GET /courses` retorna os 3 cursos seedados, cada um com suas turmas | `tests/test_catalog.py::test_list_courses` |
| 2 | `GET /deals` mapeia colunas: won→Matriculado, lost→Perdido, senão stage (REQF02) | `tests/test_deals.py::test_board_feed_maps_columns` |
| 3 | `GET /deals?course_id=` e `?cohort_id=` filtram o quadro | `tests/test_deals.py::test_board_filters` |
| 4 | `PATCH /deals/{id}` move de estágio atualiza stage e grava `DealEvent` (REQF02 histórico) | `tests/test_deals.py::test_move_stage_writes_event` |
| 5 | `PATCH` column=Perdido **sem** `lost_reason` → 422; **com** motivo → status=lost + lost_reason + evento | `tests/test_deals.py::test_move_to_perdido_requires_reason` |
| 6 | `PATCH` column=Matriculado → status=won, card column=Matriculado, evento de status | `tests/test_deals.py::test_move_to_matriculado_sets_won` |
| 7 | `POST /leads` cria lead + deal Novo/open + evento inicial; retorna DealCard em Novo (REQF01) | `tests/test_leads.py::test_create_lead_creates_deal` |
| 8 | `POST /leads` com email já existente → 409 (REQF01 dedupe) | `tests/test_leads.py::test_create_lead_duplicate_email_409` |
| 9 | `GET /leads/{id}` retorna o lead com seus deals | `tests/test_leads.py::test_get_lead_detail` |

## Verificação

```
docker compose up -d
docker compose exec backend pytest        # novos (1–9) + 8 existentes verdes
docker compose exec backend ruff check .  # limpo
cd src/frontend && npm run lint           # limpo
```
UI `http://localhost:5173/funil`: quadro carrega do DB; arrastar card persiste após
reload; arrastar p/ Perdido abre modal de motivo; "Novo Lead" (curso→turma) cria card
em Novo; filtro por curso estreita o quadro. **Check decisivo:** após mover um card
(incl. Perdido com motivo) e recarregar, o movimento persiste e há linha em
`deal_events` por transição.
```
