import { memo, useCallback, useEffect, useState } from 'react'
import { X } from 'lucide-react'

const INPUT_CLASS =
  'w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#2563EB] focus:outline-none focus:ring-1 focus:ring-[#2563EB]'

const MODALITIES = ['Presencial', 'Híbrido', 'EAD']

function buildInitialForm(course) {
  return {
    name: course?.name ?? '',
    description: course?.description ?? '',
    modality: course?.modality ?? '',
    price: course?.price != null ? String(course.price) : '',
    duration: course?.duration ?? '',
  }
}

// Modal "Novo Curso" / "Editar Curso". `course` presente = modo edição (prefill).
function CourseModal({ course, onClose, onSave, submitting, error }) {
  const isEdit = Boolean(course)
  const [form, setForm] = useState(() => buildInitialForm(course))

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
        description: form.description.trim() || null,
        modality: form.modality || null,
        price: form.price.trim() === '' ? null : Number(form.price),
        duration: form.duration.trim() || null,
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
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-slate-900 font-headline">
            {isEdit ? 'Editar Curso' : 'Novo Curso'}
          </h2>
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
              placeholder="Nome do curso"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Descrição</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              rows={3}
              placeholder="Resumo do curso"
              className={`${INPUT_CLASS} resize-none`}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Modalidade</label>
            <select name="modality" value={form.modality} onChange={handleChange} className={INPUT_CLASS}>
              <option value="">Selecione...</option>
              {MODALITIES.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Preço (R$)</label>
            <input
              name="price"
              value={form.price}
              onChange={handleChange}
              type="number"
              min="0"
              step="0.01"
              placeholder="0,00"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Carga horária</label>
            <input
              name="duration"
              value={form.duration}
              onChange={handleChange}
              placeholder="Ex.: 40h"
              className={INPUT_CLASS}
            />
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

export default memo(CourseModal)
