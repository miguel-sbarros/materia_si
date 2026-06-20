import { memo, useCallback, useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { INPUT_CLASS } from './constants.js'

// Pedido de motivo ao mover um card para "Perdido" (o backend exige lost_reason).
function LostReasonModal({ cardName, onCancel, onConfirm, submitting }) {
  const [reason, setReason] = useState('')

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault()
      if (!reason.trim()) return
      onConfirm(reason.trim())
    },
    [reason, onConfirm],
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
          <h2 className="text-lg font-bold text-slate-900 font-headline">Marcar como Perdido</h2>
          <button onClick={onCancel} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <p className="text-sm text-slate-500 mb-4">
          Informe o motivo da perda de <span className="font-semibold text-slate-700">{cardName}</span>.
          Esse registro entra no histórico do funil.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Ex.: Sem orçamento neste momento"
            rows={3}
            autoFocus
            className={`${INPUT_CLASS} resize-none`}
          />
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="border border-slate-200 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !reason.trim()}
              className="bg-red-500 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
            >
              {submitting ? 'Salvando...' : 'Confirmar Perda'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default memo(LostReasonModal)
