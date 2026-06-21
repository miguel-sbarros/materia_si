import { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Clock, Calendar, CheckCircle } from 'lucide-react'
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

  const isNegociando = card.column === 'Negociando'
  const isMatriculado = card.column === 'Matriculado'

  if (isMatriculado) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        {...listeners}
        onClick={openLead}
        className="bg-emerald-50/40 p-5 rounded-xl shadow-sm border-2 border-dashed border-emerald-100 cursor-pointer active:cursor-grabbing"
      >
        <div className="mb-3">
          <CheckCircle size={16} className="text-emerald-500" />
        </div>
        <h4 className="font-bold text-sm text-slate-900 mb-1">{card.name}</h4>
        <p className="text-xs text-slate-500">{card.course}</p>
      </div>
    )
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={openLead}
      className="bg-white p-5 rounded-xl shadow-sm border-b-2 border-transparent hover:border-blue-200 transition-all cursor-pointer active:cursor-grabbing group"
    >
      {/* Source badge + priority label */}
      <div className="flex justify-between items-start mb-3">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter ${SOURCE_COLORS[card.source] ?? 'bg-slate-100 text-slate-600'}`}>
          {card.source ?? '—'}
        </span>
        {isNegociando ? (
          <span className="text-[10px] font-bold text-blue-600">Prioridade Alta</span>
        ) : null}
      </div>

      {/* Name + course */}
      <h4 className="font-bold text-sm text-slate-900 mb-1">{card.name}</h4>
      <p className={`text-xs text-slate-500 ${isNegociando ? 'mb-3' : 'mb-4'}`}>{card.course}</p>

      {isNegociando ? (
        <>
          {/* Progress bar */}
          <div className="h-1 w-full bg-slate-100 rounded-full mb-3 overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full" style={{ width: '75%' }} />
          </div>
          {/* Value + follow-up */}
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-900">
              {card.value
                ? `R$ ${card.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                : '—'}
            </span>
            <div className="flex items-center gap-1 text-[10px] text-slate-400">
              <Calendar size={10} />
              Follow-up: {relativeTime(card.updatedAt)}
            </div>
          </div>
        </>
      ) : (
        <div className="flex items-center justify-between pt-4 border-t border-slate-50">
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
      )}
    </div>
  )
}

export default memo(LeadCard)
