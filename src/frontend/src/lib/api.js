// ─── Captus — seam de API do Funil ──────────────────────────────────────────
// Camada única de troca front↔backend para o quadro Kanban. As funções mapeiam as
// rotas reais do backend (P1) mantendo contratos estáveis (DealCard / CourseOut /
// LeadCreate). Trocar a base de URL não exige mudar a página/componentes.

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ─── Contratos ────────────────────────────────────────────────────────────────
/**
 * @typedef {Object} DealCard
 * @property {number} id        id do deal — alvo do drag/PATCH
 * @property {number} leadId
 * @property {string} name
 * @property {string} course
 * @property {number} cohortId
 * @property {string} cohortName
 * @property {string|null} source
 * @property {'Novo'|'Contatado'|'Negociando'|'Matriculado'|'Perdido'} column
 * @property {string} stage
 * @property {string} status
 * @property {number|null} value
 * @property {string|null} assignee
 * @property {string|null} updatedAt
 */

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

// money chega como string (Decimal, lossless) → número para formatação na UI.
function normalizeCard(card) {
  return { ...card, value: card.value == null ? null : Number(card.value) }
}

/**
 * `GET /deals?course_id=&cohort_id=` — feed do quadro.
 * @param {{courseId?: number, cohortId?: number}} [filters]
 * @returns {Promise<DealCard[]>}
 */
export async function getDeals({ courseId, cohortId } = {}) {
  const params = new URLSearchParams()
  if (courseId) params.set('course_id', courseId)
  if (cohortId) params.set('cohort_id', cohortId)
  const qs = params.toString()
  const cards = await request(`/deals${qs ? `?${qs}` : ''}`)
  return cards.map(normalizeCard)
}

/** `GET /courses` — cursos e suas turmas (filtro + seletor de turma do Novo Lead). */
export async function getCourses() {
  return request('/courses')
}

/**
 * `GET /courses/{id}/ementa` — curso (linha do DB) + ementa parseada do `playbook/cursos.md`.
 * @param {number} courseId
 * @returns {Promise<{course:{id:number,name:string,description:string|null,modality:string|null,price:string|null,duration:string|null}, ementa:{name:string,summary:string,sections:{heading:string,body:string}[],syllabus:{tema:string,conteudo:string,carga?:string}[]}|null}>}
 */
export async function getCourseEmenta(courseId) {
  return request(`/courses/${courseId}/ementa`)
}

/**
 * `POST /courses` — cria um curso. Retorna o CourseOut criado.
 * @param {{name:string, description?:string, modality?:string, price?:number|string, duration?:string}} payload
 */
export async function createCourse(payload) {
  return request('/courses', { method: 'POST', body: JSON.stringify(payload) })
}

/** `PUT /courses/{id}` — edita campos do curso (parcial). Retorna o CourseOut. */
export async function updateCourse(courseId, payload) {
  return request(`/courses/${courseId}`, { method: 'PUT', body: JSON.stringify(payload) })
}

/**
 * `POST /courses/{id}/cohorts` — cria uma turma no curso. Retorna o CohortOut.
 * @param {{name:string, start_date?:string, end_date?:string, capacity?:number, price_per_slot?:number|string, status?:string}} payload
 */
