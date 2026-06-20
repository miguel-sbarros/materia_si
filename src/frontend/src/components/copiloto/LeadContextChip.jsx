import { Check, ChevronDown, ChevronUp, X } from 'lucide-react'
import { personaMeta, leadAttrs } from '../../data/copilot.js'

// Chip do lead anexado ao contexto: cabeçalho sempre visível + seção expansível
// com atributos, ângulo recomendado e histórico de conversa (bolhas estilo WhatsApp).
export default function LeadContextChip({ lead, expanded, onToggle, onRemove }) {
  const meta = personaMeta(lead.persona)
  return (
    <div className="border border-slate-200 rounded-2xl bg-white overflow-hidden animate-mrfade">
      {/* Cabeçalho */}
      <div className="flex items-center gap-2.5 px-3 py-2.5">
        <span
          className="w-[34px] h-[34px] rounded-full flex items-center justify-center text-xs font-bold font-headline shrink-0"
          style={{ background: meta.bg, color: meta.color }}
        >
          {lead.initials}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-headline text-sm font-bold text-slate-900">{lead.name}</span>
            <span
              className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
              style={{ background: meta.bg, color: meta.color }}
            >
              {lead.persona}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
            <Check size={11} className="text-green-500" />
            Perfil e histórico carregados no contexto
          </div>
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1 rounded-md transition-colors shrink-0"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        <button
          type="button"
          onClick={onRemove}
          className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-1 rounded-md transition-colors shrink-0"
        >
          <X size={16} />
        </button>
      </div>

      {/* Seção expansível */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50 p-3.5 max-h-[300px] overflow-y-auto animate-mrfade">
          <div className="grid grid-cols-2 gap-x-5 gap-y-2.5 mb-3.5">
            {leadAttrs(lead).map((attr) => (
              <div key={attr.label}>
                <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-0.5">
                  {attr.label}
                </div>
                <div className="text-sm text-slate-700 font-medium">{attr.value}</div>
              </div>
            ))}
          </div>

          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-1.5">
            Ângulo recomendado
          </div>
          <div className="text-sm text-slate-600 leading-relaxed mb-3.5">{lead.angle}</div>

          <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-2">
            Histórico de conversa
          </div>
          <div className="flex flex-col gap-1.5">
            {lead.history.map((h, i) =>
              h.fromLead ? (
                <div key={i} className="flex justify-start">
                  <div className="max-w-[78%] bg-white border border-slate-200 text-slate-700 text-[12.5px] leading-relaxed px-2.5 py-1.5 rounded-tl-xl rounded-tr-xl rounded-br-xl">
                    {h.text}
                  </div>
                </div>
              ) : (
                <div key={i} className="flex justify-end">
                  <div
                    className="max-w-[78%] text-[12.5px] leading-relaxed px-2.5 py-1.5 rounded-tl-xl rounded-tr-xl rounded-bl-xl"
                    style={{ background: '#DCF8C6', color: '#1F3D2B' }}
                  >
                    {h.text}
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}
