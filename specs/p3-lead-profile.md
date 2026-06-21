# Spec — P3: Análise de conversa → LeadProfile (REQF08, Feature 3)

> Plano-fonte: `~/.claude/plans/purrfect-conjuring-grove.md` (estendido na conversa).
> Princípios exercidos: **Arquitetura em camadas · TDD · Spec-Driven · Dockerização · CI ·
> uso de subagentes** (cada tarefa abaixo é delegada a um subagente dedicado).

## Requisito / contexto

**REQF08 / Feature 3** — analisar a conversa importada (P2) e produzir um **`LeadProfile`**
estruturado por lead: extração de entidades + classificação de **persona** + estágio
**SPIN** do diálogo + **métricas da conversa** (latência de resposta, ponto de abandono).
É a camada **individual** de análise; a página **Analytics** é uma camada **agregada de mais
alto nível, construída SOBRE estas análises individuais** — não é a mesma coisa e fica fora
deste passo.

### Decisões locked (entrevista 2026-06-20)

1. **Escopo "core"**: extração → `lead_profiles` + métricas de conversa + nó de extração no
   populate + endpoint sob demanda + grafting do perfil nos shells existentes (LeadPage +
   painel direito de Conversas). **Diferidos**: `lead_course_fit` (insumo de P5) e os widgets
   da Analytics (camada agregada, fase futura).
2. **Métricas de conversa = deterministas + enriquecimento SPIN**: latência e ponto de
   abandono são calculados por **timestamps** (Python, sem LLM); o LLM apenas **rotula o
   estágio SPIN no ponto de abandono** ("onde/por que esfriou").
3. **Gatilhos da análise**: **(a) auto no import, assíncrono, se total de mensagens > 3**
   (`BackgroundTasks`; resposta do import retorna na hora; ≤3 msgs → não dispara);
   **(b) sob demanda** `POST /leads/{id}/analyze`; **(c) lote** via nó no
   `scripts/populate_chats.py` (flag `--analyze`, pula existentes).
4. **Update-aware**: a análise **carrega o `lead_profiles` atual** (se houver) e o passa ao
   LLM junto da conversa; o modelo **decide o que mudar** (não sobrescreve cegamente). Upsert
   na mesma linha (1:1 com o lead).

## Schema — `lead_profiles` (1:1 com `leads`); migração `0003_lead_profiles` (`down_revision="0002_conversations_messages"`)

Tabela única que guarda **o artefato de análise** (entidades do lead + persona + SPIN +
score/summary + métricas da conversa). Recalculável a cada re-análise.

- `id` PK; `lead_id` FK→leads **UNIQUE** (1:1); `created_at`, `updated_at`.
- **Entidades (porte de Octo `ExtractedEntities`)**: `especialidade str?`, `experiencia str?`,
  `cidade_estado str?`, `course_interest str?`, `dores_verbalizadas jsonb`,
  `desejos_expressos jsonb`, **`objecoes jsonb`** (NOVO — objeções de venda, distinto de dores),
  `hardware_software jsonb`, `termos_tecnicos jsonb`, `context_markers jsonb`. *(listas como
  `JSONB`/`ARRAY(Text)` — escolher um e ser consistente; JSONB é mais simples para listas.)*
- **Persona (porte de `PersonaAssessment`)**: `matched_persona str` (rótulo de exibição PT —
  ver mapeamento), `persona_confidence float`, `persona_reasoning text`.
- **Diálogo**: `current_spin_stage str?` (SPINStage), `lead_score int?`, `summary text?`.
- **Métricas da conversa (deterministas + SPIN)**: `median_seller_latency_seconds int?`,
  `median_lead_latency_seconds int?`, `first_response_latency_seconds int?`,
  `last_message_sent bool?` (última msg foi do vendedor?), `is_abandoned bool` (lead esfriou —
  última msg do vendedor sem resposta há > limiar, ou heurística simples), `abandon_spin_stage
  str?` (estágio SPIN no abandono — vindo do LLM).
- **Metadados**: `model_used str?`, `raw jsonb` (saída bruta do LLM, auditoria).

Registrar o modelo em `app/models/__init__.py`; adicionar `Lead.profile` (1:1,
`uselist=False`, cascade delete).

## Schemas Pydantic (`app/schemas/analysis.py`)

Portar de `sales_context_system/app/models/graph_schemas.py` **sem** `pydantic_ai`/LangGraph:
- `SPINStage` (Enum: situation/problem/implication/need_payoff).
- `PersonaType` (Enum: iniciado_digital / especialista_analogico / recem_especializado /
  protesista / indeterminado).
- `ExtractedEntities` (campos acima, **+ `objecoes`**; tirar `extraction_timestamp` default).
- `PersonaAssessment` (matched_persona, persona_confidence, persona_reasoning).
- **`LeadAnalysis`** (schema de **saída única** do LLM = `output_format`): compõe
  `ExtractedEntities` + `PersonaAssessment` + `current_spin_stage` + `lead_score` +
  `summary` + `abandon_spin_stage`. Uma **só** chamada `messages.parse` por análise.
