import { memo, lazy, Suspense } from 'react'
import { Users, Zap, Target, Download, GitBranch, Sparkles, AlertCircle, TrendingUp, MessageSquare } from 'lucide-react'
import { analyticsData, aiAnalysis } from '../data/mock.js'

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
  badge,
  badgeBg,
  badgeText,
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
          <span className={`text-xs font-bold px-2 py-1 rounded-full ${badgeBg} ${badgeText}`}>
            {badge}
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
  const churnedBg = churned > 30 ? '#fecaca' : '#fee2e2'

  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-sm font-bold text-slate-900">{label}</span>
        <span className="text-sm font-medium text-slate-500">{churned}% Churn</span>
      </div>
      <div className="h-12 w-full bg-white rounded-lg flex overflow-hidden">
        <div
          style={{ width: `${retained}%`, backgroundColor: `rgba(37, 99, 235, ${opacity})` }}
        />
        <div style={{ width: `${churned}%`, backgroundColor: churnedBg }} />
      </div>
    </div>
  )
})

// ─── Derived data (rerender-derived-state-no-effect) ─────────────────────────
const { kpis, funnelStages, spinAbandonment, avgResponseTime, peakHour, totalRevenue, revenueGrowth } =
  analyticsData

const maxFunnelCount = Math.max(...funnelStages.map(s => s.count))

const KPI_CONFIG = [
  {
    Icon: Users,
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-700',
    label: 'Total de Leads',
    value: kpis.totalLeads,
    badge: '+4.2%',
    badgeBg: 'bg-emerald-50',
    badgeText: 'text-emerald-600',
    subtext: 'Leads qualificados no funil atual',
    valueColor: 'text-[#2563EB]',
  },
  {
    Icon: Zap,
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-700',
    label: 'Novos Leads Hoje',
    value: kpis.newLeadsToday,
    badge: 'Ativos Agora',
    badgeBg: 'bg-orange-50',
    badgeText: 'text-orange-600',
    subtext: 'Novas oportunidades identificadas desde 00:00',
    valueColor: 'text-slate-900',
  },
  {
    Icon: Target,
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-700',
    label: 'Taxa de Conversão',
    value: `${kpis.conversionRate}%`,
    badge: 'Top 5%',
    badgeBg: 'bg-purple-50',
    badgeText: 'text-purple-600',
    subtext: 'Taxa de lead para matriculado',
    valueColor: 'text-slate-900',
  },
]

// ─── ICP Card ────────────────────────────────────────────────────────────────
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
      <div className="grid grid-cols-6 gap-3 mb-6">
        {icp.attributes.map(attr => (
          <div key={attr.label} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">{attr.label}</p>
            <p className="text-sm font-bold text-slate-900">{attr.value}</p>
          </div>
        ))}
      </div>
      <div className="flex items-start gap-3 p-4 bg-blue-50/60 rounded-xl border-l-4 border-[#2563EB]">
        <TrendingUp size={15} className="text-[#2563EB] mt-0.5 shrink-0" />
        <p className="text-xs text-slate-600 leading-relaxed">{icp.insight}</p>
      </div>
    </div>
  )
})

// ─── Persona Card ─────────────────────────────────────────────────────────────
const PERSONA_COLORS = {
  blue:    { bg: 'bg-blue-50',    text: 'text-blue-700',    badge: 'bg-blue-100 text-blue-700',       dot: 'bg-blue-500'    },
  purple:  { bg: 'bg-purple-50',  text: 'text-purple-700',  badge: 'bg-purple-100 text-purple-700',   dot: 'bg-purple-500'  },
  orange:  { bg: 'bg-orange-50',  text: 'text-orange-700',  badge: 'bg-orange-100 text-orange-700',   dot: 'bg-orange-500'  },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-700', badge: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
}

