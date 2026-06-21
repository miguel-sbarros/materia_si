import { Plus, MessageSquare } from 'lucide-react'
import { relativeTime } from '../../lib/api.js'

// Sidebar in-page do Copiloto: lista as sessões persistidas (mais recentes primeiro),
// destaca a sessão ativa e oferece "+ Nova conversa". Clicar numa linha abre a sessão.
export default function SessionSidebar({ sessions, currentSessionId, onOpen, onNew }) {
  return (
    <aside className="flex-none w-64 flex flex-col border-r border-slate-100 pr-3 mr-4 h-full">
      <button
        type="button"
        onClick={onNew}
        className="flex-none flex items-center gap-1.5 text-[13px] font-semibold text-slate-700 bg-white border border-slate-200 rounded-[10px] px-3 py-2 hover:bg-slate-50 mb-3"
      >
        <Plus size={14} />
        Nova conversa
      </button>

      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-1">
        {sessions.length === 0 ? (
          <div className="text-xs text-slate-400 px-2 py-3">Nenhuma conversa ainda</div>
        ) : (
          sessions.map((s) => {
            const active = s.id === currentSessionId
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onOpen(s.id)}
                className={`text-left rounded-[10px] px-2.5 py-2 transition-colors ${
                  active ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <MessageSquare
                    size={12}
                    className={active ? 'text-[#2563EB] shrink-0' : 'text-slate-400 shrink-0'}
                  />
                  <span className="text-[13px] font-semibold text-slate-900 truncate">
                    {s.title || 'Nova conversa'}
                  </span>
                </div>
                {s.lastSnippet && (
                  <div className="text-[11px] text-slate-400 truncate mt-0.5 pl-[18px]">
                    {s.lastSnippet}
                  </div>
                )}
                <div className="text-[10px] text-slate-300 mt-0.5 pl-[18px]">
                  {relativeTime(s.updatedAt)}
                </div>
              </button>
            )
          })
        )}
      </div>
    </aside>
  )
}
