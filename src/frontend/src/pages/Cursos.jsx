import { memo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  GraduationCap, Clock, BookOpen, Layers, Banknote, MapPin, Pencil, Plus,
} from 'lucide-react'
import {
  getCourses, getCourseEmenta,
  createCourse, updateCourse, createCohort, updateCohort,
} from '../lib/api.js'
import CourseModal from '../components/cursos/CourseModal.jsx'
import CohortModal from '../components/cursos/CohortModal.jsx'

// ─── Helpers ────────────────────────────────────────────────────────────────

const MODALITY_COLORS = {
  Presencial: 'bg-blue-50 text-blue-700 border border-blue-100',
  Híbrido:    'bg-purple-50 text-purple-700 border border-purple-100',
  EAD:        'bg-emerald-50 text-emerald-700 border border-emerald-100',
}

const STATUS_COLORS = {
  open:     'bg-blue-50 text-blue-700 border border-blue-100',
  active:   'bg-emerald-50 text-emerald-700 border border-emerald-100',
  finished: 'bg-slate-100 text-slate-500 border border-slate-200',
}

const STATUS_LABELS = {
  open:     'Inscrições abertas',
  active:   'Em andamento',
  finished: 'Encerrada',
}

// Money chega como string (Decimal, lossless) → número só na formatação.
function fmtBRL(value) {
  if (value == null) return '—'
  return `R$ ${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
}

// ─── Ementa table ─────────────────────────────────────────────────────────────

const EmentaTable = memo(function EmentaTable({ syllabus }) {
  // Coluna "Carga" só aparece se alguma linha a expõe.
  const showCarga = syllabus.some(row => row.carga)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="pb-3 pr-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Módulo / Tema
            </th>
            <th className="pb-3 pr-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Conteúdo
            </th>
            {showCarga && (
              <th className="pb-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap">
                Carga
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {syllabus.map((row, i) => (
            <tr key={i} className="border-b border-slate-50 last:border-0 align-top">
              <td className="py-3 pr-4 text-sm font-bold text-[#0F172A] w-1/3">{row.tema}</td>
              <td className="py-3 pr-4 text-sm text-slate-600 leading-relaxed">{row.conteudo}</td>
              {showCarga && (
                <td className="py-3 text-sm text-slate-500 whitespace-nowrap">{row.carga || '—'}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
})

// ─── Course card (fetches its own ementa) ───────────────────────────────────

const CourseCard = memo(function CourseCard({ course, onEdit }) {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['ementa', course.id],
    queryFn: () => getCourseEmenta(course.id),
  })

  // Modal de turma: `null` fechado · `{}` criar · `{cohort}` editar.
  const [cohortModal, setCohortModal] = useState(null)

  const cohortMutation = useMutation({
    mutationFn: ({ cohort, payload }) =>
      cohort ? updateCohort(cohort.id, payload) : createCohort(course.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] })
      setCohortModal(null)
    },
  })

  const detail = data?.course
  const ementa = data?.ementa ?? null
  const cohorts = course.cohorts ?? []
  const activeCohorts = cohorts.filter(c => c.status !== 'finished').length

  // Preço de exibição: preço do curso, com fallback para a primeira turma.
  const price = detail?.price ?? course.price ?? cohorts.find(c => c.price_per_slot != null)?.price_per_slot

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-50">
        <div className="flex items-start justify-between mb-4">
          <div className="w-10 h-10 rounded-xl bg-[#2563EB]/10 flex items-center justify-center flex-shrink-0">
            <GraduationCap size={20} className="text-[#2563EB]" />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-400">
              {activeCohorts} turma{activeCohorts !== 1 ? 's' : ''} ativa{activeCohorts !== 1 ? 's' : ''}
            </span>
            <button
              onClick={() => onEdit(course)}
              title="Editar curso"
              className="text-slate-400 hover:text-[#2563EB] transition-colors"
            >
              <Pencil size={15} />
            </button>
          </div>
        </div>
        <h3 className="font-headline font-bold text-[#0F172A] text-lg mb-2 leading-snug">
          {course.name}
        </h3>
        {(ementa?.summary || detail?.description) && (
          <p className="text-sm text-slate-500 leading-relaxed">
            {ementa?.summary || detail?.description}
          </p>
        )}

        {/* Meta chips */}
        <div className="flex flex-wrap gap-2 mt-4">
          {detail?.modality && (
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${MODALITY_COLORS[detail.modality] ?? 'bg-slate-50 text-slate-600 border border-slate-200'}`}
            >
              {detail.modality}
            </span>
          )}
          {detail?.duration && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-50 text-slate-600 border border-slate-200 uppercase">
              <Clock size={11} />
              {detail.duration}
            </span>
          )}
          {price != null && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-50 text-slate-600 border border-slate-200 uppercase">
              <Banknote size={11} />
              {fmtBRL(price)}
            </span>
          )}
        </div>
      </div>

      {/* Turmas */}
      <div className="px-6 py-4 border-b border-slate-50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <MapPin size={12} />
            Turmas
          </div>
          <button
            onClick={() => setCohortModal({})}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
          >
            <Plus size={13} />
            Adicionar turma
          </button>
        </div>
        {cohorts.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {cohorts.map(co => (
              <button
                key={co.id}
                onClick={() => setCohortModal({ cohort: co })}
                className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80 ${STATUS_COLORS[co.status] ?? 'bg-slate-50 text-slate-600 border border-slate-200'}`}
                title={`${STATUS_LABELS[co.status] ?? co.status} · clique para editar`}
              >
                {co.name}
                {co.price_per_slot != null && (
                  <span className="font-normal opacity-70">· {fmtBRL(co.price_per_slot)}</span>
                )}
              </button>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400">Nenhuma turma cadastrada.</p>
        )}
      </div>

      {/* Ementa */}
      <div className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen size={16} className="text-[#2563EB]" />
          <h4 className="font-headline font-bold text-[#0F172A] text-sm uppercase tracking-wide">
            Ementa
          </h4>
        </div>

        {isLoading ? (
          <p className="text-sm text-slate-400">Carregando ementa...</p>
        ) : isError ? (
          <p className="text-sm text-red-600">Não foi possível carregar a ementa.</p>
        ) : ementa && ementa.syllabus?.length > 0 ? (
          <EmentaTable syllabus={ementa.syllabus} />
        ) : (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Layers size={16} />
            Ementa em breve.
          </div>
        )}
      </div>

      {cohortModal && (
        <CohortModal
          cohort={cohortModal.cohort}
          courseName={course.name}
          onClose={() => setCohortModal(null)}
          onSave={(payload) => cohortMutation.mutate({ cohort: cohortModal.cohort, payload })}
          submitting={cohortMutation.isPending}
          error={cohortMutation.error ? cohortMutation.error.message : null}
        />
      )}
    </section>
  )
})

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Cursos() {
  const queryClient = useQueryClient()
  const { data: courses = [], isLoading, isError } = useQuery({
    queryKey: ['courses'],
    queryFn: getCourses,
  })

  // Modal de curso: `null` fechado · `{}` criar · `{course}` editar.
  const [courseModal, setCourseModal] = useState(null)

  const courseMutation = useMutation({
    mutationFn: ({ course, payload }) =>
      course ? updateCourse(course.id, payload) : createCourse(payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['courses'] })
      if (variables.course) {
        queryClient.invalidateQueries({ queryKey: ['ementa', variables.course.id] })
      }
      setCourseModal(null)
    },
  })

  return (
    <div className="pb-10">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-headline text-2xl font-semibold text-[#0F172A]">Cursos Ativos</h1>
          <p className="text-sm text-slate-500 mt-1">
            Portfólio de cursos da MR Digital com ementa e turmas
          </p>
        </div>
        <button
          onClick={() => setCourseModal({})}
          className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-semibold hover:bg-[#1D4ED8] transition-colors flex items-center gap-2 shadow-sm"
        >
          <GraduationCap size={16} />
          Novo Curso
        </button>
      </div>

      {isError ? (
        <p className="text-sm text-red-600">
          Não foi possível carregar os cursos. Verifique o backend.
        </p>
      ) : isLoading ? (
        <p className="text-sm text-slate-400">Carregando cursos...</p>
      ) : courses.length === 0 ? (
        <p className="text-sm text-slate-400">Nenhum curso cadastrado ainda.</p>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {courses.map(course => (
            <CourseCard
              key={course.id}
              course={course}
              onEdit={(c) => setCourseModal({ course: c })}
            />
          ))}
        </div>
      )}

      {courseModal && (
        <CourseModal
          course={courseModal.course}
          onClose={() => setCourseModal(null)}
          onSave={(payload) => courseMutation.mutate({ course: courseModal.course, payload })}
          submitting={courseMutation.isPending}
          error={courseMutation.error ? courseMutation.error.message : null}
        />
      )}
    </div>
  )
}
