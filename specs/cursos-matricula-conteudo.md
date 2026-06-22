# Spec — Aba Cursos funcional: Matrícula (REQF06) + Conteúdo de curso → RAG do Copiloto

**Status:** a implementar (TDD, spec-driven). Migrações aditivas `0008`/`0009` (chain off `0007_deal_stage_aprovado`).
**Origem:** falha de execução do Ciclo 2 — a aba Cursos nunca virou funcional (matrícula, vagas e conteúdo são mock/estáticos).

## Contexto e decisões travadas (interview 2026-06-22)

1. **Matrícula = tabela `enrollments` própria, integrada ao funil.** A matrícula é a **fonte da verdade** de quem está na turma. Matricular cria a `enrollment` **E** transiciona o `deal` vinculado para `won` (coluna "Matriculado"), criando o deal se não existir. Vagas = `capacity − matrículas ativas`; bloqueia turma cheia.
2. **Conteúdo do curso = ementa/módulos em tabela própria (`course_modules`), CRUD.** Migra o conteúdo hoje parseado de `playbook/cursos.md` para o banco. Upload de documentos/anexos fica **fora**.
3. **Reflexo no Copiloto = re-ingestão automática em background.** Salvar/editar/excluir módulo agenda um `BackgroundTask` que re-embeda os chunks daquele curso em `knowledge_chunks` (`source='course'`, idempotente). `rag.retrieve()` é source-agnóstico → o copiloto passa a saber **sem nenhuma mudança no copiloto**.
4. **Entrega full-stack** (backend + fiação do frontend da aba Cursos).

**Fora de escopo:** lista de espera/waitlist (REQF05 estendido), status de pagamento/frequência do aluno, upload de documentos, JWT/RLS.

## Critérios de aceitação

### REQF06 — Associar lead a turma e registrar matrícula
- `POST /cohorts/{cohort_id}/enrollments {lead_id, source?}` cria uma matrícula e:
  - transiciona (ou cria) o `deal(lead, cohort)` para `status=won` (coluna "Matriculado"), registrando um `DealEvent`;
  - vincula `enrollment.deal_id`.
- Duplicada `(lead, cohort)` → **409**; lead/cohort inexistente → **404**.
- **Turma lotada** (`matrículas ativas >= capacity`, quando `capacity` não-nulo) → **422** "Turma lotada".
- A matrícula impacta automaticamente a disponibilidade de vagas (REQF05 núcleo).
- `DELETE /cohorts/{cohort_id}/enrollments/{lead_id}` cancela a matrícula (`status='cancelled'`), **libera a vaga**, e reverte o deal para `open`/`Negociando` (registrando `DealEvent`).

### REQF04 (completar) — Gerenciar conteúdo do curso
- CRUD de módulos por curso: `GET/POST /courses/{id}/modules`, `PUT/DELETE /modules/{id}`.
- `GET /courses/{id}/ementa` passa a derivar `syllabus` **dos módulos do DB** (fallback ao parser de `cursos.md` apenas se o curso não tiver módulos — bootstrap).

### Reflexo no Copiloto (RAG)
- Criar/editar/excluir módulo agenda re-ingestão em background daquele curso: delete-then-insert dos chunks `source='course'` com `node_ref` prefixo `course:{course_id}#`, sem tocar `kb_graph`/`playbook`.
- Após re-ingestão, `rag.retrieve()` retorna os chunks do curso (verificável com `mock_embedder`).

### Frontend (aba Cursos funcional)
- Clicar numa turma abre um detalhe com: **barra de vagas** (`matriculados/capacity`), **lista de matriculados**, botão **Matricular** (busca lead existente → matricula), e **editor de ementa/módulos** (add/editar/excluir).
- Matricular reflete imediatamente: barra de vagas incrementa e o lead aparece como "Matriculado" no Funil (invalidar `['deals']`).

## Schema (migrações aditivas)

