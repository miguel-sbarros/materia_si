import { memo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  GraduationCap, Clock, BookOpen, Layers, Banknote, MapPin,
} from 'lucide-react'
import { getCourses, getCourseEmenta } from '../lib/api.js'

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

const CourseCard = memo(function CourseCard({ course }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['ementa', course.id],
    queryFn: () => getCourseEmenta(course.id),
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
          <span className="text-xs font-bold text-slate-400">
            {activeCohorts} turma{activeCohorts !== 1 ? 's' : ''} ativa{activeCohorts !== 1 ? 's' : ''}
          </span>
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
      {cohorts.length > 0 && (
        <div className="px-6 py-4 border-b border-slate-50">
          <div className="flex items-center gap-2 mb-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <MapPin size={12} />
            Turmas
          </div>
          <div className="flex flex-wrap gap-2">
            {cohorts.map(co => (
              <span
                key={co.id}
                className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg ${STATUS_COLORS[co.status] ?? 'bg-slate-50 text-slate-600 border border-slate-200'}`}
                title={STATUS_LABELS[co.status] ?? co.status}
              >
                {co.name}
                {co.price_per_slot != null && (
                  <span className="font-normal opacity-70">· {fmtBRL(co.price_per_slot)}</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

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
    </section>
  )
})

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Cursos() {
  const { data: courses = [], isLoading, isError } = useQuery({
    queryKey: ['courses'],
    queryFn: getCourses,
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
        <button className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-semibold hover:bg-[#1D4ED8] transition-colors flex items-center gap-2 shadow-sm">
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
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  )
}
