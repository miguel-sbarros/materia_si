import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { analyticsData } from '../../data/mock.js'

const { conversationTrends } = analyticsData

const tooltipStyle = {
  fontSize: 12,
  fontFamily: 'Inter, sans-serif',
  borderRadius: 8,
  border: '1px solid #e2e8f0',
  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
}

export default function ConversationTrendsChart() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart
        data={conversationTrends}
        barGap={4}
        barCategoryGap="32%"
        margin={{ top: 4, right: 4, left: -16, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey="period"
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
          cursor={{ fill: 'rgba(37, 99, 235, 0.04)' }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, fontFamily: 'Inter, sans-serif', paddingTop: 12 }}
        />
        <Bar dataKey="whatsapp" name="WhatsApp" fill="#2563EB" radius={[3, 3, 0, 0]} />
        <Bar dataKey="calls" name="Chamadas CRM" fill="#cbd5e1" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
