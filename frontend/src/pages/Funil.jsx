import { useState, useCallback, useEffect, memo } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  useDroppable,
} from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Upload, Plus, Clock, Calendar, X, CheckCircle } from 'lucide-react'
import { leads as initialLeads } from '../data/mock.js'

// ─── Constants ────────────────────────────────────────────────────────────────

const COLUMNS = [
  { id: 'Novo',        label: 'NOVO',        dotColor: 'bg-blue-500'    },
  { id: 'Contatado',   label: 'CONTATADO',   dotColor: 'bg-amber-500'   },
  { id: 'Negociando',  label: 'NEGOCIANDO',  dotColor: 'bg-blue-600'    },
  { id: 'Matriculado', label: 'MATRICULADO', dotColor: 'bg-emerald-500' },
  { id: 'Perdido',     label: 'PERDIDO',     dotColor: 'bg-red-400'     },
]

const SOURCE_COLORS = {
  'Instagram':   'bg-blue-50 text-blue-700',
  'Site Direto': 'bg-purple-50 text-purple-700',
  'WhatsApp':    'bg-emerald-50 text-emerald-700',
  'Indicação':   'bg-indigo-50 text-indigo-700',
  'E-mail':      'bg-slate-100 text-slate-600',
}

const SOURCES = ['Instagram', 'WhatsApp', 'Site Direto', 'Indicação', 'E-mail']

const COURSE_OPTIONS = [
  'Implantodontia Avançada',
  'Harmonização Orofacial',
  'Cirurgia Bucomaxilo',
  'Ortodontia Avançada',
  'Especialização Ortodontia',
  'Imersão Resinas Compostas',
  'Dermato-Cirurgia Avançada',
  'Nutrição Pediátrica',
]

// ─── Lead Card ────────────────────────────────────────────────────────────────

const LeadCard = memo(function LeadCard({ lead, isDragging }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: lead.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.35 : 1,
  }

  const isNegociando = lead.stage === 'Negociando'
  const isMatriculado = lead.stage === 'Matriculado'

  if (isMatriculado) {
    return (
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        {...listeners}
        className="bg-emerald-50/40 p-5 rounded-xl shadow-sm border-2 border-dashed border-emerald-100 cursor-grab active:cursor-grabbing"
      >
        <div className="mb-3">
          <CheckCircle size={16} className="text-emerald-500" />
        </div>
        <h4 className="font-bold text-sm text-slate-900 mb-1">{lead.name}</h4>
        <p className="text-xs text-slate-500">{lead.course}</p>
      </div>
    )
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="bg-white p-5 rounded-xl shadow-sm border-b-2 border-transparent hover:border-blue-200 transition-all cursor-grab active:cursor-grabbing group"
    >
      {/* Source badge + priority label */}
      <div className="flex justify-between items-start mb-3">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter ${SOURCE_COLORS[lead.source] ?? 'bg-slate-100 text-slate-600'}`}>
          {lead.source}
        </span>
        {isNegociando ? (
          <span className="text-[10px] font-bold text-blue-600">Prioridade Alta</span>
        ) : null}
      </div>

      {/* Name + course */}
      <h4 className="font-bold text-sm text-slate-900 mb-1">{lead.name}</h4>
      <p className={`text-xs text-slate-500 ${isNegociando ? 'mb-3' : 'mb-4'}`}>{lead.course}</p>

      {isNegociando ? (
        <>
          {/* Progress bar */}
          <div className="h-1 w-full bg-slate-100 rounded-full mb-3 overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full" style={{ width: '75%' }} />
          </div>
          {/* Value + follow-up */}
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-900">
              {lead.value
                ? `R$ ${lead.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                : '—'}
            </span>
            <div className="flex items-center gap-1 text-[10px] text-slate-400">
              <Calendar size={10} />
              Follow-up: {lead.lastContact}
            </div>
          </div>
        </>
      ) : (
        <div className="flex items-center justify-between pt-4 border-t border-slate-50">
          <div className="flex items-center gap-1 text-[10px] text-slate-400">
            <Clock size={10} />
            {lead.lastContact}
          </div>
          <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-500 border-2 border-white">
            {lead.assignee}
          </div>
        </div>
      )}
    </div>
  )
})

// ─── Kanban Column ─────────────────────────────────────────────────────────────

