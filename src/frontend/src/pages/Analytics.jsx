import { memo, lazy, Suspense } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, Zap, Target, Download, GitBranch, Sparkles, AlertCircle, TrendingUp } from 'lucide-react'
import { getAnalytics } from '../lib/api.js'

// ─── Lazy chart imports (bundle-dynamic-imports) ─────────────────────────────
const LazyConversationChart = lazy(() =>
  import('../components/charts/ConversationTrendsChart.jsx')
)
const LazyRevenueChart = lazy(() =>
  import('../components/charts/RevenueChart.jsx')
)

// ─── Chart skeleton (used as Suspense fallback) ───────────────────────────────
function ChartSkeleton({ height = 'h-64' }) {
  return <div className={`${height} rounded-xl bg-slate-100 animate-pulse`} />
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
const KpiCard = memo(function KpiCard({
  Icon,
  iconBg,
  iconColor,
  label,
  value,
  subtext,
  valueColor,
}) {
  return (
    <div className="p-8 rounded-2xl bg-white shadow-sm flex flex-col justify-between border border-slate-100/80">
      <div>
        <div className="flex justify-between items-start mb-4">
          <span className={`p-2 ${iconBg} ${iconColor} rounded-lg`}>
            <Icon size={22} />
          </span>
        </div>
        <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
        <h3 className={`text-5xl font-extrabold mt-2 ${valueColor}`}>{value}</h3>
      </div>
      <div className="mt-6 pt-6 border-t border-slate-50">
        <p className="text-xs text-slate-400">{subtext}</p>
      </div>
    </div>
  )
})

// ─── Funnel Stage Card ────────────────────────────────────────────────────────
const FunnelStageCard = memo(function FunnelStageCard({
  name,
  count,
  barWidthPct,
  isHighlighted,
  isLost,
}) {
  const countColor = isHighlighted
    ? 'text-[#2563EB]'
    : isLost
    ? 'text-slate-400'
    : 'text-slate-900'
  const barColor = isLost ? 'bg-slate-400' : 'bg-[#2563EB]'

  return (
    <div className="bg-slate-50 p-6 rounded-xl hover:bg-white hover:shadow-sm transition-all group cursor-default border border-slate-100">
      <p className="text-xs font-bold text-slate-500 mb-1 group-hover:text-[#2563EB] uppercase tracking-wide">
        {name}
      </p>
      <p className={`text-2xl font-extrabold ${countColor}`}>{count}</p>
      <div className="mt-4 h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all`}
          style={{ width: `${barWidthPct}%` }}
        />
      </div>
    </div>
  )
})

// ─── SPIN Row ─────────────────────────────────────────────────────────────────
const SpinRow = memo(function SpinRow({ stage, retained, churned, opacity }) {
  const label = stage === 'Necessidade' ? 'Necessidade de Solução' : stage
  const total = retained + churned
  const retainedPct = total > 0 ? (retained / total) * 100 : 0
  const churnedPct = total > 0 ? (churned / total) * 100 : 0
  const churnedBg = churnedPct > 30 ? '#fecaca' : '#fee2e2'

  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-sm font-bold text-slate-900">{label}</span>
        <span className="text-sm font-medium text-slate-500">{Math.round(churnedPct)}% Churn</span>
      </div>
      <div className="h-12 w-full bg-white rounded-lg flex overflow-hidden">
        <div
          style={{ width: `${retainedPct}%`, backgroundColor: `rgba(37, 99, 235, ${opacity})` }}
        />
        <div style={{ width: `${churnedPct}%`, backgroundColor: churnedBg }} />
      </div>
    </div>
  )
})

// ─── ICP Card (resumo derivado da persona dominante) ──────────────────────────
const IcpCard = memo(function IcpCard({ icp }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-8">
      <div className="flex justify-between items-start mb-6">
        <div>
          <p className="text-[10px] font-bold text-[#2563EB] uppercase tracking-widest mb-1">Perfil de Cliente Ideal (ICP)</p>
          <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">{icp.summary}</p>
        </div>
        <div className="shrink-0 ml-6 p-3 bg-blue-50 rounded-xl">
          <Users size={22} className="text-[#2563EB]" />
        </div>
      </div>
      {icp.insight && (
        <div className="flex items-start gap-3 p-4 bg-blue-50/60 rounded-xl border-l-4 border-[#2563EB]">
          <TrendingUp size={15} className="text-[#2563EB] mt-0.5 shrink-0" />
          <p className="text-xs text-slate-600 leading-relaxed">{icp.insight}</p>
        </div>
      )}
    </div>
  )
})

