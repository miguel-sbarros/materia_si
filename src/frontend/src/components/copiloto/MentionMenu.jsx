import { personaMeta } from '../../data/copilot.js'

// Dropdown de menções (@): lista leads para anexar ao contexto do copiloto.
export default function MentionMenu({ results, onPick }) {
  return (
    <div className="absolute bottom-[calc(100%+8px)] left-0 right-0 bg-white border border-slate-200 rounded-2xl shadow-xl p-1.5 max-h-[280px] overflow-auto z-40">
      <div className="px-2.5 pt-1.5 pb-1 text-[11px] font-bold tracking-wide uppercase text-slate-400">
        Anexar lead ao contexto
      </div>
      {results.length === 0 ? (
        <div className="text-xs text-slate-400 p-2.5">Nenhum lead encontrado</div>
      ) : (
        results.map((lead) => {
          const meta = personaMeta(lead.persona)
          return (
            <button
              key={lead.id}
              type="button"
              onClick={() => onPick(lead)}
              className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-left hover:bg-slate-50 transition-colors"
            >
              <span
                className="w-[30px] h-[30px] rounded-full flex items-center justify-center text-[11px] font-bold font-headline shrink-0"
                style={{ background: meta.bg, color: meta.color }}
              >
                {lead.initials}
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-semibold text-slate-900 truncate">{lead.name}</span>
                <span className="block text-[11px] text-slate-400 truncate">
                  {lead.persona} · {lead.stage}
                </span>
              </span>
            </button>
          )
        })
      )}
    </div>
  )
}
