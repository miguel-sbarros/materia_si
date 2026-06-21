// Helpers de exibição do perfil de IA (P3) — compartilhados por LeadPage e Conversas.

// Estágio SPIN (valor do backend) → rótulo PT.
export const SPIN_LABELS = {
  situation: 'Situação',
  problem: 'Problema',
  implication: 'Implicação',
  need_payoff: 'Necessidade',
}

export const spinLabel = (stage) => SPIN_LABELS[stage] || '—'

// Segundos → duração curta legível (ex.: 45s, 2min, 1h20). null → '—'.
export function fmtDuration(seconds) {
  if (seconds == null) return '—'
  const s = Math.round(seconds)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}min`
  const h = Math.floor(m / 60)
  const rem = m % 60
  return rem ? `${h}h${String(rem).padStart(2, '0')}` : `${h}h`
}
