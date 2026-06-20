import { Copy, Check } from 'lucide-react'
import { toneMeta } from '../../data/copilot.js'

// Cartão de uma variante de mensagem sugerida: badge de tom + botão copiar + texto.
export default function DraftCard({ tone, text, copied, onCopy }) {
  const meta = toneMeta(tone)
  return (
    <div className="border border-slate-200 rounded-2xl bg-white overflow-hidden shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-slate-100">
        <span
          className="text-[11px] font-bold px-2.5 py-1 rounded-full"
          style={{ background: meta.bg, color: meta.color }}
        >
          {tone}
        </span>
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
      </div>
      <div className="px-3.5 py-3 text-sm text-slate-900 leading-relaxed whitespace-pre-line">
        {text}
      </div>
    </div>
  )
}
