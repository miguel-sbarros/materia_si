import { memo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Pencil, Plus, Trash2, X, Check } from 'lucide-react'
import {
  getCourseModules,
  createCourseModule,
  updateCourseModule,
  deleteCourseModule,
} from '../../lib/api.js'

const INPUT_CLASS =
  'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

const EMPTY_FORM = { title: '', content: '', carga: '' }

// Linha de formulário de módulo (criar ou editar). Salvar exige título.
const ModuleForm = memo(function ModuleForm({ initial, onSave, onCancel, submitting }) {
  const [form, setForm] = useState(initial ?? EMPTY_FORM)
  const change = (e) => setForm((p) => ({ ...p, [e.target.name]: e.target.value }))

  return (
    <div className="rounded-lg border border-slate-200 p-3 space-y-2 bg-slate-50/60">
      <input
        name="title"
        value={form.title}
        onChange={change}
        placeholder="Título do módulo *"
        autoFocus
        className={INPUT_CLASS}
      />
      <textarea
        name="content"
        value={form.content ?? ''}
        onChange={change}
        placeholder="Conteúdo / descrição"
        rows={2}
        className={INPUT_CLASS}
      />
      <input
        name="carga"
        value={form.carga ?? ''}
        onChange={change}
        placeholder="Carga (ex.: 8 horas)"
        className={INPUT_CLASS}
      />
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 px-2.5 py-1.5 rounded-lg hover:bg-slate-100"
        >
          <X size={13} /> Cancelar
        </button>
        <button
          type="button"
          disabled={submitting || !form.title.trim()}
          onClick={() =>
            onSave({
              title: form.title.trim(),
              content: form.content?.trim() || null,
              carga: form.carga?.trim() || null,
            })
          }
          className="inline-flex items-center gap-1 text-xs font-semibold text-white bg-[#2563EB] px-2.5 py-1.5 rounded-lg hover:bg-[#1D4ED8] disabled:opacity-50"
        >
          <Check size={13} /> Salvar
        </button>
      </div>
    </div>
  )
})

// Editor da ementa de um curso: lista de módulos com add/editar/excluir (CRUD no DB).
function EmentaEditor({ courseId }) {
  const queryClient = useQueryClient()
  const { data: modules = [], isLoading } = useQuery({
    queryKey: ['courseModules', courseId],
    queryFn: () => getCourseModules(courseId),
  })

  // null = nenhum form aberto · 'new' = criar · <id> = editar aquele módulo.
  const [editing, setEditing] = useState(null)

  // Salvar/editar/excluir reflete na ementa e agenda re-ingestão no Copiloto (RAG).
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['courseModules', courseId] })
    queryClient.invalidateQueries({ queryKey: ['ementa', courseId] })
  }

  const createMut = useMutation({
    mutationFn: (payload) => createCourseModule(courseId, { ...payload, position: modules.length }),
    onSuccess: () => {
      invalidate()
      setEditing(null)
    },
  })
  const updateMut = useMutation({
    mutationFn: ({ id, payload }) => updateCourseModule(id, payload),
    onSuccess: () => {
      invalidate()
      setEditing(null)
    },
  })
  const deleteMut = useMutation({
    mutationFn: (id) => deleteCourseModule(id),
    onSuccess: invalidate,
  })

  const submitting = createMut.isPending || updateMut.isPending

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-[#2563EB]" />
          <h4 className="font-headline font-bold text-[#0F172A] text-sm uppercase tracking-wide">
            Ementa / Módulos
          </h4>
        </div>
        {editing !== 'new' ? (
          <button
            onClick={() => setEditing('new')}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
          >
            <Plus size={13} /> Adicionar módulo
          </button>
        ) : null}
      </div>

      {editing === 'new' ? (
        <div className="mb-3">
          <ModuleForm
            onSave={(payload) => createMut.mutate(payload)}
            onCancel={() => setEditing(null)}
            submitting={submitting}
          />
        </div>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-slate-400">Carregando módulos...</p>
      ) : modules.length === 0 && editing !== 'new' ? (
        <p className="text-sm text-slate-400">Nenhum módulo cadastrado. Adicione o primeiro.</p>
      ) : (
        <div className="space-y-2">
          {modules.map((m) =>
            editing === m.id ? (
              <ModuleForm
                key={m.id}
                initial={{ title: m.title, content: m.content, carga: m.carga }}
                onSave={(payload) => updateMut.mutate({ id: m.id, payload })}
                onCancel={() => setEditing(null)}
                submitting={submitting}
              />
            ) : (
              <div
                key={m.id}
                className="flex items-start justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="text-sm font-bold text-[#0F172A]">{m.title}</p>
                  {m.content ? (
                    <p className="text-sm text-slate-600 leading-relaxed mt-0.5">{m.content}</p>
                  ) : null}
                  {m.carga ? (
                    <p className="text-[11px] text-slate-400 mt-1">{m.carga}</p>
                  ) : null}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => setEditing(m.id)}
                    title="Editar módulo"
                    className="text-slate-400 hover:text-[#2563EB] transition-colors p-1"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => deleteMut.mutate(m.id)}
                    title="Excluir módulo"
                    className="text-slate-400 hover:text-red-600 transition-colors p-1"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ),
          )}
        </div>
      )}

      {createMut.error || updateMut.error || deleteMut.error ? (
        <p className="mt-2 text-xs font-semibold text-red-600">
          {(createMut.error || updateMut.error || deleteMut.error).message}
        </p>
      ) : null}
    </div>
  )
}

export default memo(EmentaEditor)
