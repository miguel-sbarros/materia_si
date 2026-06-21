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

function yTickFormatter(v) {
  return `R$ ${(v / 1000).toFixed(0)}k`
}

function tooltipFormatter(value) {
  return [`R$ ${value.toLocaleString('pt-BR')}`, 'Receita']
}

export default function RevenueChart({ data = [] }) {
  if (data.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center rounded-xl bg-slate-50 border border-slate-100">
        <p className="text-sm text-slate-400">Sem receita registrada no período.</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={data}
        barCategoryGap="28%"
        margin={{ top: 4, right: 4, left: 4, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: '#94a3b8', fontFamily: 'Inter, sans-serif' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={yTickFormatter}
          tick={{ fontSize: 11, fill: '#94a3b8', fontFamily: 'Inter, sans-serif' }}
          axisLine={false}
          tickLine={false}
          width={68}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ fontWeight: 600, color: '#0f172a', marginBottom: 4 }}
          itemStyle={{ color: '#475569', fontSize: 12 }}
          formatter={tooltipFormatter}
          cursor={{ fill: 'rgba(37, 99, 235, 0.04)' }}
        />
        <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
