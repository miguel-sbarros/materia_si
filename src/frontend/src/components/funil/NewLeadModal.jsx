import { memo, useCallback, useEffect, useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { INPUT_CLASS, SOURCES } from './constants.js'

const EMPTY_FORM = { name: '', email: '', phone: '', source: '', courseId: '', cohortId: '' }

// Modal "Novo Lead": cria lead + deal inicial. Curso/turma vêm de `courses` (DB real).
function NewLeadModal({ courses, onClose, onSave, submitting, error }) {
  const [form, setForm] = useState(EMPTY_FORM)

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const cohorts = useMemo(() => {
    const course = courses?.find((c) => String(c.id) === form.courseId)
    return course?.cohorts ?? []
  }, [courses, form.courseId])

  const handleChange = useCallback((e) => {
    const { name, value } = e.target
    setForm((prev) =>
      name === 'courseId' ? { ...prev, courseId: value, cohortId: '' } : { ...prev, [name]: value },
    )
  }, [])

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault()
      if (!form.name.trim() || !form.cohortId) return
      onSave({
        name: form.name.trim(),
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        source: form.source || null,
        cohort_id: Number(form.cohortId),
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
          <h2 className="text-lg font-bold text-slate-900 font-headline">Novo Lead</h2>
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
              placeholder="Nome completo"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">E-mail</label>
            <input
              name="email"
              value={form.email}
              onChange={handleChange}
              type="email"
              placeholder="email@exemplo.com"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Telefone</label>
            <input
              name="phone"
              value={form.phone}
              onChange={handleChange}
              type="tel"
              placeholder="(11) 99999-0000"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Canal de Origem</label>
            <select name="source" value={form.source} onChange={handleChange} className={INPUT_CLASS}>
              <option value="">Selecione...</option>
              {SOURCES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Curso de Interesse *</label>
            <select name="courseId" value={form.courseId} onChange={handleChange} className={INPUT_CLASS}>
              <option value="">Selecione...</option>
              {courses?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Turma *</label>
            <select
              name="cohortId"
              value={form.cohortId}
              onChange={handleChange}
              disabled={!form.courseId}
              className={`${INPUT_CLASS} disabled:bg-slate-50 disabled:text-slate-400`}
            >
              <option value="">{form.courseId ? 'Selecione...' : 'Escolha um curso primeiro'}</option>
              {cohorts.map((co) => (
                <option key={co.id} value={co.id}>{co.name}</option>
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
              disabled={submitting || !form.name.trim() || !form.cohortId}
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

export default memo(NewLeadModal)
