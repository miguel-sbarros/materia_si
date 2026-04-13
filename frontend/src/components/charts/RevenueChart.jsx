import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { analyticsData } from '../../data/mock.js'

const { revenue } = analyticsData

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

function tooltipFormatter(value, _name, entry) {
  const label = entry.payload.projected ? 'Projeção' : 'Receita'
  return [`R$ ${value.toLocaleString('pt-BR')}`, label]
}

// Custom bar shape so projected bars get a dashed stroke
function ProjectedBar(props) {
  const { x, y, width, height } = props
  if (height <= 0) return null
  return (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      rx={4}
      ry={4}
      fill="rgba(37, 99, 235, 0.22)"
      stroke="#2563EB"
      strokeWidth={1.5}
      strokeDasharray="5 3"
    />
  )
}

function SolidBar(props) {
  const { x, y, width, height } = props
  if (height <= 0) return null
  return <rect x={x} y={y} width={width} height={height} rx={4} ry={4} fill="#2563EB" />
}

function CustomBar(props) {
  return props.projected ? <ProjectedBar {...props} /> : <SolidBar {...props} />
}

export default function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={revenue}
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
        <Bar dataKey="value" shape={<CustomBar />} />
      </BarChart>
    </ResponsiveContainer>
  )
}