- `ChatMetrics` (resultado puro do cálculo determinista — não vai ao LLM).

**Mapeamento PersonaType → rótulo de exibição** (casar com as chaves de `personaMeta` no
front): iniciado_digital→"Iniciado Digital", especialista_analogico→"Especialista Analógico",
recem_especializado→"Recém-Especializado", protesista→"Focado em Prótese",
indeterminado→`None`.

## Prompt da análise (`app/prompts/`)

> **Referências de criação do prompt (instrução do usuário):**
> - `src/backend/app/prompts/copilot.py::SYSTEM_PROMPT` — o **prompt monolítico "OCTO"**: 5
>   etapas — **Etapa 1 DECODIFICADOR** (extração de entidades: especialidade, experiência,
>   dores, desejos, context markers, hardware/software, termos técnicos — mapeia 1:1 em
>   `ExtractedEntities`), **Etapa 2 Contextual**, **Etapa 3 Estratégico-Tático** (mapeamento
>   SPIN S/P/I/N + as 4 personas), **Etapa 4 Redação** (escrita de mensagem WhatsApp),
>   **Etapa 5 Guardrails** + um *Template de Output* (Decodificação / Posição SPIN /
>   Estratégia+persona / Insights / Mensagem sugerida). **Para P3 reusar Etapas 1 + 3 + 5**
>   (extração → persona/SPIN → guardrails) e o template (Decodificação/SPIN/Estratégia/Insights
>   → campos de `LeadAnalysis`); **DROPAR a Etapa 4 (redação de mensagem) — ela é o copiloto P4**,
>   não a análise. O prompt de análise produz **estrutura** (`output_format=LeadAnalysis`), não a
>   mensagem. (Obs.: o literal abre com `""""` — 1ª char do conteúdo é `"`.)
> - `playbook/*.md` — fundamentação: `personas.md` + os 4 dossiês (`001_..004_*.md`),
>   `about_mr.md`, `cursos.md`, `argumentos_valor.md`, `filosofia.md`. Para o prompt de
>   **classificação de persona**, embutir uma **referência compacta** das 4 personas (extraída
>   de `personas.md` — indicadores-chave por persona), **não** os dossiês inteiros (esses
>   alimentam o RAG do P4).
> - `sales_context_system/app/agents/prompts.py::get_spin_prompt("entity_extraction")` — prompt
>   de extração + ~8 few-shots PT já validados. Reusar como base do schema de extração.

O prompt instrui o modelo a, sobre o transcrito da conversa: extrair entidades (incl.
**objeções, desejos, dores, informações úteis**), classificar **persona** (1 das 4, com
confiança + razão, fundamentado na referência compacta), inferir o **estágio SPIN** do
diálogo e o **estágio SPIN no ponto de abandono**, e produzir `lead_score` + `summary`.
**Update-aware**: receber o `lead_profiles` atual (se houver) como contexto e revisá-lo.
Modelo **`claude-haiku-4-5`** (config `model_extraction`).

## Contrato LLM (`app/services/llm/client.py`)

`messages.parse(model=..., output_format=LeadAnalysis, ...)` retorna `ParsedMessage` no SDK
real; o **mock** dos testes retorna o Pydantic puro. Adicionar normalizador:
`out = getattr(resp, "parsed_output", None); model = out if out is not None else resp` (mock →
`out=None` → usa `resp`; real → `out=LeadAnalysis`). Validar `isinstance(model, output_format)`
e levantar erro tipado caso contrário. Testes **mockam** o cliente; live atrás de
`@pytest.mark.integration`.

## Pipeline de análise (`app/services/analysis.py`)

`analyze_lead(db, lead_id) -> LeadProfile`:
1. Carrega a conversa (mensagens ordenadas) + o `lead_profiles` atual (se houver).
2. **Métricas deterministas** (`compute_chat_metrics(messages) -> ChatMetrics`, função pura):
   latência mediana vendedor/lead (diferença de `sent_at` entre turnos alternados), latência
   da 1ª resposta, última msg foi do vendedor?, `is_abandoned` (heurística: última msg do
   vendedor e lead não respondeu — `last_message_sent and not lead_replied_after`).
3. **Chamada LLM** única → `LeadAnalysis` (entidades+persona+SPIN+score+summary+abandon_stage),
   passando o transcrito + perfil atual.
4. **Upsert** em `lead_profiles` (atualiza no lugar; seta `model_used`, `raw`, `updated_at`,
   mescla métricas deterministas + `abandon_spin_stage` do LLM).

## Gatilhos / endpoints

- `POST /leads/{id}/analyze` (router `leads.py` → service) — síncrono; retorna `LeadProfileOut`.
- **Auto no import** (`app/api/routes/imports.py` + `POST /leads/{id}/messages`): após persistir,
  **se total de mensagens da conversa > 3**, `background_tasks.add_task(analyze_lead_bg, lead_id)`.
  `analyze_lead_bg` abre sua **própria** `SessionLocal` (não a request). Falha de LLM é logada,
  não quebra o import.