### `0008_enrollments`
```sql
CREATE TABLE enrollments (
    id         SERIAL PRIMARY KEY,
    lead_id    INTEGER NOT NULL REFERENCES leads(id),
    cohort_id  INTEGER NOT NULL REFERENCES cohorts(id),
    deal_id    INTEGER REFERENCES deals(id),           -- deal que materializa a matrícula
    status     VARCHAR NOT NULL DEFAULT 'active'
               CHECK (status IN ('active','cancelled')),
    source     VARCHAR(60),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_enrollments_lead_cohort UNIQUE (lead_id, cohort_id)
);
```
- Enum `EnrollmentStatus(StrEnum)` = `active|cancelled` em `app/core/constants.py`; coluna via `enum_column(EnrollmentStatus, "enrollment_status")`.

### `0009_course_modules`
```sql
CREATE TABLE course_modules (
    id         SERIAL PRIMARY KEY,
    course_id  INTEGER NOT NULL REFERENCES courses(id),
    title      VARCHAR(300) NOT NULL,
    content    TEXT,
    position   INTEGER NOT NULL DEFAULT 0,   -- ordem de exibição
    carga      VARCHAR(80),                  -- ex.: "3 dias - 24 horas"
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Relationships: `Lead.enrollments`, `Cohort.enrollments`, `Course.modules` (cascade delete-orphan nos módulos). Registrar `Enrollment` e `CourseModule` em `app/models/__init__.py`.

## Contrato da API

| Método | Rota | Entrada | Resposta |
|---|---|---|---|
| POST | `/cohorts/{cohort_id}/enrollments` | `{lead_id:int, source?:str}` | `201 EnrollmentOut` · 404/409/422 |
| GET | `/cohorts/{cohort_id}/enrollments` | — | `{capacity, enrolled, available, enrollments:[EnrollmentOut]}` |
| DELETE | `/cohorts/{cohort_id}/enrollments/{lead_id}` | — | `200` (cancela + libera vaga + reverte deal) |
| GET | `/courses/{course_id}/modules` | — | `[ModuleOut]` |
| POST | `/courses/{course_id}/modules` | `ModuleCreate` | `201 ModuleOut` (agenda reingest bg) |
| PUT | `/modules/{module_id}` | `ModuleUpdate` | `ModuleOut` (agenda reingest bg) |
| DELETE | `/modules/{module_id}` | — | `204` (agenda reingest bg) |

Schemas (`from_attributes=True`; `EnrollmentOut` camelCase no fio: `leadId/cohortId/dealId/enrolledAt/leadName`):
- `EnrollmentCreate{lead_id, source?}`, `EnrollmentOut{id, leadId, leadName, cohortId, dealId?, status, source?, enrolledAt}`, `CohortEnrollmentsOut{capacity?, enrolled, available?, enrollments:[EnrollmentOut]}`.
- `ModuleCreate{title, content?, position?, carga?}`, `ModuleUpdate{...todos opcionais}`, `ModuleOut{id, courseId, title, content?, position, carga?}`.

## Lógica de serviço (reuso máximo)

`app/services/enrollments.py`:
- `enroll_lead(db, cohort_id, lead_id, source=None) -> Enrollment`:
  1. cohort/lead existem? (senão `ValueError` → 404).
  2. `active_count >= capacity` (capacity não-nulo)? → `ValueError("Turma lotada")` → 422.
  3. cria `Enrollment(active)`; `IntegrityError` na UNIQUE → 409.
  4. deal `(lead, cohort)`: se existir e `open`, `move_deal(...MATRICULADO)`; se não existir, `create_closed_deal(status=WON)` (reusar `app/services/deals.py`). Setar `enrollment.deal_id`.
- `cancel_enrollment(db, cohort_id, lead_id)`: `status='cancelled'`; reverter deal vinculado para `open`/`Negociando` + `DealEvent`.
- `cohort_enrollments(db, cohort_id) -> CohortEnrollmentsOut`: conta só `active`; `available = capacity - active` (None se capacity None).

`app/services/course_modules.py`: CRUD de `CourseModule` (padrão `catalog.py`). Atualizar `app/api/routes/catalog.py::get_course_ementa` para montar `syllabus` dos módulos do DB (fallback ao `course_content.course_ementa` se sem módulos).

`app/services/course_rag.py` (reusa `ingest_knowledge._embed_and_persist` por padrão e `rag.embed_texts`):
- `reingest_course(db, course_id)`: `delete(KnowledgeChunk).where(source=='course', node_ref.like(f'course:{course_id}#%'))`; constrói 1 chunk por módulo (`source='course'`, `chunk_type='course_module'`, `node_ref=f'course:{course_id}#{module.id}'`, `title=module.title`, `content=f"{course.name} — {module.title}: {module.content}"`); embeda; insere.
- `reingest_course_bg(course_id)`: própria `SessionLocal`, engole exceções (template = `analysis.run_analysis_bg`).

Router de matrícula em `app/api/routes/enrollments.py` (incluir em `create_app()`); endpoints de módulo em `catalog.py`. Endpoints de módulo injetam `BackgroundTasks` e chamam `background_tasks.add_task(reingest_course_bg, course_id)`.

## Frontend (`src/frontend/src`)

- `lib/api.js`: `getCohortEnrollments(cohortId)`, `enrollLead(cohortId, leadId)`, `cancelEnrollment(cohortId, leadId)`, `getCourseModules(courseId)`, `createCourseModule/updateCourseModule/deleteCourseModule`.
- Componentes novos em `components/cursos/`: `CohortDetailModal.jsx` (barra de vagas + lista de matriculados + botões), `EnrollmentModal.jsx` (busca lead via `searchLeads` → `enrollLead`), `EmentaEditor.jsx` (CRUD de módulos).
- `pages/Cursos.jsx`: clicar numa turma abre `CohortDetailModal`. Mutations seguem o padrão TanStack (Funil.jsx): query keys `['cohortEnrollments', cohortId]` e `['courseModules', courseId]`; `onSuccess` invalida essas chaves **e** `['deals']` e `['courses']` quando aplicável.

## Casos de teste (escrever primeiro — TDD)

`tests/factories.py`: `make_enrollment(session, cohort, lead=None, status=active)`, `make_course_module(session, course, title=..., position=0)`.

`tests/test_enrollments.py`:
- `test_enroll_creates_enrollment_and_wins_deal` — cria enrollment + deal vira `won` (coluna Matriculado) + `DealEvent` gravado + `enrollment.deal_id` setado.
- `test_enroll_existing_open_deal_moves_to_won` — deal aberto pré-existente vai para won.
- `test_enroll_duplicate_409`, `test_enroll_unknown_lead_or_cohort_404`.
- `test_enroll_full_cohort_422` — `capacity=1`, 1 matrícula ativa → 2ª retorna 422.
- `test_cancel_enrollment_frees_slot_and_reopens_deal` — cancela → `available` volta a subir + deal `open/Negociando`.
- `test_cohort_enrollments_summary_counts_active_only`.

`tests/test_course_modules.py`:
- CRUD (criar/listar/editar/excluir); `GET /courses/{id}/ementa` deriva syllabus dos módulos do DB.
- `test_module_save_schedules_reingest` — espião monkeypatcha `reingest_course_bg` e confirma o agendamento.

`tests/test_course_rag.py` (usa `mock_embedder`):
- `test_reingest_course_idempotent_by_prefix` — re-rodar não duplica; só afeta `course:{id}#%`; `kb_graph`/`playbook` intactos.
- `test_retrieve_finds_course_chunk` — após reingest, `rag.retrieve` retorna o chunk do curso.

`scripts/seed.py`: criar `enrollments` (active) para os deals `won` já semeados e popular `course_modules` dos cursos semeados (a partir de `course_content.parse_cursos_md()`), para a demo ter vagas/conteúdo. Idempotente.

## Verificação (prova de que a etapa está pronta)

1. `docker compose exec backend pytest` — **tudo verde** (incluindo os novos testes).
2. `docker compose exec backend ruff check .` — limpo.
3. `cd src/frontend && npm run build && npm run lint` — limpos.
4. **E2E manual** (`docker compose up`): em Cursos, abrir uma turma → Matricular um lead → a **barra de vagas incrementa** e o lead aparece "Matriculado" no Funil; editar um módulo → numa sessão do Copiloto, perguntar sobre o conteúdo do curso → a resposta reflete o módulo editado.

A verificação que prova o passo: **(1)+(4)** — `pytest` verde + o fluxo matricular→vaga→Funil e editar-módulo→Copiloto-sabe funcionando em `docker compose up`.
