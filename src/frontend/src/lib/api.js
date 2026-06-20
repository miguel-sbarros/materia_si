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