- **Lote**: `scripts/populate_chats.py --analyze` — após importar cada conversa, se >3 msgs e
  (sem perfil ou `--reanalyze`), roda `analyze_lead` (síncrono no script).

## Exibição (grafting nos shells de P2)

- **Estender `GET /leads/{id}`** (`LeadDetail`): quando houver `lead_profiles`, preencher
  `persona` (rótulo), `angle` (derivado de desejos/objeções ou summary), `leadScore`, `summary`,
  e **novos campos** `dores: list[str]`, `desejos: list[str]`, `objecoes: list[str]`,
  `especialidade/experiencia/cidade`, e `chatMetrics` (latências + abandono + SPIN). Sem perfil →
  placeholders atuais (P2).
- **LeadPage** (`pages/LeadPage.jsx`): header de persona usa a persona real (tint via
  `personaMeta`); grade de atributos ganha especialidade/experiência/cidade; novas seções
  **Dores / Desejos / Objeções** (chips) + **Métricas da conversa** (latência, "esfriou em:
  <estágio SPIN>"); "Ângulo recomendado" real.
- **Conversas** (painel direito): substituir o placeholder "(P3)" por persona + dores + desejos
  + lead_score + summary.

## Critérios de aceitação → casos de teste (TDD — escrever antes)

| # | Critério (REQ) | Teste |
|---|---|---|
| 1 | `lead_profiles` persiste, 1:1 com lead (UNIQUE lead_id), cascade | `tests/test_models_profile.py` |
| 2 | `compute_chat_metrics` calcula latência mediana + abandono a partir de timestamps | `tests/test_chat_metrics.py` (função pura) |
| 3 | `analyze_lead` (mock LLM) cria perfil com entidades/persona/SPIN/score/objeções | `tests/test_analysis.py::test_analyze_creates_profile` |
| 4 | re-análise é **update-aware**: 2ª rodada atualiza a MESMA linha (sem duplicar) | `tests/test_analysis.py::test_reanalyze_updates_in_place` |
| 5 | `PersonaType` → rótulo de exibição correto | `tests/test_analysis.py::test_persona_label_map` |
| 6 | `POST /leads/{id}/analyze` → 200 + perfil | `tests/test_analysis.py::test_analyze_endpoint` |
| 7 | import com >3 msgs agenda análise; ≤3 não agenda (gate) | `tests/test_analysis_trigger.py` |
| 8 | `GET /leads/{id}` inclui perfil real quando existe; placeholders quando não | `tests/test_leads.py::test_lead_detail_profile` |
| 9 | (live) extração real devolve `LeadAnalysis` válido | `tests/test_analysis.py::test_live_extraction` `@pytest.mark.integration` |

## Verificação (decisiva)

```
docker compose up -d
docker compose exec backend pytest        # casos 1–8 + suíte existente verdes (mockados)
docker compose exec backend pytest -m integration   # caso 9 (precisa ANTHROPIC_API_KEY)
docker compose exec backend ruff check .  # limpo
cd src/frontend && npm run build          # limpo
```
UI: importar uma conversa com >3 msgs → após segundos, abrir `/leadpage/:id` → persona,
dores/desejos/objeções, score, summary e métricas (latência + ponto de abandono com estágio
SPIN) preenchidos; painel direito de Conversas idem. `POST /leads/{id}/analyze` reprocessa e
**atualiza** o mesmo perfil.

## Execução — delegar a subagentes (1 por escopo, TDD red→green)

- **Subagente A — Schema + Pydantic + migração.** Modelo `LeadProfile` + migração
  `0003_lead_profiles`; portar `SPINStage/PersonaType/ExtractedEntities(+objecoes)/
  PersonaAssessment/LeadAnalysis/ChatMetrics` para `app/schemas/analysis.py`; registrar modelo;
  `Lead.profile`. Testes: caso 1. *(fundação)*
- **Subagente B — Motor de análise.** `compute_chat_metrics` (puro) + prompt em `app/prompts/`
  (de Octo few-shots + referência compacta de personas do `playbook/`; grafta `copilot.py` se
  preenchido) + normalizador `parsed_output` em `client.py` + `analyze_lead` (update-aware,
  mock nos testes). Testes: casos 2–5. *(depende de A)*
- **Subagente C — Gatilhos + endpoints + populate.** `POST /leads/{id}/analyze`; auto-no-import
  assíncrono (gate >3, `SessionLocal` próprio); nó `--analyze` no populate. Testes: casos 6–7.
  *(depende de B)*
- **Subagente D — Exibição.** Estender `GET /leads/{id}` + `LeadDetail`; grafting no LeadPage e
  no painel direito de Conversas. Testes: caso 8. *(depende de B/C)*

Ordem: A → B → C → D (sequencial; tocam arquivos compartilhados — `leads.py`, `lead.py` schema,
`lib/api.js`). Cada subagente: testes primeiro, depois implementação, `ruff` limpo.
