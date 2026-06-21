# Spec — P2: Import WhatsApp + Lead page (REQF03, Feature 2)

> Plano-fonte: `~/.claude/plans/purrfect-conjuring-grove.md`.
> Princípios exercidos: **Arquitetura em camadas, TDD, Spec-Driven Development**.

## Requisito / contexto

**REQF03** — importar conversas exportadas do WhatsApp (`.zip` / `_chat.txt`) como **v0**
da futura integração WhatsApp Business API; exibir o histórico por lead. Tabelas novas:
`conversations`, `messages`. Página de detalhes do lead (`/leadpage/:id`) acessível de
**3 pontos** (card do Funil, busca da Topbar, qualquer card de lead).

**Decisões desta etapa:**
- Único caminho de import: `.zip` / `_chat.txt` (carrega timestamps reais). `all_chats.json`
  **não** é usado.
- Fixture sintético/de-identificado **commitado** (`tests/fixtures/whatsapp/`) → demo do
  grader + testes rodam em clone limpo. Corpus real (`data/Chats_21-01-2026/`) é local-only.
- `POST /imports` é **síncrono** (valida, persiste, retorna resumo). Import em massa é o
  script re-executável `scripts/populate_chats.py`.
- Sem coluna `message_type`: mídia vira placeholder PT no `text` (`[áudio]`, `[imagem]`,
  `[documento]`, `[mídia]`). Whisper/FFmpeg/SQLite do `wpp2db.py` são descartados.

**Auth diferida:** mantém o seller seedado (Dra. Ana Costa) como usuário corrente implícito.

## Schema (migração `0002_conversations_messages`, `down_revision="0001_core_deal"`)

- `conversations(id, lead_id FK→leads, channel='WhatsApp', source?, external_user_id?,
  unread, last_message_at?, created_at)` — `UNIQUE(lead_id, channel)`; índice em
  `external_user_id`.
- `messages(id, conversation_id FK→conversations, text, sent bool, channel, sent_at?,
  sequence, read, created_at)` — **`UNIQUE(conversation_id, sequence)`** (torna o re-import
  idempotente). `sent=true` ⇔ vendedor.

## Parser (porte de `sales_context_system/export_msgs/wpp2db.py` — só parsing)

- Split por fronteira de timestamp (trata multi-linha):
  `re.finditer(r'\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\]', text)`.
- Parse por mensagem: `r'\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.+)'` com
  `re.DOTALL` → `(timestamp, sender, body)`.
- `~Sender` ⇒ **lead** (`sent=False`); sem `~` (ex.: `MR Digital`) ⇒ **vendedor**
  (`sent=True`).
- Filtra as 2 mensagens de sistema PT (aviso de criptografia E2E; "iniciada em um anúncio
  no Facebook") + corpos vazios.
- Limpa U+200E (`‎`) nas bordas; lê UTF-8.
- `external_user_id` (telefone) do nome do `.zip` `WhatsApp Chat - <phone>.zip`; nome do
  lead = `~`-sender mais frequente.
- Erros tipados: `EmptyChatError` (vazio), `NotWhatsAppExportError` (zero timestamps) → 422.

## Contrato de API (routers finos → services)

| Método e rota | Propósito | Retorno |
|---|---|---|
| `POST /imports` | Upload `.txt`/`.zip` (+ `lead_id` opcional). Cria/atualiza lead+conversa+mensagens. | `ImportSummary` |
| `POST /leads/{id}/messages` | Anexa 1 mensagem manual à conversa do lead. | `MessageOut` — `201` |
| `GET /leads/{id}/conversation` | Thread do lead. | `{conversationId, messages: [MessageOut]}` |
| `GET /conversations` | Feed do painel esquerdo de Conversas. | `list[ConversationSummary]` |
| `GET /leads/{id}` (estendido) | Detalhe do lead + `conversation` + campos de perfil (placeholder até P3). | `LeadDetail` |
| `GET /leads?q=` | Busca de leads por nome (ILIKE, cap ~8). | `list[LeadSummary]` |

## Schemas Pydantic (`app/schemas/conversation.py`, extensões em `lead.py`)

- `MessageOut`: `id, text, sent, sentAt: datetime|None, sequence, read`.
- `ConversationSummary`: `id, leadId, name, lastMessage: str|None, lastMessageAt: datetime|None, unread, channel`.
- `ImportSummary`: `leadId, conversationId, messagesImported: int, createdLead: bool`.
- `LeadSummary`: `id, name, initials, persona: str|None, stage: str|None`.
- `LeadDetail` (estende P1): + `conversation: list[MessageOut]`, + perfil placeholder
  (`persona, angle, leadScore, summary` = null/"—" até P3), + `attributes` derivados de leads/deals.

## Critérios de aceitação → casos de teste (TDD — escrever antes)

| # | Critério (REQ) | Teste |
|---|---|---|
| 1 | Conversation/Message persistem; ordenação por `sequence`; `UNIQUE(conv,seq)` rejeita dup | `tests/test_models_conversation.py` |
| 2 | parser separa por timestamp e trata multi-linha | `tests/test_whatsapp_parser.py::test_multiline` |
| 3 | `~Sender` → lead (sent=False); sem `~` → vendedor (sent=True) | `tests/test_whatsapp_parser.py::test_sender_role` |
| 4 | filtra mensagens de sistema e vazias | `tests/test_whatsapp_parser.py::test_system_filter` |
| 5 | mídia `<anexado:…>`/`<Mídia oculta>` → placeholder PT | `tests/test_whatsapp_parser.py::test_media_placeholder` |
| 6 | vazio → `EmptyChatError`; sem timestamp → `NotWhatsAppExportError` | `tests/test_whatsapp_parser.py::test_typed_errors` |
| 7 | `POST /imports` (.txt e .zip) cria lead+conversation+messages (REQF03) | `tests/test_imports.py::test_import_txt` / `::test_import_zip` |
| 8 | re-importar o mesmo arquivo é idempotente (sem linhas novas) | `tests/test_imports.py::test_import_idempotent` |
| 9 | `POST /imports` arquivo inválido → 422 com erro tipado | `tests/test_imports.py::test_import_bad_file_422` |
| 10 | `POST /leads/{id}/messages` anexa 1 mensagem | `tests/test_imports.py::test_manual_message` |
| 11 | `GET /leads/{id}/conversation` e `GET /conversations` devolvem thread/lista | `tests/test_imports.py::test_get_conversation` |
| 12 | `GET /leads/{id}` inclui `conversation` + campos de perfil (placeholder) | `tests/test_leads.py::test_lead_detail_has_conversation` |
| 13 | `GET /leads?q=` busca por nome (case-insensitive); vazio → `[]` | `tests/test_leads.py::test_search_leads` |

## Verificação (decisiva)

```
docker compose up -d
docker compose exec backend pytest        # casos 1–13 + 17 existentes verdes
docker compose exec backend ruff check .  # limpo
cd src/frontend && npm run build          # limpo
```
UI: upload de um `.zip` em Conversas → lead + thread aparecem (bolhas vendedor/lead, com
timestamps); **re-upload não duplica** (idempotente); clicar card no Funil abre
`/leadpage/:id` com header persona + grid de atributos + histórico WhatsApp (bolhas
verde `#DCF8C6` vendedor / branco lead); busca na Topbar navega para a página do lead.
```