const PersonaCard = memo(function PersonaCard({ persona }) {
  const c = PERSONA_COLORS[persona.color]
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center shrink-0`}>
          <Users size={18} className={c.text} />
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${c.badge}`}>
          {persona.badge}
        </span>
      </div>
      <h4 className="text-sm font-bold text-slate-900 mb-2 font-headline">{persona.name}</h4>
      <p className="text-xs text-slate-500 leading-relaxed mb-4">{persona.description}</p>
      <div className="space-y-1.5 mb-4">
        {persona.traits.map(t => (
          <div key={t} className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${c.dot}`} />
            <span className="text-xs text-slate-600">{t}</span>
          </div>
        ))}
      </div>
      <div className="mt-auto pt-4 border-t border-slate-50">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">Principal Dor</p>
        <p className="text-xs text-slate-600 leading-relaxed">{persona.painPoint}</p>
      </div>
      <div className="mt-3 flex items-center gap-1.5">
        <MessageSquare size={11} className="text-slate-400" />
        <span className="text-[10px] text-slate-400">{persona.channel}</span>
      </div>
    </div>
  )
})

// ─── Pain Point Row ───────────────────────────────────────────────────────────
const SEVERITY = {
  high: { bar: 'bg-red-400', badge: 'bg-red-50 text-red-600' },
  medium: { bar: 'bg-amber-400', badge: 'bg-amber-50 text-amber-600' },
  low: { bar: 'bg-slate-300', badge: 'bg-slate-100 text-slate-500' },
}

const PainPointRow = memo(function PainPointRow({ point }) {
  const s = SEVERITY[point.severity]
  const pct = parseInt(point.affected)
  return (
    <div className="flex items-center gap-4 py-3.5 border-b border-slate-50 last:border-0">
      <span className="text-xs font-extrabold text-slate-300 w-4 shrink-0">#{point.rank}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-sm font-bold text-slate-800 truncate">{point.title}</p>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${s.badge}`}>
            {point.affected}
          </span>
        </div>
        <p className="text-xs text-slate-400 truncate">{point.description}</p>
      </div>
      <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden shrink-0">
        <div className={`h-full ${s.bar} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
})

// Decreasing opacity per SPIN stage (matching prototype visual gradient)
const SPIN_OPACITIES = [1.0, 0.8, 0.6, 0.4]

// ─── Analytics Page ───────────────────────────────────────────────────────────
export default function Analytics() {
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
        {KPI_CONFIG.map(card => (
          <KpiCard key={card.label} {...card} />
        ))}
      </div>

      {/* ── Funnel Status ── */}
      <section className="mb-8">
        <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2 font-headline">
          <GitBranch size={17} className="text-[#2563EB]" />
          Status do Funil de Leads
        </h3>
        <div className="grid grid-cols-5 gap-4">
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
              Últimos 30 dias
            </span>
          </div>
          <div className="space-y-7">
            {spinAbandonment.map((row, i) => (
              <SpinRow
                key={row.stage}
                stage={row.stage}
                retained={row.retained}
                churned={row.churned}
                opacity={SPIN_OPACITIES[i]}
              />
            ))}
          </div>
          <div className="mt-8 p-4 bg-blue-50/60 rounded-xl border-l-4 border-[#2563EB]">
            <p className="text-xs leading-relaxed text-slate-600 italic">
              O abandono é maior no estágio de{' '}
              <strong className="text-slate-800">Implicação</strong>. Considere
              refinar os roteiros de proposta de valor para o paciente.
            </p>
          </div>
        </div>

        {/* Conversation Trends — col-span-7 */}
        <div className="col-span-7 bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900 font-headline">
                Tendências de Conversa
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Interações em todos os canais médicos
              </p>
            </div>
            <div className="flex gap-2">
              <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-bold">
                <span className="w-2 h-2 rounded-full bg-blue-700" />
                WhatsApp
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 text-slate-500 rounded-full text-xs font-bold">
                <span className="w-2 h-2 rounded-full bg-slate-300" />
                Chamadas
              </span>
            </div>
          </div>

          <Suspense fallback={<ChartSkeleton height="h-60" />}>
            <LazyConversationChart />
          </Suspense>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Tempo Médio de Resposta</p>
              <p className="text-xl font-bold text-slate-900">{avgResponseTime}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Horário de Pico</p>
              <p className="text-xl font-bold text-slate-900">{peakHour}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Revenue Chart (full width) ── */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-base font-bold text-slate-900 font-headline">
              Histórico de Receita Mensal e Projeção de Crescimento
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Barras sólidas = realizado · Barras tracejadas = projeção
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
              Faturamento Total (Ano)
            </p>
            <p className="text-2xl font-extrabold text-[#2563EB]">
              R$ {totalRevenue.toLocaleString('pt-BR')}
            </p>
            <p className="text-sm font-semibold text-emerald-600 mt-0.5">
              {revenueGrowth} vs. ano anterior
            </p>
          </div>
        </div>

        <Suspense fallback={<ChartSkeleton height="h-72" />}>
          <LazyRevenueChart />
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
            Gerado por IA · Atualizado há 2h
          </span>
        </div>

        {/* ICP */}
        <IcpCard icp={aiAnalysis.icp} />

        {/* Personas + Pain Points */}
        <div className="grid grid-cols-12 gap-6">
          {/* Personas — col-span-7 */}
          <div className="col-span-7 space-y-4">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Personas Identificadas</p>
            <div className="grid grid-cols-2 gap-4">
              {aiAnalysis.personas.map(p => (
                <PersonaCard key={p.id} persona={p} />
              ))}
            </div>
          </div>

          {/* Pain Points — col-span-5 */}
          <div className="col-span-5 bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Principais Dores</p>
              <AlertCircle size={14} className="text-slate-300" />
            </div>
            <div>
              {aiAnalysis.painPoints.map(p => (
                <PainPointRow key={p.rank} point={p} />
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
