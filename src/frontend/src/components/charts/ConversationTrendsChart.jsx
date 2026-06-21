import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const tooltipStyle = {
  fontSize: 12,
  fontFamily: 'Inter, sans-serif',
  borderRadius: 8,
  border: '1px solid #e2e8f0',
  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
}

// Formata 'YYYY-MM-DD' → 'DD/MM' (eixo X compacto)
function weekTickFormatter(iso) {
  if (!iso) return ''
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

function tooltipFormatter(value) {
  return [value, 'Mensagens']
}

export default function ConversationTrendsChart({ data = [] }) {
  if (data.length === 0) {
    return (
      <div className="h-60 flex items-center justify-center rounded-xl bg-slate-50 border border-slate-100">
        <p className="text-sm text-slate-400">Sem atividade de mensagens no período.</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart
        data={data}
        barCategoryGap="32%"
        margin={{ top: 4, right: 4, left: -16, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="week"
          tickFormatter={weekTickFormatter}
          tick={{ fontSize: 11, fill: '#94a3b8', fontFamily: 'Inter, sans-serif' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#94a3b8', fontFamily: 'Inter, sans-serif' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ fontWeight: 600, color: '#0f172a', marginBottom: 4 }}
          itemStyle={{ color: '#475569', fontSize: 12 }}
          labelFormatter={weekTickFormatter}
          formatter={tooltipFormatter}
          cursor={{ fill: 'rgba(37, 99, 235, 0.04)' }}
        />
        <Bar dataKey="count" name="Mensagens" fill="#2563EB" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
