// Colunas do quadro (id = valor de `column` no DealCard). Todas são estágios abertos;
// Matriculado (won) / Perdido (lost) são transições terminais feitas pela close drop-zone.
export const COLUMNS = [
  { id: 'Novo', label: 'NOVO', dotColor: 'bg-blue-500' },
  { id: 'Contatado', label: 'CONTATADO', dotColor: 'bg-amber-500' },
  { id: 'Negociando', label: 'NEGOCIANDO', dotColor: 'bg-blue-600' },
  { id: 'Aprovado', label: 'APROVADO', dotColor: 'bg-green-500' },
]

export const SOURCE_COLORS = {
  Instagram: 'bg-blue-50 text-blue-700',
  'Site Direto': 'bg-purple-50 text-purple-700',
  WhatsApp: 'bg-emerald-50 text-emerald-700',
  Indicação: 'bg-indigo-50 text-indigo-700',
  'E-mail': 'bg-slate-100 text-slate-600',
}

export const SOURCES = ['Instagram', 'WhatsApp', 'Site Direto', 'Indicação', 'E-mail']

export const INPUT_CLASS =
  'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

// Estágios abertos do Funil — todas as colunas são abertas; o fechamento (won/lost)
// acontece arrastando o card para a close drop-zone.
export const OPEN_STAGES = COLUMNS

// Estado inicial dos campos de posicionamento no Funil (estágio começa em Novo).
export const EMPTY_PLACEMENT = { courseId: '', cohortId: '', stage: 'Novo' }

// Posicionamento válido para confirmar (turma escolhida; estágio sempre preenchido).
export const isPlacementValid = (p) => Boolean(p.cohortId)