export async function createCohort(courseId, payload) {
  return request(`/courses/${courseId}/cohorts`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** `PUT /cohorts/{id}` — edita campos da turma (parcial). Retorna o CohortOut. */
export async function updateCohort(cohortId, payload) {
  return request(`/cohorts/${cohortId}`, { method: 'PUT', body: JSON.stringify(payload) })
}

/**
 * `POST /leads` — cria lead + deal inicial; retorna o DealCard (em Novo).
 * @param {{name: string, email?: string, phone?: string, source?: string, cohort_id: number}} payload
 * @returns {Promise<DealCard>}
 */
export async function createLead(payload) {
  const card = await request('/leads', { method: 'POST', body: JSON.stringify(payload) })
  return normalizeCard(card)
}

/**
 * `PATCH /deals/{id}` — move/transiciona o deal para a coluna alvo.
 * @param {number} dealId
 * @param {{column: string, lostReason?: string}} move
 * @returns {Promise<DealCard>}
 */
export async function moveDeal(dealId, { column, lostReason } = {}) {
  const card = await request(`/deals/${dealId}`, {
    method: 'PATCH',
    body: JSON.stringify({ column, lost_reason: lostReason ?? null }),
  })
  return normalizeCard(card)
}

/** `GET /leads/{id}` — detalhe do lead com seus deals (usado por P2). */
export async function getLead(id) {
  return request(`/leads/${id}`)
}

/**
 * `PATCH /leads/{id}` — edita os dados de contato do lead (parcial). 409 se email duplicado.
 * Retorna o LeadDetail completo (mesmo shape de GET /leads/{id}).
 * @param {number} id
 * @param {{name?:string, email?:string, phone?:string, source?:string}} payload
 */
export async function updateLead(id, payload) {
  return request(`/leads/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

/**
 * `POST /leads/{id}/deals` — posiciona um lead existente no Funil (turma + estágio aberto).
 * Usado quando um import cria um novo lead. Retorna o DealCard recém-criado.
 * @param {number} leadId
 * @param {{cohortId: number, stage: 'Novo'|'Contatado'|'Negociando'}} body
 * @returns {Promise<DealCard>}
 */
export async function createDeal(leadId, { cohortId, stage } = {}) {
  const card = await request(`/leads/${leadId}/deals`, {
    method: 'POST',
    body: JSON.stringify({ cohort_id: cohortId, stage }),
  })
  return normalizeCard(card)
}

/**
 * `GET /leads/{id}` — detalhe estendido: deals + conversation + attributes + `profile`
 * (perfil de IA do P3: persona, dores, desejos, objeções, comentários, SPIN, score, métricas;
 * `null` enquanto a análise não rodou). Usado pela página do lead e pelo painel de Conversas.
 */
export async function getLeadDetail(id) {
  return request(`/leads/${id}`)
}

/**
 * `GET /leads?q=` — busca de leads por nome (Topbar). Vazio/branco → [] sem requisição.
 * @param {string} q
 * @returns {Promise<{id:number,name:string,initials:string,persona:string|null,stage:string|null}[]>}
 */
export async function searchLeads(q) {
  const term = (q || '').trim()
  if (!term) return []
  return request(`/leads?q=${encodeURIComponent(term)}`)
}

// ─── Conversas (P2, REQF03) ─────────────────────────────────────────────────
/**
 * @typedef {Object} ConversationSummary
 * @property {number} id
 * @property {number} leadId
 * @property {string} name
 * @property {string|null} lastMessage
 * @property {string|null} lastMessageAt
 * @property {boolean} unread
 * @property {string} channel
 */
/**
 * @typedef {Object} MessageOut
 * @property {number} id
 * @property {string} text
 * @property {boolean} sent
 * @property {string|null} sentAt
 * @property {number} sequence
 * @property {boolean} read
 */

/** `GET /conversations` — feed do painel esquerdo de Conversas. */
export async function getConversations() {
  return request('/conversations')
}

/** `GET /leads/{id}/conversation` — thread do lead `{conversationId, messages}`. */
export async function getLeadConversation(leadId) {
  return request(`/leads/${leadId}/conversation`)
}

/** `POST /leads/{id}/messages` — anexa 1 mensagem manual (vendedor). */
export async function sendMessage(leadId, text) {
  return request(`/leads/${leadId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

/**
 * `POST /imports` — upload de .zip/.txt do WhatsApp (multipart).
 * Usa fetch cru com FormData (sem Content-Type manual — o browser define o boundary).
 * Resolução do lead no backend: `leadId` > telefone no nome do .zip > `leadName` (cria novo).
 * @param {File} file
 * @param {{leadId?: number, leadName?: string}} [opts]
 * @returns {Promise<{leadId:number, conversationId:number, messagesImported:number, createdLead:boolean}>}
 */
export async function importChat(file, { leadId, leadName } = {}) {
  const form = new FormData()
  form.append('file', file)
  if (leadId != null) form.append('lead_id', String(leadId))
  if (leadName != null && String(leadName).trim()) form.append('lead_name', String(leadName).trim())
  const resp = await fetch(`${BASE}/imports`, { method: 'POST', body: form })
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
  return resp.json()
}

// ─── Analytics (Análises) ───────────────────────────────────────────────────────
/**
 * `GET /analytics?course_id=&cohort_id=` — métricas agregadas reais (KPIs, funil, SPIN,
 * personas, dores, receita, latência, abandono, atividade de mensagens). Filtros opcionais
 * por curso/turma escopam todas as métricas ao subconjunto correspondente.
 * @param {{courseId?: number, cohortId?: number}} [filters]
 */
export async function getAnalytics({ courseId, cohortId } = {}) {
  const params = new URLSearchParams()
  if (courseId) params.set('course_id', courseId)
  if (cohortId) params.set('cohort_id', cohortId)
  const qs = params.toString()
  return request(`/analytics${qs ? `?${qs}` : ''}`)
}

// Extrai HH:MM de um ISO timestamp (bolhas do chat). '' se ausente.
export function clockTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// Rótulo relativo a partir de um ISO timestamp (best-effort — tempo de contato real chega em P2).
export function relativeTime(iso) {
  if (!iso) return '—'
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 1) return 'agora'
  if (mins < 60) return `${mins}min atrás`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h atrás`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d atrás`
  return `${Math.floor(days / 7)}sem atrás`
}
