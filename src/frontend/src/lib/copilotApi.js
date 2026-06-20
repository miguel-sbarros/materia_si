// ─── Copiloto — seam de API (mock) ──────────────────────────────────────────
// Esta é a camada única de troca entre o protótipo e o backend real (P4). As
// funções abaixo simulam as rotas do PRD chamando os dados mock de data/copilot.js.
// Para plugar o backend de verdade, basta reescrever ESTE arquivo: trocar as
// chamadas locais por fetch() nas mesmas rotas, mantendo as assinaturas e os
// contratos (LeadSummary / Lead / Draft / Message) intactos.

import {
  COPILOT_LEADS,
  kbResponse,
  runCommand,
  craftDrafts,
} from '../data/copilot.js'

// ─── Contratos (PRD) ────────────────────────────────────────────────────────
/**
 * @typedef {Object} LeadSummary
 * @property {number} id
 * @property {string} name
 * @property {string} initials
 * @property {string} persona
 * @property {string} stage
 */

/**
 * @typedef {LeadSummary & {
 *   course: string,
 *   value: number|null,
 *   source: string,
 *   phone: string,
 *   lastContact: string,
 *   angle: string,
 *   history: {fromLead: boolean, text: string}[]
 * }} Lead
 */

/**
 * @typedef {Object} Draft
 * @property {'Consultivo'|'Objetivo'|'Caloroso'} tone
 * @property {string} text
 */

/**
 * @typedef {Object} Message
 * @property {number|string} [id]
 * @property {'user'|'assistant'} role
 * @property {'text'|'drafts'} kind
 * @property {string} [text]
 * @property {string} [reasoning]
 * @property {Draft[]} [variants]
 */

// Latência simulada — torna a UI assíncrona como será com o backend real.
const delay = (ms) => new Promise((r) => setTimeout(r, ms))

/**
 * Stand-in de `GET /api/leads?q={query}`.
 * Busca leads por nome (case-insensitive), retorna no máximo 6 como LeadSummary.
 * q vazio/whitespace retorna todos (até 6).
 * @param {string} q
 * @returns {Promise<LeadSummary[]>}
 */
export async function searchLeads(q) {
  await delay(60)
  const term = (q || '').trim().toLowerCase()
  return COPILOT_LEADS
    .filter((l) => !term || l.name.toLowerCase().includes(term))
    .slice(0, 6)
    .map(({ id, name, initials, persona, stage }) => ({
      id,
      name,
      initials,
      persona,
      stage,
    }))
}

/**
 * Stand-in de `GET /api/leads/{id}/context`.
 * Retorna o Lead completo (ou undefined se não encontrado).
 * @param {number} id
 * @returns {Promise<Lead|undefined>}
 */
export async function getLeadContext(id) {
  await delay(60)
  return COPILOT_LEADS.find((l) => l.id === id)
}

/**
 * Stand-in de `POST /api/copilot/chat`.
 * Retorna uma Message do assistente SEM id (o chamador atribui o id).
 * Precedência: command → leadId → texto do último user.
 * @param {{ messages?: Message[], leadId?: number, command?: string }} params
 * @returns {Promise<Message>}
 */
export async function postCopilotChat({ messages, leadId, command }) {
  await delay(900) // latência de geração simulada

  if (command) {
    return { role: 'assistant', kind: 'text', text: runCommand(command) }
  }

  if (leadId) {
    const lead = COPILOT_LEADS.find((l) => l.id === leadId)
    const d = craftDrafts(lead)
    return {
      role: 'assistant',
      kind: 'drafts',
      reasoning: d.reasoning,
      variants: d.variants,
    }
  }

  const lastUser = [...(messages || [])].reverse().find((m) => m.role === 'user')
  return { role: 'assistant', kind: 'text', text: kbResponse(lastUser?.text) }
}