// ─── Persona Card ─────────────────────────────────────────────────────────────
const PERSONA_COLORS = [
  { bg: 'bg-blue-50',    text: 'text-blue-700',    badge: 'bg-blue-100 text-blue-700',       dot: 'bg-blue-500'    },
  { bg: 'bg-purple-50',  text: 'text-purple-700',  badge: 'bg-purple-100 text-purple-700',   dot: 'bg-purple-500'  },
  { bg: 'bg-orange-50',  text: 'text-orange-700',  badge: 'bg-orange-100 text-orange-700',   dot: 'bg-orange-500'  },
  { bg: 'bg-emerald-50', text: 'text-emerald-700', badge: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
]

const PersonaCard = memo(function PersonaCard({ persona, colorIndex }) {
  const c = PERSONA_COLORS[colorIndex % PERSONA_COLORS.length]
  const dores = persona.topDores ?? []
  const desejos = persona.topDesejos ?? []
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center shrink-0`}>
          <Users size={18} className={c.text} />
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${c.badge}`}>
          {persona.conversionRate}% conv.
        </span>
      </div>
      <h4 className="text-sm font-bold text-slate-900 mb-1 font-headline">{persona.persona}</h4>
      <p className="text-[11px] font-semibold text-slate-400 mb-2">{persona.leads} leads</p>
      <p className="text-xs text-slate-500 leading-relaxed mb-4">{persona.description ?? '—'}</p>
      {desejos.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {desejos.slice(0, 3).map(t => (
            <div key={t} className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${c.dot}`} />
              <span className="text-xs text-slate-600">{t}</span>
            </div>
          ))}
        </div>
      )}
      <div className="mt-auto pt-4 border-t border-slate-50">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">Principais Dores</p>
        <p className="text-xs text-slate-600 leading-relaxed">
          {dores.length > 0 ? dores.slice(0, 3).join(' · ') : '—'}
        </p>
      </div>
    </div>
  )
})

// ─── Pain Point Row ───────────────────────────────────────────────────────────
const PainPointRow = memo(function PainPointRow({ point, barPct }) {
  return (
    <div className="flex items-center gap-4 py-3.5 border-b border-slate-50 last:border-0">
      <span className="text-xs font-extrabold text-slate-300 w-4 shrink-0">#{point.rank}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-sm font-bold text-slate-800 truncate">{point.title}</p>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 bg-red-50 text-red-600">
            {point.count} leads
          </span>
        </div>
      </div>
      <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden shrink-0">
        <div className="h-full bg-red-400 rounded-full" style={{ width: `${barPct}%` }} />
      </div>
    </div>
  )
})

// Decreasing opacity per SPIN stage (matching prototype visual gradient)
const SPIN_OPACITIES = [1.0, 0.8, 0.6, 0.4]

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmtSeconds(s) {
  if (s == null) return '—'
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  const rest = s % 60
  return rest ? `${m}m ${rest}s` : `${m}min`
}

function fmtHour(h) {
  if (h == null) return '—'
  return `${String(h).padStart(2, '0')}h`
}

// Resumo de ICP derivado da persona dominante (sem números fabricados)
function deriveIcp(personas) {
  if (!personas || personas.length === 0) {
    return { summary: 'Ainda não há leads analisados suficientes para inferir um perfil ideal.', insight: null }
  }
  const top = [...personas].sort((a, b) => b.leads - a.leads)[0]
  const dores = (top.topDores ?? []).slice(0, 2).join(', ')
  const desejos = (top.topDesejos ?? []).slice(0, 2).join(', ')
  const summary = `Perfil predominante: ${top.persona} (${top.leads} leads, ${top.conversionRate}% de conversão).` +
    (top.description ? ` ${top.description}` : '')
  const insight = (dores || desejos)
    ? `Principais dores: ${dores || '—'}. Principais desejos: ${desejos || '—'}.`
    : null
  return { summary, insight }
}

// ─── Loading / Error states ─────────────────────────────────────────────────
function AnalyticsSkeleton() {
  return (
    <div className="pb-8 space-y-8">
      <div className="h-10 w-80 bg-slate-100 rounded-lg animate-pulse" />
      <div className="grid grid-cols-3 gap-6">
        {[0, 1, 2].map(i => (
          <div key={i} className="h-44 rounded-2xl bg-slate-100 animate-pulse" />
        ))}
      </div>
      <div className="h-32 rounded-2xl bg-slate-100 animate-pulse" />
      <div className="h-72 rounded-2xl bg-slate-100 animate-pulse" />
    </div>
  )
}

function AnalyticsError() {
  return (
    <div className="pb-8">
      <div className="flex flex-col items-center justify-center gap-3 py-24 text-center">
        <AlertCircle size={40} className="text-red-400" />
        <p className="text-lg font-bold text-slate-800">Não foi possível carregar as análises</p>
        <p className="text-sm text-slate-500">Verifique a conexão com o servidor e tente novamente.</p>
      </div>
    </div>
  )
}

// ─── Analytics Page ───────────────────────────────────────────────────────────
export default function Analytics() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics'],
    queryFn: getAnalytics,
  })

  if (isLoading) return <AnalyticsSkeleton />
  if (isError || !data) return <AnalyticsError />

  const {
    kpis,
    funnelStages,
    spin,
    personas,
    painPoints,
    revenue,
    latency,
    abandonmentRate,
    messageActivity,
  } = data

  const kpiCards = [
    {
      Icon: Users,
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-700',
      label: 'Total de Leads',
      value: kpis.totalLeads,
      subtext: 'Leads qualificados no funil atual',
      valueColor: 'text-[#2563EB]',
    },
    {
      Icon: Zap,
      iconBg: 'bg-orange-50',
      iconColor: 'text-orange-700',
      label: 'Novos Leads Hoje',
      value: kpis.newLeadsToday,
      subtext: 'Novas oportunidades identificadas desde 00:00',
      valueColor: 'text-slate-900',
    },
    {
      Icon: Target,
      iconBg: 'bg-purple-50',
      iconColor: 'text-purple-700',
      label: 'Taxa de Conversão',
      value: `${kpis.conversionRate}%`,
      subtext: 'Taxa de lead para matriculado',
      valueColor: 'text-slate-900',
    },
  ]

  const maxFunnelCount = Math.max(1, ...funnelStages.map(s => s.count))
  const maxPainCount = Math.max(1, ...painPoints.map(p => p.count))
  const icp = deriveIcp(personas)
  const abandonPct = Math.round((abandonmentRate ?? 0) * 100)

  return (
    <div className="pb-8">
      {/* ── Page Header ── */}
      <section className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-1 font-headline">
            Visão Geral de Performance
          </h2>
          <p className="text-slate-500 font-medium text-sm">
            Monitoramento de métricas de aquisição e retenção de pacientes.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-semibold text-sm hover:bg-slate-200 transition-colors">
            Últimos 30 Dias
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-[#2563EB] text-white rounded-lg font-semibold text-sm shadow-md shadow-blue-500/20 hover:bg-[#1D4ED8] transition-colors">
            <Download size={15} />
            Exportar Relatório
          </button>
        </div>
      </section>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        {kpiCards.map(card => (
          <KpiCard key={card.label} {...card} />
        ))}
      </div>

      {/* ── Funnel Status ── */}
      <section className="mb-8">
        <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2 font-headline">
          <GitBranch size={17} className="text-[#2563EB]" />
          Status do Funil de Leads
        </h3>
        <div className="grid grid-cols-6 gap-4">
          {funnelStages.map(stage => (
            <FunnelStageCard
              key={stage.name}
              name={stage.name}
              count={stage.count}
              barWidthPct={Math.round((stage.count / maxFunnelCount) * 100)}
              isHighlighted={stage.name === 'Matriculado'}
              isLost={stage.name === 'Perdido'}
            />
          ))}
        </div>
      </section>

      {/* ── Charts row: SPIN + Conversation ── */}
      <div className="grid grid-cols-12 gap-6 mb-6">

        {/* SPIN Abandonment — col-span-5 */}
        <div className="col-span-5 bg-slate-50 p-8 rounded-2xl border border-slate-100">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-base font-bold text-slate-900 font-headline">
              Abandono por Estágio (SPIN)
            </h3>
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded-full">
              Conversas analisadas
            </span>
          </div>
          <div className="space-y-7">
            {spin.map((row, i) => (
              <SpinRow
                key={row.stage}
                stage={row.stage}
                retained={row.retained}
                churned={row.churned}
                opacity={SPIN_OPACITIES[i] ?? 0.4}
              />
            ))}
          </div>
          <div className="mt-8 p-4 bg-blue-50/60 rounded-xl border-l-4 border-[#2563EB]">
            <p className="text-xs leading-relaxed text-slate-600 italic">
              Taxa geral de abandono das conversas:{' '}
              <strong className="text-slate-800">{abandonPct}%</strong>. Cada barra
              compara leads que avançaram (azul) vs. que abandonaram (vermelho) no estágio SPIN.
            </p>
          </div>
        </div>

        {/* Conversation Trends — col-span-7 */}
        <div className="col-span-7 bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900 font-headline">
                Volume de Mensagens (WhatsApp)
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Mensagens trocadas por semana
              </p>
            </div>
            <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-bold">
              <span className="w-2 h-2 rounded-full bg-blue-700" />
              WhatsApp
            </span>
          </div>

          <Suspense fallback={<ChartSkeleton height="h-60" />}>
            <LazyConversationChart data={messageActivity.weekly} />
          </Suspense>

          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Tempo Médio de Resposta</p>
              <p className="text-xl font-bold text-slate-900">
                {fmtSeconds(messageActivity.avgResponseSeconds ?? latency.medianSellerSeconds)}
              </p>
            </div>
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">1ª Resposta (mediana)</p>
              <p className="text-xl font-bold text-slate-900">{fmtSeconds(latency.firstResponseSeconds)}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Horário de Pico</p>
              <p className="text-xl font-bold text-slate-900">{fmtHour(messageActivity.peakHour)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Revenue Chart (full width) ── */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 font-headline">
              Histórico de Receita Mensal
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Receita realizada por mês (matrículas fechadas)
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Faturamento Total
            </p>
            <p className="text-2xl font-extrabold text-[#2563EB]">
              R$ {revenue.total.toLocaleString('pt-BR')}
            </p>
          </div>
        </div>

        <Suspense fallback={<ChartSkeleton height="h-72" />}>
          <LazyRevenueChart data={revenue.byMonth} />
        </Suspense>
      </div>

      {/* ── AI Insights ── */}
      <section className="mt-8 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2 font-headline">
            <Sparkles size={17} className="text-[#2563EB]" />
            Análise de Inteligência Artificial
          </h3>
          <span className="text-[10px] font-bold text-slate-400 bg-slate-100 px-3 py-1 rounded-full uppercase tracking-widest">
            Gerado por IA
          </span>
        </div>

        {/* ICP */}
        <IcpCard icp={icp} />

        {/* Personas + Pain Points */}
        <div className="grid grid-cols-12 gap-6">
          {/* Personas — col-span-7 */}
          <div className="col-span-7 space-y-4">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Personas Identificadas</p>
            {personas.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {personas.map((p, i) => (
                  <PersonaCard key={p.persona} persona={p} colorIndex={i} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">Nenhuma persona identificada ainda.</p>
            )}
          </div>

          {/* Pain Points — col-span-5 */}
          <div className="col-span-5 bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Principais Dores</p>
              <AlertCircle size={14} className="text-slate-300" />
            </div>
            {painPoints.length > 0 ? (
              <div>
                {painPoints.map(p => (
                  <PainPointRow
                    key={p.rank}
                    point={p}
                    barPct={Math.round((p.count / maxPainCount) * 100)}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">Nenhuma dor recorrente identificada.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
