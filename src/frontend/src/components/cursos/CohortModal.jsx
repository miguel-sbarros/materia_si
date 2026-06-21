import { memo, useCallback, useEffect, useState } from 'react'
import { X } from 'lucide-react'

const INPUT_CLASS =
  'w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]'

const STATUS_LABELS = {
  open: 'Inscrições abertas',
  active: 'Em andamento',
  finished: 'Encerrada',
}

function buildInitialForm(cohort) {
  return {
    name: cohort?.name ?? '',
    start_date: cohort?.start_date ?? '',
    end_date: cohort?.end_date ?? '',
    capacity: cohort?.capacity != null ? String(cohort.capacity) : '',
    price_per_slot: cohort?.price_per_slot != null ? String(cohort.price_per_slot) : '',
    status: cohort?.status ?? 'open',
  }
}

// Modal "Nova Turma" / "Editar Turma". `cohort` presente = modo edição (prefill).
function CohortModal({ cohort, courseName, onClose, onSave, submitting, error }) {
  const isEdit = Boolean(cohort)
  const [form, setForm] = useState(() => buildInitialForm(cohort))

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const handleChange = useCallback((e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }, [])

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault()
      if (!form.name.trim()) return
      onSave({
        name: form.name.trim(),
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        capacity: form.capacity.trim() === '' ? null : Number(form.capacity),
        price_per_slot: form.price_per_slot.trim() === '' ? null : Number(form.price_per_slot),
        status: form.status,
      })
    },
    [form, onSave],
  )

  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900 font-headline">
              {isEdit ? 'Editar Turma' : 'Nova Turma'}
            </h2>
            {courseName ? (
              <p className="text-xs text-slate-500 mt-0.5">{courseName}</p>
            ) : null}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Nome *</label>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Nome da turma"
              className={INPUT_CLASS}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Início</label>
              <input
                name="start_date"
                value={form.start_date}
                onChange={handleChange}
                type="date"
                className={INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Término</label>
              <input
                name="end_date"
                value={form.end_date}
                onChange={handleChange}
                type="date"
                className={INPUT_CLASS}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Vagas</label>
              <input
                name="capacity"
                value={form.capacity}
                onChange={handleChange}
                type="number"
                min="0"
                step="1"
                placeholder="0"
                className={INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Preço/vaga (R$)</label>
              <input
                name="price_per_slot"
                value={form.price_per_slot}
                onChange={handleChange}
                type="number"
                min="0"
                step="0.01"
                placeholder="0,00"
                className={INPUT_CLASS}
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Status</label>
            <select name="status" value={form.status} onChange={handleChange} className={INPUT_CLASS}>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {error ? <p className="text-xs font-semibold text-red-600">{error}</p> : null}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="border border-slate-200 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !form.name.trim()}
              className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8] transition-colors disabled:opacity-50"
            >
              {submitting ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default memo(CohortModal)
