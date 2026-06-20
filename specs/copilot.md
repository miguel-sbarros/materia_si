# Spec — Copiloto de Vendas para WhatsApp

> Fonte do produto: `prototype/PRD Copiloto WhatsApp.dc.html` (Draft 1.0).
> Protótipo de UI: `prototype/Copiloto WhatsApp.dc.html`.
> Mapeia para a **Feature 4 (Copilot)** do `CLAUDE.md`.

## Propósito / contexto

Uma superfície conversacional que ajuda o **vendedor** a decidir a melhor
mensagem de WhatsApp para cada lead — combinando base de conhecimento (cursos,
personas, SPIN), o perfil + histórico do lead e a geração de mensagens prontas
para copiar. Vive na rota **`/copiloto`** dentro do `<Layout>` existente
(sidebar + topbar), seguindo o padrão das demais páginas em `src/pages`.

Esta etapa entrega o **port do frontend sobre mocks** (PRD Fase 1–2: UI shell +
drafts + base de conhecimento + slash commands). O backend LLM real — endpoints,
geração via Claude com prompt estruturado, streaming — é a **fase P4** do plano
mestre; aqui ele é substituído pela seam `src/frontend/src/lib/copilotApi.js`.

## Requisitos funcionais (PRD)

| ID | Requisito | Prior. |
|----|-----------|--------|
| F-01 | Estado vazio com saudação personalizada e campo de entrada centralizado (estilo Granola, paleta MR). | P0 |
| F-02 | Detecção de `@` no input abre seletor de leads filtrável por nome; Enter seleciona o primeiro. | P0 |
| F-03 | Chip de contexto do lead recolhível: cabeçalho sempre visível; expandido mostra atributos, ângulo recomendado e histórico (rolável). | P0 |
| F-04 | Resposta com lead anexado = Análise + 3 variantes (Consultivo / Objetivo / Caloroso), cada uma copiável. | P0 |
| F-05 | Botão Copiar usa a Clipboard API e dá feedback visual ("Copiado") por ~1,6s. | P0 |
| F-06 | Modo base de conhecimento (sem lead): responde cursos, personas, SPIN, risco e resumo semanal. | P1 |
| F-07 | Detecção de `/` abre menu de comandos filtrável; executar comando insere a resposta na conversa. | P1 |
| F-08 | "Nova conversa" limpa mensagens, lead anexado e retorna ao estado vazio. | P1 |
| F-09 | Indicador de "digitando" enquanto a resposta é gerada; auto-scroll para a última mensagem. | P1 |
| F-10 | Persistência da conversa por sessão (recarregar a página não perde o histórico ativo). | P2 |
| F-11 | Regenerar variantes / pedir mais tons a partir de uma resposta existente. | P2 |

## Contratos de dados (PRD)

```
Lead {
  id, name, initials, persona, stage,
  course, value, source, phone, lastContact,
  angle,        // ângulo recomendado (string)
  history: [{ fromLead: bool, text, at }]
}

Message {
  id, role: "user" | "assistant",
  kind: "text" | "drafts",
  text?, reasoning?, variants?: Draft[]
}

Draft {
  tone: "Consultivo" | "Objetivo" | "Caloroso",
  text
}
```

## Endpoints (a seam `lib/copilotApi.js` faz o stand-in)

| Método | Rota | Retorna |
|--------|------|---------|
| GET | `/api/leads?q={query}` | Leads resumidos (id, nome, persona, estágio) para o autocomplete do `@`. |
| GET | `/api/leads/{id}/context` | Perfil completo + histórico de mensagens do lead, carregado ao anexar. |
| POST | `/api/copilot/chat` | Corpo `{ messages[], leadId?, command? }` → uma `Message` (texto KB ou `drafts` com Análise + variantes). |

## Arquitetura frontend (como construída)

```
src/
├─ pages/
│  └─ Copiloto.jsx               // container: monta o composer e alterna vazio/conversa
├─ hooks/
│  └─ useCopilot.js              // useReducer: messages[], attachedLead, input, isTyping, menus
├─ components/copiloto/
│  ├─ EmptyState.jsx             // saudação + composer central
│  ├─ Composer.jsx               // textarea + detecção de @ e /
│  ├─ MentionMenu.jsx            // seletor de leads
│  ├─ CommandMenu.jsx            // menu de slash-commands
│  ├─ LeadContextChip.jsx        // chip recolhível do lead
│  ├─ MessageList.jsx            // thread + auto-scroll
│  └─ DraftCard.jsx              // variante + copiar
├─ data/
│  └─ copilot.js                 // mock: COPILOT_LEADS, COMMANDS, kbResponse, runCommand, craftDrafts
└─ lib/
   └─ copilotApi.js              // seam: searchLeads / getLeadContext / postCopilotChat
```

A detecção de `@` e `/` usa regex sobre o final do input (igual ao protótipo).
Estado local à página — sem store global. A troca para o backend real (P4) é
feita reescrevendo **só** `copilotApi.js`, mantendo as assinaturas e os contratos.

## Verificação

```
cd src/frontend && npm run lint && npm run build
```

Manual — abrir `/copiloto`:
- digitar `@` no campo → anexar um lead pelo seletor (F-02);
- digitar `/` → escolher um comando da lista (F-07);
- enviar com um lead anexado → ver Análise + 3 cards de sugestão (F-04);
- clicar **Copiar** em um card → feedback "Copiado" (F-05);
- clicar **Nova conversa** → volta ao estado vazio (F-08).
```
