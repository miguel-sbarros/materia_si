import { memo } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { CheckCircle, Archive } from 'lucide-react'

// Um dos dois alvos de fechamento da close drop-zone.
function CloseTarget({ id, label, hint, Icon, active, tone }) {
  const { setNodeRef, isOver } = useDroppable({ id })
  const t = tone === 'won' ? wonTone : lostTone
  const state = isOver ? t.over : active ? t.armed : t.idle

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 flex items-center justify-center gap-3 rounded-xl border-2 border-dashed px-5 py-4 transition-all duration-150 ${state}`}
    >
      <Icon size={20} className="flex-shrink-0" />
      <div className="text-left">
        <p className="text-sm font-bold leading-tight">{label}</p>
        <p className="text-[11px] opacity-70 leading-tight">{hint}</p>
      </div>
    </div>
  )
}

// Estados de cor por alvo. `idle` = repouso (discreto), `armed` = card sendo arrastado
// (destaca a zona), `over` = card pairando sobre este alvo.
const wonTone = {
  idle: 'border-slate-200 text-slate-400 bg-white',
  armed: 'border-emerald-300 text-emerald-600 bg-emerald-50/40',
  over: 'border-emerald-500 text-emerald-700 bg-emerald-50 ring-2 ring-emerald-200',
}
const lostTone = {
  idle: 'border-slate-200 text-slate-400 bg-white',
  armed: 'border-red-300 text-red-500 bg-red-50/40',
  over: 'border-red-500 text-red-600 bg-red-50 ring-2 ring-red-200',
}

// Rodapé do funil: arraste um card aqui para fechar o deal (won/lost).
// `active` = há um card sendo arrastado no momento (destaca a zona).
function CloseDropZone({ active }) {
  return (
    <div
      className={`mt-6 rounded-2xl border border-slate-200 p-4 transition-all duration-150 ${
        active ? 'bg-slate-50 shadow-sm' : 'bg-white/60'
      }`}
    >
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3 px-1">
        Arraste para fechar o deal
      </p>
      <div className="flex flex-col sm:flex-row gap-3">
        <CloseTarget
          id="close-matriculado"
          label="Matriculado"
          hint="Marcar como ganho"
          Icon={CheckCircle}
          tone="won"
          active={active}
        />
        <CloseTarget
          id="close-perdido"
          label="Perdido"
          hint="Informar motivo da perda"
          Icon={Archive}
          tone="lost"
          active={active}
        />
      </div>
    </div>
  )
}

export default memo(CloseDropZone)
