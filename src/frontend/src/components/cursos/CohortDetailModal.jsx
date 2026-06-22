import { memo, useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, Users, UserPlus, UserMinus } from 'lucide-react'
import { getCohortEnrollments, enrollLead, cancelEnrollment } from '../../lib/api.js'
import EnrollmentModal from './EnrollmentModal.jsx'
import EmentaEditor from './EmentaEditor.jsx'

function initials(name) {
  return (name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

// Barra de vagas: matriculados / capacidade (verde→âmbar→vermelho conforme lota).
const VagasBar = memo(function VagasBar({ enrolled, capacity }) {
  const hasCap = capacity != null
  const pct = hasCap && capacity > 0 ? Math.min(100, (enrolled / capacity) * 100) : 0
  const color = pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-amber-500' : 'bg-emerald-500'

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600">
          <Users size={14} /> Vagas
        </span>
        <span className="text-xs font-bold text-slate-700">
          {enrolled}
          {hasCap ? ` / ${capacity}` : ''} matriculado{enrolled !== 1 ? 's' : ''}
        </span>
      </div>
      {hasCap ? (
        <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
          <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
        </div>
      ) : (
        <p className="text-[11px] text-slate-400">Sem limite de vagas definido.</p>
      )}
    </div>
  )
})

// Detalhe de uma turma: barra de vagas + lista de matriculados + Matricular + editor de ementa.
function CohortDetailModal({ cohort, courseId, onClose }) {
  const queryClient = useQueryClient()
  const [enrollOpen, setEnrollOpen] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape' && !enrollOpen) onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose, enrollOpen])

  const { data, isLoading, isError } = useQuery({
    queryKey: ['cohortEnrollments', cohort.id],
    queryFn: () => getCohortEnrollments(cohort.id),
  })

  // Após matricular/cancelar: atualiza vagas + reflete o lead no Funil (e contagem de cursos).
  const afterChange = () => {
    queryClient.invalidateQueries({ queryKey: ['cohortEnrollments', cohort.id] })
    queryClient.invalidateQueries({ queryKey: ['deals'] })
    queryClient.invalidateQueries({ queryKey: ['courses'] })
  }

  const enrollMut = useMutation({
    mutationFn: (leadId) => enrollLead(cohort.id, leadId),
    onSuccess: () => {
      afterChange()
      setEnrollOpen(false)
    },
  })
  const cancelMut = useMutation({
    mutationFn: (leadId) => cancelEnrollment(cohort.id, leadId),
    onSuccess: afterChange,
  })

  const enrollments = data?.enrollments ?? []

  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[88vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between p-6 border-b border-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-900 font-headline">{cohort.name}</h2>
            <p className="text-xs text-slate-500 mt-0.5">Matrículas e ementa da turma</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Vagas + matriculados */}
          <section>
            {isLoading ? (
              <p className="text-sm text-slate-400">Carregando matrículas...</p>
            ) : isError ? (
              <p className="text-sm text-red-600">Não foi possível carregar as matrículas.</p>
            ) : (
              <>
                <VagasBar enrolled={data.enrolled} capacity={data.capacity} />

                <div className="flex items-center justify-between mt-5 mb-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Matriculados
                  </span>
                  <button
                    onClick={() => setEnrollOpen(true)}
                    disabled={data.available != null && data.available <= 0}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-white bg-[#2563EB] px-3 py-1.5 rounded-lg hover:bg-[#1D4ED8] transition-colors disabled:opacity-50"
                    title={
                      data.available != null && data.available <= 0
                        ? 'Turma lotada'
                        : 'Matricular um lead'
                    }
                  >
                    <UserPlus size={13} /> Matricular
                  </button>
                </div>

                {enrollments.length === 0 ? (
                  <p className="text-sm text-slate-400">Nenhum lead matriculado ainda.</p>
                ) : (
                  <div className="space-y-1.5">
                    {enrollments.map((e) => (
                      <div
                        key={e.id}
                        className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2"
                      >
                        <span className="flex items-center gap-2.5 min-w-0">
                          <span className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold flex items-center justify-center shrink-0">
                            {initials(e.leadName)}
                          </span>
                          <span className="text-sm font-semibold text-slate-800 truncate">
                            {e.leadName}
                          </span>
                        </span>
                        <button
                          onClick={() => cancelMut.mutate(e.leadId)}
                          disabled={cancelMut.isPending}
                          title="Cancelar matrícula"
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-red-600 transition-colors disabled:opacity-50"
                        >
                          <UserMinus size={13} /> Cancelar
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {cancelMut.error ? (
                  <p className="mt-2 text-xs font-semibold text-red-600">{cancelMut.error.message}</p>
                ) : null}
              </>
            )}
          </section>

          {/* Ementa / módulos */}
          <section className="border-t border-slate-50 pt-6">
            <EmentaEditor courseId={courseId} />
          </section>
        </div>
      </div>

      {enrollOpen ? (
        <EnrollmentModal
          cohortName={cohort.name}
          onCancel={() => setEnrollOpen(false)}
          onConfirm={(leadId) => enrollMut.mutate(leadId)}
          submitting={enrollMut.isPending}
          error={enrollMut.error ? enrollMut.error.message : null}
        />
      ) : null}
    </div>
  )
}

export default memo(CohortDetailModal)
