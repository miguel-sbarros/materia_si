import { memo, useEffect } from 'react'
import { X } from 'lucide-react'

// Confirmação ao anexar um lead quando a conversa atual já tem um lead anexado.
// Confirmar → inicia uma NOVA conversa com o lead; cancelar → descarta sem mudar.
function ConfirmNewSessionModal({ leadName, onCancel, onConfirm }) {
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

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
          <h2 className="text-lg font-bold text-slate-900 font-headline">
            Já existe um lead nesta conversa
          </h2>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <p className="text-sm text-slate-500 mb-6">
          Anexar{leadName ? <span className="font-semibold text-slate-700"> {leadName}</span> : ' outro lead'} iniciará uma{' '}
          <span className="font-semibold text-slate-700">nova conversa</span>. Deseja continuar?
        </p>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="border border-slate-200 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8] transition-colors"
          >
            Iniciar nova conversa
          </button>
        </div>
      </div>
    </div>
  )
}

export default memo(ConfirmNewSessionModal)
