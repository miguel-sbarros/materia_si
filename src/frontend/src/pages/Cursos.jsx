import { memo, useState, useMemo } from 'react'
import {
  Users, Calendar, ChevronLeft, ChevronRight,
  Search, Filter, Download, Trash2, Upload,
  UserPlus, MoreVertical, Clock, MapPin,
  AlertTriangle, GraduationCap, FileText, File, Archive,
} from 'lucide-react'
import { courses, cohort } from '../data/mock.js'

// ─── Constants ────────────────────────────────────────────────────────────────

const MODALITY_COLORS = {
  Presencial: 'bg-blue-50 text-blue-700 border border-blue-100',
  Híbrido:    'bg-purple-50 text-purple-700 border border-purple-100',
  EAD:        'bg-emerald-50 text-emerald-700 border border-emerald-100',
}

const DOC_ICONS = {
  PDF:  { Icon: FileText, iconBg: 'bg-blue-50',   iconColor: 'text-[#2563EB]'  },
  DOCX: { Icon: File,     iconBg: 'bg-amber-50',  iconColor: 'text-amber-600'  },
  ZIP:  { Icon: Archive,  iconBg: 'bg-green-50',  iconColor: 'text-green-600'  },
}

// ─── Course List Components ───────────────────────────────────────────────────

