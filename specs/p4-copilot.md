# Spec — P4 Copiloto de Vendas (RAG + agente + sessões)

> Implementa a **Feature 4** do `CLAUDE.md` / fase **P4** do plano mestre.
> Plano de execução: `~/.claude/plans/elegant-floating-boot.md`.
> Substitui o backend mock de `specs/copilot.md` (que cobria só o front).

## Propósito

Transformar a página `/copiloto` (hoje mock) num **copiloto agêntico real**: aconselha o
**vendedor** sobre a melhor mensagem para um lead, fundamentado em RAG sobre a base de
conhecimento da MR (`legacy_neo4j_kb.json` + `playbook/*.md`), no `LeadProfile` e no
histórico de WhatsApp do lead. Conversas do copiloto são **persistidas em sessões**
(tabelas próprias, distintas das mensagens lead/vendedor) e listadas numa sidebar.

## Decisões travadas (entrevista 2026-06-20 + adendos)

- **Embeddings = OpenAI** `text-embedding-3-small` (1536-dim) — override do CLAUDE.md
  (sentence-transformers/384). `OPENAI_API_KEY` no ambiente. Geração continua Claude.
- **Copiloto = agente** com loop de tool-use (SDK Anthropic), terminando em saída
  estruturada `SellerAdvice` quando há lead anexado. Modelo **`claude-sonnet-4-6`**.
- **Conselho = 3 *paths* estratégicos dinâmicos** (`title`+`rationale`+`message`) +
  `reasoning` no topo. Sem rótulos fixos de tom.
- **Sessão por lead** (`lead_id` fixo na criação; nullable p/ chat sem lead).
- **Send** reaproveita `POST /leads/{id}/messages` (não envia por API externa).
- **Slash-commands disparam workflows reais** de agregação (ICP, Analytics).
- **`@lead`** injeta contexto do lead (perfil + histórico) no agente.

## Requisitos / critérios de aceite (REQF04 copiloto; REQF08 análise agregada)

| ID | Critério |
|----|----------|
| C-01 | `POST /copilot/sessions {leadId?}` cria sessão (lead fixo, nullable) → 201. |
| C-02 | `GET /copilot/sessions` lista sessões por `updated_at` desc com `lastSnippet`. |
| C-03 | `GET /copilot/sessions/{id}` devolve sessão + mensagens ordenadas; 404 se inexistente. |
| C-04 | `POST /copilot/sessions/{id}/chat {text}` com lead anexado → mensagem `assistant` `kind="advice"` com `reasoning` + exatamente 3 `paths`; o agente chama ≥1 ferramenta no caminho. |
| C-05 | Mesmo endpoint **sem** lead → resposta `kind="text"` (modo base de conhecimento). |
| C-06 | `chat {command:"/icp"}` → agrega personas/conversão/dores/desejos reais e narra (`kind="text"`). |
| C-07 | `chat {command:"/analytics"}` → agrega taxas de conversão + latência reais e narra. |
| C-08 | Mensagens do copiloto vivem em `copilot_messages` — **linha distinta** de `messages` (lead/vendedor). |
| C-09 | Botão **Send** num path grava a mensagem no histórico WhatsApp do lead via `POST /leads/{id}/messages` (`sent=True`); não chama API externa. |
| C-10 | Ingestão `scripts/ingest_knowledge.py` é **idempotente** (re-rodar não duplica). |
| C-11 | `rag.retrieve` ordena por similaridade de cosseno; chunks `Script` que batem persona+SPIN sobem. |

## Schema (DB) — migrações encadeadas em `0003_lead_profiles`

**`0004_knowledge_chunks`** — `KnowledgeChunk`:
`id, source('kb_graph'|'playbook'), chunk_type, node_ref, label, title, content TEXT,
persona String(60)?, spin_stage String(40)?, meta JSONB, embedding Vector(1536),
tsv tsvector?, created_at`. `UNIQUE(source, node_ref)`. `tsv` não populado (BM25 diferido).

