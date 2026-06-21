import { Copy, Check, Send } from 'lucide-react'
import Markdown from './Markdown.jsx'

// Estilo neutro do badge de título do path (substitui o badge fixo de tom).
const TITLE_META = { color: '#2563EB', bg: '#EFF6FF' }

// Cartão de um path estratégico sugerido: badge de título dinâmico + rationale +
// mensagem + ações (Copiar / Enviar). Enviar grava no histórico WhatsApp do lead.
export default function DraftCard({
  title,
  rationale,
  text,
  copied,
  onCopy,
  onSend,
  sending,
  sent,
  sendDisabled,
}) {
  return (
    <div className="border border-slate-200 rounded-2xl bg-white overflow-hidden shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
      <div className="flex items-center justify-between gap-2 px-3.5 py-2.5 border-b border-slate-100">
        <span
          className="text-[11px] font-bold px-2.5 py-1 rounded-full truncate"
          style={{ background: TITLE_META.bg, color: TITLE_META.color }}
        >
          {title}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={onCopy}
            className="flex items-center gap-1.5 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
          >
            {copied ? (
              <>
                <Check size={13} className="text-green-500" />
                Copiado
              </>
            ) : (
              <>
                <Copy size={13} />
                Copiar
              </>
            )}
          </button>
          <button
            type="button"
            onClick={onSend}
            disabled={sendDisabled || sending}
            title={sendDisabled ? 'Anexe um lead (@) para enviar ao histórico' : undefined}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold border transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-[#2563EB] text-white border-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-200"
          >
            {sent ? (
              <>
                <Check size={13} />
                Enviado
              </>
            ) : (
              <>
                <Send size={13} />
                {sending ? 'Enviando...' : 'Enviar'}
              </>
            )}
          </button>
        </div>
      </div>
      {rationale && (
        <div className="px-3.5 pt-2.5 text-xs text-slate-400 leading-relaxed">
          {rationale}
        </div>
      )}
      <Markdown className="px-3.5 py-3 text-sm text-slate-900 leading-relaxed">
        {text}
      </Markdown>
    </div>
  )
}
