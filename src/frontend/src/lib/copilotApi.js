// ─── Copiloto — seam de API (P4, backend real) ──────────────────────────────
// Camada única de troca front↔backend do Copiloto. Espelha lib/api.js (mesma BASE
// e padrão de fetch) e expõe as rotas de sessão do copiloto:
//   POST /copilot/sessions            → cria sessão (lead fixo opcional)
//   GET  /copilot/sessions            → lista (mais recentes primeiro)
//   GET  /copilot/sessions/{id}       → sessão + mensagens
//   POST /copilot/sessions/{id}/chat  → 1 mensagem assistant (advice|text)
// O contexto de lead (@) e o histórico reusam os helpers de lib/api.js
// (searchLeads / getLeadDetail / sendMessage). A normalização das mensagens do
// assistente para o shape de UI vive aqui (advice → drafts, text → text).

import { searchLeads as apiSearchLeads, getLeadDetail } from './api.js'
import { personaMeta } from '../data/copilot.js'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let detail
    try {
      detail = (await resp.json()).detail
    } catch {
      /* resposta sem corpo JSON */
    }
    const err = new Error(detail || `HTTP ${resp.status}`)
    err.status = resp.status
    throw err
  }
  if (resp.status === 204) return null
  return resp.json()
}

// ─── Contratos (wire) ────────────────────────────────────────────────────────
/**
 * @typedef {Object} SessionOut
 * @property {number} id
 * @property {number|null} leadId
 * @property {string} title
 * @property {string|null} updatedAt
 * @property {string|null} lastSnippet
 */
/**
 * @typedef {Object} MessageOut       backend: kind 'text'|'advice'
 * @property {number} id
 * @property {'user'|'assistant'} role
 * @property {'text'|'advice'} kind
 * @property {string|null} [content]
 * @property {{reasoning: string, paths: {title, rationale, message}[]}|null} [advice]
 */
/**
 * @typedef {Object} UIMessage        shape consumido pelos componentes
 * @property {number|string} id
 * @property {'user'|'assistant'} role
 * @property {'text'|'drafts'} kind   advice→'drafts'; texto→'text'
 * @property {string} [text]
 * @property {string} [reasoning]
 * @property {{title: string, rationale: string, message: string}[]} [paths]
 */

// Normaliza um MessageOut do backend para o shape que MessageList/DraftCard renderizam.
// advice → { kind:'drafts', reasoning, paths }; text → { kind:'text', text }.
export function normalizeMessage(m) {
  if (m.kind === 'advice' && m.advice) {
    return {
      id: m.id,
      role: m.role,
      kind: 'drafts',
      reasoning: m.advice.reasoning || '',
      paths: m.advice.paths || [],
    }
  }
  return {
    id: m.id,
    role: m.role,
    kind: 'text',
    text: m.content || '',
  }
}

/** `POST /copilot/sessions` — cria sessão (lead fixo opcional). */
export async function createSession(leadId) {
  return request('/copilot/sessions', {
    method: 'POST',
    body: JSON.stringify({ leadId: leadId ?? null }),
  })
}

/**
 * `PATCH /copilot/sessions/{id}` — anexa um lead à sessão atual (sem novo thread).
 * Defensivo: se o backend recusar com 409 (sessão já tem lead), cai para criar
 * uma nova sessão com o lead — na prática o modal de confirmação evita esse caminho.
 * @param {number} sessionId
 * @param {number} leadId
 * @returns {Promise<SessionOut>}
 */
export async function attachLead(sessionId, leadId) {
  try {
    return await request(`/copilot/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ leadId }),
    })
  } catch (err) {
    if (err.status === 409) return createSession(leadId)
    throw err
  }
}

/** `GET /copilot/sessions` — lista de sessões (mais recentes primeiro). */
export async function listSessions() {
  return request('/copilot/sessions')
}

/** `GET /copilot/sessions/{id}` — sessão + mensagens (já normalizadas para a UI). */
export async function getSession(id) {
  const data = await request(`/copilot/sessions/${id}`)
  return { session: data.session, messages: (data.messages || []).map(normalizeMessage) }
}

/**
 * `POST /copilot/sessions/{id}/chat` — envia texto/comando, devolve a resposta
 * do assistente já normalizada (drafts|text).
 * @param {number} sessionId
 * @param {{text?: string, command?: string}} body
 * @returns {Promise<UIMessage>}
 */
export async function postChat(sessionId, { text, command } = {}) {
  const m = await request(`/copilot/sessions/${sessionId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ text: text ?? '', command: command ?? null }),
  })
  return normalizeMessage(m)
}

// ─── Contexto do lead (@) ─────────────────────────────────────────────────────
/**
 * `GET /leads?q=` — busca leads para o menu @ (delegado a lib/api.js).
 * @param {string} q
 * @returns {Promise<{id:number,name:string,initials:string,persona:string|null,stage:string|null}[]>}
 */
export async function searchLeads(q) {
  return apiSearchLeads(q)
}

// Iniciais a partir do nome (fallback quando o detalhe não traz `initials`).
function initialsOf(name) {
  const parts = (name || '').replace(/^Dr[a]?\.\s*/i, '').trim().split(/\s+/)
  return parts.slice(0, 2).map((p) => p[0] || '').join('').toUpperCase()
}

/**
 * `GET /leads/{id}` — detalhe do lead, normalizado para o LeadContextChip
 * (persona/angle/history/atributos). Mapeia o profile de IA (P3) + a conversation.
 * @param {number} id
 * @returns {Promise<Object>} lead pronto para o chip
 */
export async function getLeadContext(id) {
  const d = await getLeadDetail(id)
  const profile = d.profile || null
  const persona = profile?.persona || null
  // Deal em aberto (preferência) ou o primeiro, para curso/estágio.
  const deal = (d.deals || []).find((x) => x.status === 'open') || (d.deals || [])[0] || null
  // angle = resumo da IA quando houver; senão a justificativa de persona.
  const angle = profile?.summary || profile?.personaReasoning || ''
  // history: conversation (sent=True → vendedor) → { fromLead, text }.
  const history = (d.conversation || []).map((msg) => ({
    fromLead: !msg.sent,
    text: msg.text,
  }))
  return {
    id: d.id,
    name: d.name,
    initials: initialsOf(d.name),
    persona,
    stage: deal?.column || deal?.stage || '—',
    course: deal?.course || '—',
    value: null,
    source: d.source || '—',
    lastContact: '—',
    phone: d.phone || '—',
    angle,
    history,
    profile,
    meta: personaMeta(persona),
  }
}
