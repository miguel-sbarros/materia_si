import { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Clock } from 'lucide-react'
import { SOURCE_COLORS } from './constants.js'
import { relativeTime } from '../../lib/api.js'

// Card do quadro (um DealCard). `id` do sortable = id do deal (alvo do PATCH).
function LeadCard({ card, isDragging }) {
  const navigate = useNavigate()
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: card.id,
  })

  // Clique genuíno abre a página do lead. O PointerSensor exige 8px de movimento
  // para iniciar o drag, então o dnd-kit suprime o click após um drag de verdade —
  // só um clique sem arrasto chega aqui.
  const openLead = () => navigate(`/leadpage/${card.leadId}`)

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.35 : 1,
  }

  const value = card.value
    ? `R$ ${card.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
    : null

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={openLead}
      className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all cursor-pointer active:cursor-grabbing group"
    >
      {/* Source badge + value */}
      <div className="flex justify-between items-center mb-3">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter ${SOURCE_COLORS[card.source] ?? 'bg-slate-100 text-slate-600'}`}>
          {card.source ?? '—'}
        </span>
        {value ? (
          <span className="text-[11px] font-bold text-slate-700">{value}</span>
        ) : null}
      </div>

      {/* Name + course */}
      <h4 className="font-bold text-sm text-slate-900 mb-0.5 group-hover:text-blue-700 transition-colors">
        {card.name}
      </h4>
      <p className="text-xs text-slate-500 mb-3 truncate">{card.course}</p>

      {/* Footer: relative time + assignee avatar */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-50">
        <div className="flex items-center gap-1 text-[10px] text-slate-400">
          <Clock size={10} />
          {relativeTime(card.updatedAt)}
        </div>
        {card.assignee ? (
          <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-500 border-2 border-white">
            {card.assignee}
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default memo(LeadCard)
