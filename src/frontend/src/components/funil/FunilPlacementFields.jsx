import { memo, useMemo } from 'react'
import { INPUT_CLASS, OPEN_STAGES } from './constants.js'

// Campos compartilhados de posicionamento no Funil: curso → turma + estágio aberto.
// Controlado pelo pai via `value` ({ courseId, cohortId, stage }) + `onChange`.
// Reusado pelo wizard do .txt e pelo modal do .zip (lead recém-criado).
function FunilPlacementFields({ courses, value, onChange }) {
  const cohorts = useMemo(() => {
    const course = courses?.find((c) => String(c.id) === value.courseId)
    return course?.cohorts ?? []
  }, [courses, value.courseId])

  const setField = (name, v) =>
    onChange(
      name === 'courseId' ? { ...value, courseId: v, cohortId: '' } : { ...value, [name]: v },
    )

  return (
    <>
      <div>
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Curso de Interesse *
        </label>
        <select
          value={value.courseId}
          onChange={(e) => setField('courseId', e.target.value)}
          className={INPUT_CLASS}
        >
          <option value="">Selecione...</option>
          {courses?.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Turma *</label>
        <select
          value={value.cohortId}
          onChange={(e) => setField('cohortId', e.target.value)}
          disabled={!value.courseId}
          className={`${INPUT_CLASS} disabled:bg-slate-50 disabled:text-slate-400`}
        >
          <option value="">{value.courseId ? 'Selecione...' : 'Escolha um curso primeiro'}</option>
          {cohorts.map((co) => (
            <option key={co.id} value={co.id}>{co.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">Estágio *</label>
        <select
          value={value.stage}
          onChange={(e) => setField('stage', e.target.value)}
          className={INPUT_CLASS}
        >
          {OPEN_STAGES.map((s) => (
            <option key={s.id} value={s.id}>{s.id}</option>
          ))}
        </select>
      </div>
    </>
  )
}

export default memo(FunilPlacementFields)
