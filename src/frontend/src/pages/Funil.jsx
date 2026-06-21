import { useState, useCallback, useMemo } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, Plus } from 'lucide-react'
import { getDeals, getCourses, createLead, moveDeal } from '../lib/api.js'
import { COLUMNS } from '../components/funil/constants.js'
import KanbanColumn from '../components/funil/KanbanColumn.jsx'
import OverlayCard from '../components/funil/OverlayCard.jsx'
import NewLeadModal from '../components/funil/NewLeadModal.jsx'
import LostReasonModal from '../components/funil/LostReasonModal.jsx'
import CloseDropZone from '../components/funil/CloseDropZone.jsx'

export default function Funil() {
  const queryClient = useQueryClient()
  const [courseId, setCourseId] = useState('') // '' = todos os cursos
  const [cohortId, setCohortId] = useState('') // '' = todas as turmas
  const [activeId, setActiveId] = useState(null)
  const [showNewLead, setShowNewLead] = useState(false)
  const [pendingLost, setPendingLost] = useState(null) // card aguardando motivo da perda

  const dealsKey = useMemo(
    () => ['deals', courseId || null, cohortId || null],
    [courseId, cohortId],
  )

  const {
    data: cards = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: dealsKey,
    queryFn: () =>
      getDeals({
        courseId: courseId ? Number(courseId) : undefined,
        cohortId: cohortId ? Number(cohortId) : undefined,
      }),
  })

  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: getCourses })

  // Turmas do curso selecionado (ou todas as turmas quando nenhum curso está filtrado).
  const cohortOptions = useMemo(() => {
    if (courseId) {
      const c = courses.find((co) => String(co.id) === String(courseId))
      return c?.cohorts ?? []
    }
    return courses.flatMap((co) => co.cohorts ?? [])
  }, [courses, courseId])

  const moveMutation = useMutation({
    mutationFn: ({ dealId, column, lostReason }) => moveDeal(dealId, { column, lostReason }),
    onMutate: async ({ dealId, column }) => {
      await queryClient.cancelQueries({ queryKey: dealsKey })
      const prev = queryClient.getQueryData(dealsKey)
      queryClient.setQueryData(dealsKey, (old = []) =>
        old.map((c) => (c.id === dealId ? { ...c, column } : c)),
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(dealsKey, ctx.prev)
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: dealsKey }),
  })

  const createMutation = useMutation({
    mutationFn: createLead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] })
      setShowNewLead(false)
    },
  })

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const columnCards = useMemo(
    () =>
      COLUMNS.reduce((acc, col) => {
        acc[col.id] = cards.filter((c) => c.column === col.id)
        return acc
      }, {}),
    [cards],
  )

  const activeCard = activeId ? cards.find((c) => c.id === activeId) : null

  const handleDragStart = useCallback(({ active }) => setActiveId(active.id), [])
  const handleDragCancel = useCallback(() => setActiveId(null), [])

  const handleDragEnd = useCallback(
    ({ active, over }) => {
      setActiveId(null)
      if (!over) return

      const card = cards.find((c) => c.id === active.id)
      if (!card) return

      // Close drop-zone: fecha o deal (sai do quadro, pois passa a won/lost).
      if (over.id === 'close-matriculado') {
        moveMutation.mutate({ dealId: card.id, column: 'Matriculado' })
        return
      }
      if (over.id === 'close-perdido') {
        setPendingLost(card) // pede o motivo antes de transicionar para lost
        return
      }

      // Coluna alvo: id de coluna, ou a coluna do card sob o cursor.
      const isColumnTarget = COLUMNS.some((c) => c.id === over.id)
      const targetColumn = isColumnTarget
        ? over.id
        : cards.find((c) => c.id === over.id)?.column
      // Mesma coluna ou alvo inválido: ordem dentro da coluna não é persistida (sem grão).
      if (!targetColumn || targetColumn === card.column) return

      moveMutation.mutate({ dealId: card.id, column: targetColumn })
    },
    [cards, moveMutation],
  )

  const confirmLost = useCallback(
    (reason) => {
      moveMutation.mutate(
        { dealId: pendingLost.id, column: 'Perdido', lostReason: reason },
        { onSettled: () => setPendingLost(null) },
      )
    },
    [pendingLost, moveMutation],
  )

  const openNewLead = useCallback(() => {
    createMutation.reset()
    setShowNewLead(true)
  }, [createMutation])

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
          <select
            value={courseId}
            onChange={(e) => {
              setCourseId(e.target.value)
              setCohortId('') // turma pertence ao curso → reseta ao trocar de curso
            }}
            className="px-4 py-2.5 border border-slate-200 text-slate-700 font-semibold text-sm rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos os cursos</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select
            value={cohortId}
            onChange={(e) => setCohortId(e.target.value)}
            className="px-4 py-2.5 border border-slate-200 text-slate-700 font-semibold text-sm rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas as turmas</option>
            {cohortOptions.map((co) => (
              <option key={co.id} value={co.id}>{co.name}</option>
            ))}
          </select>
          <button className="flex items-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 font-semibold text-sm rounded-lg hover:bg-slate-50 transition-colors">
            <Upload size={14} />
            Importar Leads
          </button>
          <button
            onClick={openNewLead}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#2563EB] text-white font-semibold text-sm rounded-lg shadow-sm shadow-blue-200 hover:bg-[#1D4ED8] transition-colors"
          >
            <Plus size={14} />
            Novo Lead
          </button>
        </div>
      </div>

      {/* Board states */}
      {isError ? (
        <p className="text-sm text-red-600">Não foi possível carregar o funil. Verifique o backend.</p>
      ) : isLoading ? (
        <p className="text-sm text-slate-400">Carregando funil...</p>
      ) : (
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
                cards={columnCards[col.id]}
                activeId={activeId}
              />
            ))}
          </div>

          <CloseDropZone active={activeId != null} />

          <DragOverlay dropAnimation={{ duration: 150, easing: 'ease' }}>
            {activeCard ? <OverlayCard card={activeCard} /> : null}
          </DragOverlay>
        </DndContext>
      )}

      {/* Modals */}
      {showNewLead ? (
        <NewLeadModal
          courses={courses}
          onClose={() => setShowNewLead(false)}
          onSave={(payload) => createMutation.mutate(payload)}
          submitting={createMutation.isPending}
          error={createMutation.isError ? createMutation.error?.message : null}
        />
      ) : null}

      {pendingLost ? (
        <LostReasonModal
          cardName={pendingLost.name}
          onCancel={() => setPendingLost(null)}
          onConfirm={confirmLost}
          submitting={moveMutation.isPending}
        />
      ) : null}
    </div>
  )
}
