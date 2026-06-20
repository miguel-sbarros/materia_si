import {
  CalendarRange,
  ListChecks,
  AlertTriangle,
  Users,
  GraduationCap,
  Target,
  Slash,
} from 'lucide-react'

// Ícone por comando slash.
const CMD_ICONS = {
  '/weekly-review': CalendarRange,
  '/today-tasks': ListChecks,
  '/at-risk': AlertTriangle,
  '/personas': Users,
  '/courses': GraduationCap,
  '/spin': Target,
}

// Dropdown de comandos (/): lista os slash-commands do copiloto.
export default function CommandMenu({ results, onPick }) {
  return (
    <div className="absolute bottom-[calc(100%+8px)] left-0 right-0 bg-white border border-slate-200 rounded-2xl shadow-xl p-1.5 max-h-[280px] overflow-auto z-40">
      <div className="px-2.5 pt-1.5 pb-1 text-[11px] font-bold tracking-wide uppercase text-slate-400">
        Comandos
      </div>
      {results.length === 0 ? (
        <div className="text-xs text-slate-400 p-2.5">Nenhum comando encontrado</div>
      ) : (
        results.map((item) => {
          const Icon = CMD_ICONS[item.cmd] || Slash
          return (
            <button
              key={item.cmd}
              type="button"
              onClick={() => onPick(item.cmd)}
              className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-left hover:bg-slate-50 transition-colors"
            >
              <span className="w-[30px] h-[30px] rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <Icon size={15} />
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-semibold text-slate-900 truncate">{item.label}</span>
                <span className="block text-[11px] text-slate-400 truncate">{item.desc}</span>
              </span>
              <span className="text-[11px] text-slate-400 font-mono shrink-0">{item.cmd}</span>
            </button>
          )
        })
      )}
    </div>
  )
}