**`0005_copilot_sessions`** (down_revision `0004_knowledge_chunks`):
- `CopilotSession(id, lead_id FK→leads NULLABLE, title, created_at, updated_at[onupdate])`.
- `CopilotMessage(id, session_id FK, role['user'|'assistant'], kind['text'|'advice'],
  content TEXT?, advice JSONB?, sequence, created_at)`, `UNIQUE(session_id, sequence)`.

## Schemas Pydantic (`app/schemas/copilot.py`, wire camelCase)

```
AdvicePath  = { title: str, rationale: str, message: str }
SellerAdvice = { reasoning: str, paths: list[AdvicePath] }   # exatamente 3 (validado em Python)
SessionOut  = { id, leadId, title, updatedAt, lastSnippet }
MessageOut  = { id, role, kind, content?, advice? }
ChatIn      = { text: str, command?: str }
```

`SellerAdvice` é a saída terminal do loop do agente (`output_config.format` + `tools`);
o bloco `text` final do turno `end_turn` é JSON validado por `model_validate_json`.

## Ferramentas do agente (`app/services/copilot.py::_build_tools`)

| Ferramenta | Fonte |
|-----------|-------|
| `search_knowledge(query, persona?, spin_stage?)` | pgvector sobre `knowledge_chunks` (`rag.retrieve`) |
| `get_cohorts_status(course_name?)` | tabela `cohorts`/`courses` (status/capacidade/datas/preço) |
| `get_course_ementa(course_name)` | `courses` + `playbook/cursos.md`/KB Curso·Modulo |
| `get_icp_stats()` | `analytics.icp_summary` (personas, conversão, dores, desejos) |
| `get_funnel_analytics()` | `analytics.funnel_analytics` (conversão, latência, abandono) |

Toda ferramenta sempre devolve `tool_result` (erro → `is_error:true`) para o loop terminar.
`run_agent` tem `max_iterations` de guarda.

## Casos de teste (TDD)

- `tests/test_rag.py` (`mock_embedder`): ordenação por cosseno; boost Script persona+SPIN;
  filtro `None`; `UNIQUE(source,node_ref)`. + `@integration test_live_embedding` (1536-dim).
- `tests/test_ingest_knowledge.py` (`mock_embedder`): mapeia enums Script; funde justificativa
  de relacionamento; split playbook em `##`; idempotência.
- `tests/test_analytics.py` (sem LLM): conversão por persona (`icp_summary`); taxas + latência
  (`funnel_analytics`).
- `tests/test_llm_client.py`: `run_agent` loop de tool (tool_use → estruturado) e modo texto.
- `tests/test_copilot.py` (`mock_anthropic`+`mock_embedder`): criar sessão c/ lead; listar por
  recência; agente chama ferramenta → conselho 3-paths (`kind=advice`); modo KB texto; comando
  `/icp` chama `get_icp_stats`; comando `/spin` roteia `search_knowledge`; label→enum de persona;
  404. + `@integration test_live_copilot_advice` (Sonnet real; sem timeout de gramática; loop termina).
- `tests/test_copilot_tools.py` (sem LLM): `get_cohorts_status`, `get_course_ementa`.
- `tests/test_copilot_send.py`: mensagem sugerida via `POST /leads/{id}/messages` cai em
  `messages` e é linha distinta de `copilot_messages`.

## Verificação

```
docker compose exec backend alembic upgrade head      # 0004 + 0005
docker compose exec backend python scripts/ingest_knowledge.py   # idempotente
docker compose exec backend pytest                     # mocked
docker compose exec backend pytest -m integration      # Sonnet + OpenAI ao vivo
docker compose exec backend ruff check .
cd src/frontend && npm run build && npm run lint
```

Manual `/copiloto`: `@`-anexar lead → nova sessão na sidebar + conselho 3-paths (agente usa
ferramenta); **Send** num path → mensagem aparece no histórico do lead; `/icp` e `/analytics`
devolvem números reais; recarregar mantém a sessão.
