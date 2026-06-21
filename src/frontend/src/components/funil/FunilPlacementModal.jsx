import { memo, useCallback, useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getCourses } from '../../lib/api.js'
import FunilPlacementFields from './FunilPlacementFields.jsx'
import { EMPTY_PLACEMENT, isPlacementValid } from './constants.js'

// Modal de posicionamento no Funil para um lead recém-criado por import (.zip).
// Coleta curso → turma + estágio aberto e chama `onConfirm({ cohortId, stage })`.
// Cancelar deixa o lead fora do quadro (decisão aceita).
function FunilPlacementModal({ leadName, onCancel, onConfirm, submitting, error }) {
  const [placement, setPlacement] = useState(EMPTY_PLACEMENT)
  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: getCourses })

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

  const canConfirm = isPlacementValid(placement)

  const handleConfirm = useCallback(
    (e) => {
      e.preventDefault()
      if (!canConfirm || submitting) return
      onConfirm({ cohortId: Number(placement.cohortId), stage: placement.stage })
    },
    [canConfirm, submitting, placement, onConfirm],
  )

  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900 font-headline">Posicionar no Funil</h2>
          <button onClick={onCancel} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <p className="text-sm text-slate-500 mb-4">
          Novo lead <span className="font-semibold text-slate-700">{leadName}</span> criado. Escolha a
          turma e o estágio para colocá-lo no quadro.
        </p>

        <form onSubmit={handleConfirm} className="space-y-4">
          <FunilPlacementFields courses={courses} value={placement} onChange={setPlacement} />

          {error ? <p className="text-xs font-semibold text-red-600">{error}</p> : null}

          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={onCancel}
              className="border border-slate-200 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              Pular
            </button>
            <button
              type="submit"
              disabled={submitting || !canConfirm}
              className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8] transition-colors disabled:opacity-50"
            >
              {submitting ? 'Salvando…' : 'Adicionar ao Funil'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default memo(FunilPlacementModal)
