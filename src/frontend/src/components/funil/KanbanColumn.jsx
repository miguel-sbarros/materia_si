import { memo } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import LeadCard from './LeadCard.jsx'

function KanbanColumn({ column, cards, activeId }) {
  const { setNodeRef: setDropRef, isOver } = useDroppable({ id: column.id })
  const isPerdido = column.id === 'Perdido'
  const cardIds = cards.map((c) => c.id)

  return (
    <div className="flex-shrink-0 w-80">
      {/* Column header */}
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${column.dotColor}`} />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 font-headline">
            {column.label}
          </h3>
        </div>
        <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
          {String(cards.length).padStart(2, '0')}
        </span>
      </div>

      {/* Drop area */}
      <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
        <div
          ref={setDropRef}
          className={`space-y-3 min-h-[100px] rounded-xl transition-colors duration-150 ${isOver ? 'bg-blue-50/60' : ''}`}
        >
          {isPerdido && cards.length === 0 ? (
            <div className="bg-slate-50 p-6 rounded-xl border border-dashed border-slate-200 flex flex-col items-center justify-center text-center opacity-60">
              <span className="text-2xl mb-2">🗑️</span>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Área de Arquivo</p>
            </div>
          ) : (
            cards.map((card) => (
              <LeadCard key={card.id} card={card} isDragging={activeId === card.id} />
            ))
          )}
        </div>
      </SortableContext>
    </div>
  )
}

export default memo(KanbanColumn)