const KanbanColumn = memo(function KanbanColumn({ column, leads, activeId }) {
  const { setNodeRef: setDropRef, isOver } = useDroppable({ id: column.id })
  const isPerdido = column.id === 'Perdido'
  const leadIds = leads.map(l => l.id)

  return (
    <div className="flex-shrink-0 w-80">
      {/* Column header */}
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${column.dotColor}`} />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 font-headline">
            {column.label}
          </h3>
        </div>
        <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
          {String(leads.length).padStart(2, '0')}
        </span>
      </div>

      {/* Drop area */}
      <SortableContext items={leadIds} strategy={verticalListSortingStrategy}>
        <div
          ref={setDropRef}
          className={`space-y-3 min-h-[100px] rounded-xl transition-colors duration-150 ${isOver ? 'bg-blue-50/60' : ''}`}
        >
          {isPerdido && leads.length === 0 ? (
            <div className="bg-slate-50 p-6 rounded-xl border border-dashed border-slate-200 flex flex-col items-center justify-center text-center opacity-60">
              <span className="text-2xl mb-2">🗑️</span>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Área de Arquivo</p>
            </div>
          ) : (
            leads.map(lead => (
              <LeadCard key={lead.id} lead={lead} isDragging={activeId === lead.id} />
            ))
          )}
        </div>
      </SortableContext>

      {/* Add card footer */}
      {!isPerdido ? (
        <button className="mt-3 w-full flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 py-2 px-1 transition-colors">
          <Plus size={13} />
          Adicionar card
        </button>
      ) : null}
    </div>
  )
})

// ─── New Lead Modal ────────────────────────────────────────────────────────────

const EMPTY_FORM = { name: '', email: '', phone: '', source: '', course: '' }

const INPUT_CLASS =
  'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

const NewLeadModal = memo(function NewLeadModal({ onClose, onSave }) {
  const [form, setForm] = useState(EMPTY_FORM)

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const handleChange = useCallback((e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }, [])

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault()
      if (!form.name.trim()) return
      onSave(form)
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
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
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
            <select
              name="source"
              value={form.source}
              onChange={handleChange}
              className={INPUT_CLASS}
            >
              <option value="">Selecione...</option>
              {SOURCES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Curso de Interesse</label>
            <select
              name="course"
              value={form.course}
              onChange={handleChange}
              className={INPUT_CLASS}
            >
              <option value="">Selecione...</option>
              {COURSE_OPTIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

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
              className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8] transition-colors"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
})

// ─── Drag Overlay Card ────────────────────────────────────────────────────────

const OverlayCard = memo(function OverlayCard({ lead }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-lg border border-slate-200 w-72 cursor-grabbing rotate-1">
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-tighter ${SOURCE_COLORS[lead.source] ?? 'bg-slate-100 text-slate-600'}`}>
        {lead.source}
      </span>
      <h4 className="font-bold text-sm text-slate-900 mt-3 mb-1">{lead.name}</h4>
      <p className="text-xs text-slate-500">{lead.course}</p>
    </div>
  )
})

// ─── Funil Page ────────────────────────────────────────────────────────────────

export default function Funil() {
  const [leads, setLeads] = useState(initialLeads)
  const [activeId, setActiveId] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  )

  // Derive column buckets during render — no useEffect
  const columnLeads = COLUMNS.reduce((acc, col) => {
    acc[col.id] = leads.filter((l) => l.stage === col.id)
    return acc
  }, {})

  const activeLead = activeId ? leads.find((l) => l.id === activeId) : null

  const handleDragStart = useCallback(({ active }) => {
    setActiveId(active.id)
  }, [])

  const handleDragEnd = useCallback(({ active, over }) => {
    setActiveId(null)
    if (!over) return

    const activeLeadId = active.id
    const overId = over.id
    const isColumnTarget = COLUMNS.some((c) => c.id === overId)

    setLeads((prev) => {
      const activeLead = prev.find((l) => l.id === activeLeadId)
      if (!activeLead) return prev

      const targetStage = isColumnTarget
        ? overId
        : prev.find((l) => l.id === overId)?.stage

      if (!targetStage) return prev

      if (activeLead.stage === targetStage) {
        // Same column — reorder
        const colLeads = prev.filter((l) => l.stage === targetStage)
        const oldIndex = colLeads.findIndex((l) => l.id === activeLeadId)
        const newIndex = colLeads.findIndex((l) => l.id === overId)
        if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) return prev
        const reordered = arrayMove(colLeads, oldIndex, newIndex)
        return [...prev.filter((l) => l.stage !== targetStage), ...reordered]
      } else {
        // Cross-column move
        return prev.map((l) =>
          l.id === activeLeadId ? { ...l, stage: targetStage } : l,
        )
      }
    })
  }, [])

  const handleDragCancel = useCallback(() => setActiveId(null), [])

  const openModal = useCallback(() => setShowModal(true), [])
  const closeModal = useCallback(() => setShowModal(false), [])

  const handleSaveLead = useCallback(
    (form) => {
      setLeads((prev) => [
        {
          id: Date.now(),
          name: form.name,
          email: form.email,
          phone: form.phone,
          source: form.source || 'Instagram',
          course: form.course || '',
          stage: 'Novo',
          lastContact: 'Agora',
          value: null,
          assignee: 'AC',
        },
        ...prev,
      ])
      closeModal()
    },
    [closeModal],
  )

  return (
    <div className="pb-8">
      {/* Page header */}
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight mb-1 font-headline">
            Funil de Vendas
          </h2>
          <p className="text-sm text-slate-500">
            Gerencie seus leads clínicos e inscrições de alunos.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 font-semibold text-sm rounded-lg hover:bg-slate-50 transition-colors">
            <Upload size={14} />
            Importar Leads
          </button>
          <button
            onClick={openModal}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#2563EB] text-white font-semibold text-sm rounded-lg shadow-sm shadow-blue-200 hover:bg-[#1D4ED8] transition-colors"
          >
            <Plus size={14} />
            Novo Lead
          </button>
        </div>
      </div>

      {/* Kanban board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="flex gap-6 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <KanbanColumn
              key={col.id}
              column={col}
              leads={columnLeads[col.id]}
              activeId={activeId}
            />
          ))}
        </div>

        <DragOverlay dropAnimation={{ duration: 150, easing: 'ease' }}>
          {activeLead ? <OverlayCard lead={activeLead} /> : null}
        </DragOverlay>
      </DndContext>

      {/* New lead modal */}
      {showModal ? <NewLeadModal onClose={closeModal} onSave={handleSaveLead} /> : null}
    </div>
  )
}
