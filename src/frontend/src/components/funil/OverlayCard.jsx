import { memo } from 'react'
import { SOURCE_COLORS } from './constants.js'

// Card "fantasma" exibido sob o cursor durante o arraste.
function OverlayCard({ card }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-lg border border-slate-200 w-72 cursor-grabbing rotate-1">
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter ${SOURCE_COLORS[card.source] ?? 'bg-slate-100 text-slate-600'}`}>
        {card.source ?? '—'}
      </span>
      <h4 className="font-bold text-sm text-slate-900 mt-3 mb-1">{card.name}</h4>
      <p className="text-xs text-slate-500">{card.course}</p>
    </div>
  )
}

export default memo(OverlayCard)