const CourseCard = memo(function CourseCard({ course, onSelect }) {
  return (
    <button
      onClick={() => onSelect(course.id)}
      className="text-left w-full p-6 bg-white rounded-2xl shadow-sm border border-slate-100 hover:shadow-md hover:border-[#2563EB]/20 transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 rounded-xl bg-[#2563EB]/10 flex items-center justify-center">
          <GraduationCap size={20} className="text-[#2563EB]" />
        </div>
        <span className="text-xs font-bold text-slate-400">
          {course.activeCohorts} turma{course.activeCohorts !== 1 ? 's' : ''} ativa{course.activeCohorts !== 1 ? 's' : ''}
        </span>
      </div>
      <h3 className="font-headline font-bold text-[#0F172A] text-base mb-2 group-hover:text-[#2563EB] transition-colors leading-snug">
        {course.name}
      </h3>
      <p className="text-sm text-slate-500 mb-4 leading-relaxed">{course.description}</p>
      <div className="flex flex-wrap gap-2">
        {course.modalities.map(m => (
          <span
            key={m}
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${MODALITY_COLORS[m] ?? 'bg-slate-50 text-slate-600 border border-slate-200'}`}
          >
            {m}
          </span>
        ))}
      </div>
    </button>
  )
})

// ─── Cohort Detail Components ─────────────────────────────────────────────────

const TimelineItem = memo(function TimelineItem({ item, index }) {
  const isEven = index % 2 === 0

  return (
    <div className={`flex items-center gap-8 group ${isEven ? '' : 'md:flex-row-reverse'}`}>
      {/* Side label (desktop only) */}
      <div className={`flex-1 hidden md:block ${isEven ? 'text-right' : 'text-left'}`}>
        <h4 className="text-base font-bold text-[#2563EB]">{item.title}</h4>
      </div>

      {/* Date circle */}
      <div
        className={`relative z-10 w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-lg flex-shrink-0 group-hover:scale-110 transition-transform ${
          item.mandatory ? 'border-4 border-[#2563EB]' : 'border-4 border-slate-200'
        }`}
      >
        <span className="text-xs font-bold text-slate-700">{item.date}</span>
      </div>

      {/* Content block */}
      <div className="flex-1 p-6 rounded-2xl bg-slate-50 group-hover:bg-white transition-all group-hover:shadow-xl group-hover:shadow-slate-200/50">
        {/* Title visible on mobile */}
        <div className="md:hidden mb-2">
          <h4 className="text-base font-bold text-[#2563EB]">{item.title}</h4>
        </div>

        <div className="flex items-center gap-4 text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
          {item.mandatory ? (
            <span className="flex items-center gap-1 text-red-600">
              <AlertTriangle size={14} />
              PRESENÇA OBRIGATÓRIA
            </span>
          ) : (
            <>
              <span className="flex items-center gap-1">
                <Clock size={14} />
                {item.time}
              </span>
              <span className="flex items-center gap-1">
                <MapPin size={14} />
                {item.location}
              </span>
            </>
          )}
        </div>
        <p className="text-sm leading-relaxed text-slate-600">{item.description}</p>
      </div>
    </div>
  )
})

const DocumentRow = memo(function DocumentRow({ doc }) {
  const { Icon, iconBg, iconColor } = DOC_ICONS[doc.type] ?? DOC_ICONS.PDF
  return (
    <tr className="group border-b border-slate-50 last:border-0">
      <td className="py-4">
        <div className="flex items-center gap-3">
          <span className={`p-2 rounded-lg ${iconBg} ${iconColor}`}>
            <Icon size={18} />
          </span>
          <span className="font-bold text-sm text-[#0F172A]">{doc.name}</span>
        </div>
      </td>
      <td className="py-4 text-sm text-slate-500">{doc.type}</td>
      <td className="py-4 text-sm text-slate-500">{doc.uploadedAt}</td>
      <td className="py-4 text-right">
        <div className="flex items-center justify-end gap-1">
          <button
            className="p-2 hover:bg-blue-50 text-slate-400 hover:text-[#2563EB] rounded-lg transition-colors"
            title="Baixar"
          >
            <Download size={18} />
          </button>
          <button
            className="p-2 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-lg transition-colors"
            title="Excluir"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </td>
    </tr>
  )
})

const StudentCard = memo(function StudentCard({ student }) {
  const initials = student.name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
  const isPago = student.status === 'Pago'

  return (
    <div className="group flex items-center justify-between p-5 rounded-2xl bg-white hover:shadow-lg transition-all border border-transparent hover:border-[#2563EB]/10">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-[#2563EB]/10 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-bold text-[#2563EB]">{initials}</span>
        </div>
        <div>
          <h4 className="font-bold text-[#0F172A] text-sm">{student.name}</h4>
          <p className="text-xs text-slate-500">
            {student.email} • Matriculado em {student.enrolledAt}
          </p>
        </div>
      </div>
      <div className="hidden md:block text-center">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Status</p>
        <span
          className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${
            isPago ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
          }`}
        >
          {isPago ? 'Pago & Ativo' : 'Parcelado'}
        </span>
      </div>
      <div className="hidden lg:block text-center">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Frequência</p>
        <p className="text-sm font-bold text-[#0F172A]">
          {student.attendance}%{' '}
          <span className="text-[10px] font-medium text-slate-400">
            ({student.attendance === 100 ? '0 faltas' : '1 falta'})
          </span>
        </p>
      </div>
      <button className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors">
        <MoreVertical size={18} className="text-slate-400" />
      </button>
    </div>
  )
})

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Cursos() {
  const [selectedCourseId, setSelectedCourseId] = useState(null)
  const [studentSearch, setStudentSearch] = useState('')

  const selectedCourse = selectedCourseId !== null
    ? courses.find(c => c.id === selectedCourseId) ?? null
    : null

  const filteredStudents = useMemo(
    () =>
      cohort.students.filter(s =>
        s.name.toLowerCase().includes(studentSearch.toLowerCase())
      ),
    [studentSearch]
  )

  // ── View 2 — Cohort Detail ────────────────────────────────────────────────
  if (selectedCourse !== null) {
    const m = cohort.metrics
    const enrollPct = Math.round((m.enrolled / m.capacity) * 100)

    return (
      <div className="pb-10">
        {/* Breadcrumb + Header */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-end mb-8 gap-4">
          <div>
            <nav className="flex items-center gap-1.5 text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">
              <button
                onClick={() => setSelectedCourseId(null)}
                className="hover:text-[#2563EB] transition-colors"
              >
                Cursos
              </button>
              <ChevronRight size={14} />
              <span className="text-[#2563EB] truncate max-w-xs">{selectedCourse.name}</span>
            </nav>
            <h1 className="font-headline text-3xl font-extrabold tracking-tight text-[#0F172A]">
              {selectedCourse.name}
            </h1>
          </div>
          <div className="flex gap-3 flex-shrink-0">
            <button className="border border-[#E2E8F0] text-[#0F172A] rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-[#F8FAFC] transition-colors">
              Editar Ementa
            </button>
            <button className="bg-[#2563EB] text-white rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-[#1D4ED8] transition-colors flex items-center gap-2 shadow-lg shadow-[#2563EB]/20">
              <UserPlus size={16} />
              Matricular Aluno
            </button>
          </div>
        </div>

        {/* Bento Stats Grid */}
        <div className="grid grid-cols-12 gap-6 mb-12">
          {/* Matrículas */}
          <div className="col-span-12 lg:col-span-4 p-8 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-slate-500 font-bold text-xs uppercase tracking-widest">
                  Matrículas
                </span>
                <div className="w-8 h-8 rounded-full bg-[#2563EB]/10 text-[#2563EB] flex items-center justify-center">
                  <Users size={16} />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <h3 className="font-headline text-5xl font-extrabold text-[#0F172A] tracking-tighter">
                  {m.enrolled}
                </h3>
                <span className="text-xl font-semibold text-slate-300">/ {m.capacity}</span>
              </div>
            </div>
            <div className="mt-8">
              <div className="flex justify-between text-xs font-bold text-slate-500 mb-2">
                <span>Progresso</span>
                <span className="text-[#2563EB]">{enrollPct}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#2563EB] rounded-full transition-all"
                  style={{ width: `${enrollPct}%` }}
                />
              </div>
            </div>
          </div>

          {/* Período Letivo */}
          <div className="col-span-12 lg:col-span-5 p-8 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <span className="text-slate-500 font-bold text-xs uppercase tracking-widest">
                Período Letivo
              </span>
              <div className="w-8 h-8 rounded-full bg-[#2563EB]/10 text-[#2563EB] flex items-center justify-center">
                <Calendar size={16} />
              </div>
            </div>
            <div className="flex items-center gap-8 flex-1">
              <div className="flex-1">
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">
                  Início
                </p>
                <p className="text-2xl font-bold text-[#0F172A]">{m.startDate}</p>
              </div>
              <div className="h-10 w-px bg-slate-100" />
              <div className="flex-1">
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">
                  Término
                </p>
                <p className="text-2xl font-bold text-[#0F172A]">{m.endDate}</p>
              </div>
            </div>
            <div className="mt-6 flex gap-2 flex-wrap">
              {m.modalities.map(mod => (
                <span
                  key={mod}
                  className="px-3 py-1 bg-slate-50 rounded-lg text-[10px] font-bold text-slate-600 border border-slate-200 uppercase"
                >
                  {mod}
                </span>
              ))}
              <span className="px-3 py-1 bg-blue-50 rounded-lg text-[10px] font-bold text-[#2563EB] border border-[#2563EB]/10 uppercase">
                {cohort.name}
              </span>
            </div>
          </div>

          {/* Investimento */}
          <div className="col-span-12 lg:col-span-3 p-8 rounded-3xl bg-[#2563EB] text-white shadow-xl shadow-[#2563EB]/20 relative overflow-hidden group">
            <div className="absolute -right-8 -top-8 opacity-10 pointer-events-none">
              <Users size={180} />
            </div>
            <div className="relative z-10 flex flex-col h-full">
              <span className="font-bold text-xs uppercase tracking-widest mb-4 opacity-80">
                Investimento
              </span>
              <div className="mb-auto">
                <p className="text-sm opacity-80">Valor por vaga</p>
                <h3 className="font-headline text-3xl font-extrabold tracking-tight">
                  R$ {m.pricePerSlot.toLocaleString('pt-BR')}
                </h3>
              </div>
              <div className="pt-4 border-t border-white/10 mt-6">
                <p className="text-[10px] opacity-70 uppercase font-bold tracking-widest mb-1">
                  Receita Prevista
                </p>
                <p className="text-xl font-bold">
                  R$ {m.projectedRevenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Cronograma */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-headline text-2xl font-bold tracking-tight text-[#0F172A]">
              Cronograma do Curso
            </h2>
            <div className="flex items-center gap-3">
              <button className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                <ChevronLeft size={20} className="text-[#0F172A]" />
              </button>
              <span className="font-bold text-sm uppercase text-[#0F172A]">Maio 2026</span>
              <button className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                <ChevronRight size={20} className="text-[#0F172A]" />
              </button>
            </div>
          </div>
          <div className="relative">
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200 -translate-x-1/2 hidden md:block" />
            <div className="space-y-12 relative">
              {cohort.schedule.map((item, i) => (
                <TimelineItem key={item.id} item={item} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* Documentos */}
        <section className="mb-12 p-8 rounded-3xl bg-white border border-slate-100 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="font-headline text-2xl font-bold tracking-tight text-[#0F172A]">
                Gerenciar Documentos
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Editais, contratos e materiais de apoio centrais do curso
              </p>
            </div>
            <button className="border border-[#E2E8F0] text-[#0F172A] rounded-lg px-4 py-2.5 text-sm font-semibold hover:bg-[#F8FAFC] transition-colors flex items-center gap-2 self-start md:self-auto">
              <Upload size={16} />
              Fazer Upload
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="pb-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Nome do Arquivo
                  </th>
                  <th className="pb-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Tipo
                  </th>
                  <th className="pb-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Data de Upload
                  </th>
                  <th className="pb-4 text-right text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {cohort.documents.map(doc => (
                  <DocumentRow key={doc.id} doc={doc} />
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Alunos Matriculados */}
        <section className="p-8 rounded-3xl bg-slate-50">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="font-headline text-2xl font-bold tracking-tight text-[#0F172A]">
                Alunos Matriculados
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {m.enrolled} perfis ativos para a turma {cohort.name}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                />
                <input
                  type="text"
                  placeholder="Filtrar por nome..."
                  value={studentSearch}
                  onChange={e => setStudentSearch(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-white rounded-lg border border-[#E2E8F0] focus:outline-none focus:ring-2 focus:ring-[#2563EB] text-sm w-56 shadow-sm"
                />
              </div>
              <button className="bg-white p-2 rounded-lg border border-[#E2E8F0] hover:bg-slate-50 transition-colors">
                <Filter size={18} className="text-slate-600" />
              </button>
              <button className="bg-white p-2 rounded-lg border border-[#E2E8F0] hover:bg-slate-50 transition-colors">
                <Download size={18} className="text-slate-600" />
              </button>
            </div>
          </div>
          <div className="space-y-4">
            {filteredStudents.map(student => (
              <StudentCard key={student.id} student={student} />
            ))}
          </div>
          <button className="w-full mt-6 py-4 rounded-xl border-2 border-dashed border-slate-300 text-slate-400 font-bold text-sm hover:border-[#2563EB] hover:text-[#2563EB] transition-all uppercase tracking-widest">
            Ver todos os {m.enrolled} alunos matriculados
          </button>
        </section>
      </div>
    )
  }

  // ── View 1 — Course List ──────────────────────────────────────────────────
  return (
    <div className="pb-10">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-headline text-2xl font-semibold text-[#0F172A]">Cursos Ativos</h1>
          <p className="text-sm text-slate-500 mt-1">Gerencie cursos, turmas e matrículas</p>
        </div>
        <button className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-semibold hover:bg-[#1D4ED8] transition-colors flex items-center gap-2 shadow-sm">
          <GraduationCap size={16} />
          Novo Curso
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {courses.map(course => (
          <CourseCard key={course.id} course={course} onSelect={setSelectedCourseId} />
        ))}
      </div>
    </div>
  )
}
