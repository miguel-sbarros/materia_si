import { memo, useCallback, useEffect, useMemo, useState } from 'react'
import { X, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getCourses, searchLeads } from '../../lib/api.js'
import FunilPlacementFields from '../funil/FunilPlacementFields.jsx'
import { EMPTY_PLACEMENT, isPlacementValid } from '../funil/constants.js'

const INPUT_CLASS =
  'w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

// Wizard para um _chat.txt nu (sem telefone no nome → sem como inferir o lead).
// O usuário vincula a conversa a um lead existente (busca) ou cria um lead novo
// (nome + posicionamento no Funil: curso → turma + estágio).
function ImportTxtWizard({ fileName, onCancel, onConfirm, submitting, error }) {
  const [mode, setMode] = useState('existing') // 'existing' | 'new'
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [newName, setNewName] = useState('')
  const [placement, setPlacement] = useState(EMPTY_PLACEMENT)
  const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: getCourses })

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onCancel])

  // Busca debounced (250ms). A limpeza acontece no callback do timeout (não síncrono no
  // corpo do effect) — searchLeads resolve [] para termo vazio (mesmo padrão da Topbar).
  useEffect(() => {
    if (mode !== 'existing') return undefined
    const term = query.trim()
    const t = setTimeout(() => {
      searchLeads(term)
        .then(setResults)
        .catch(() => setResults([]))
    }, term ? 250 : 0)
    return () => clearTimeout(t)
  }, [query, mode])

  const canConfirm = useMemo(
    () =>
      mode === 'existing'
        ? selected != null
        : newName.trim().length > 0 && isPlacementValid(placement),
    [mode, selected, newName, placement],
  )

  const handleConfirm = useCallback(
    (e) => {
      e.preventDefault()
      if (!canConfirm || submitting) return
      if (mode === 'existing') onConfirm({ leadId: selected.id })
      else
        onConfirm({
          leadName: newName.trim(),
          placement: { cohortId: Number(placement.cohortId), stage: placement.stage },
        })
    },
    [canConfirm, submitting, mode, selected, newName, placement, onConfirm],
  )

  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900 font-headline">Importar conversa</h2>
          <button onClick={onCancel} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <p className="text-sm text-slate-500 mb-4">
          O arquivo <span className="font-semibold text-slate-700">{fileName}</span> não tem
          telefone no nome. Vincule a conversa a um lead.
        </p>

        {/* Seletor de modo */}
        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => setMode('existing')}
            className={`flex-1 px-3 py-2 text-xs font-bold rounded-lg uppercase tracking-tight transition-colors ${
              mode === 'existing'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            Lead existente
          </button>
          <button
            type="button"
            onClick={() => setMode('new')}
            className={`flex-1 px-3 py-2 text-xs font-bold rounded-lg uppercase tracking-tight transition-colors ${
              mode === 'new'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            Novo lead
          </button>
        </div>

        <form onSubmit={handleConfirm} className="space-y-4">
          {mode === 'existing' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Buscar lead
              </label>
              <div className="relative">
                <Search
                  size={15}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value)
                    setSelected(null)
                  }}
                  placeholder="Nome do lead..."
                  autoFocus
                  className={`${INPUT_CLASS} pl-9`}
                />
              </div>
              {results.length > 0 ? (
                <div className="mt-2 max-h-44 overflow-y-auto rounded-lg border border-slate-100 divide-y divide-slate-50">
                  {results.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setSelected(r)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${
                        selected?.id === r.id ? 'bg-blue-50' : 'hover:bg-slate-50'
                      }`}
                    >
                      <span className="w-7 h-7 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold flex items-center justify-center shrink-0">
                        {r.initials}
                      </span>
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold text-slate-800 truncate">
                          {r.name}
                        </span>
                        <span className="block text-[11px] text-slate-400 truncate">
                          {r.persona || r.stage || 'Sem estágio'}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
              ) : query.trim() ? (
                <p className="mt-2 text-xs text-slate-400 italic">Nenhum lead encontrado.</p>
              ) : null}
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                  Nome do novo lead *
                </label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Nome completo"
                  autoFocus
                  className={INPUT_CLASS}
                />
              </div>
              <FunilPlacementFields
                courses={courses}
                value={placement}
                onChange={setPlacement}
              />
            </>
          )}

          {error ? <p className="text-xs font-semibold text-red-600">{error}</p> : null}

          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={onCancel}
              className="border border-slate-200 text-slate-700 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !canConfirm}
              className="bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8] transition-colors disabled:opacity-50"
            >
              {submitting ? 'Importando…' : 'Importar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default memo(ImportTxtWizard)
