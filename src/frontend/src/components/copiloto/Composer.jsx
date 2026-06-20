import { ArrowUp } from 'lucide-react'
import CommandMenu from './CommandMenu.jsx'
import MentionMenu from './MentionMenu.jsx'
import LeadContextChip from './LeadContextChip.jsx'

// Caixa de composição do copiloto: menus de comando/menção flutuando acima do
// input, chip do lead anexado e o campo de texto com botão de envio.
export default function Composer({
  input,
  onInputChange,
  onKeyDown,
  onSend,
  placeholder,
  attachedLead,
  leadExpanded,
  onToggleLead,
  onRemoveLead,
  showMentions,
  mentionResults,
  onPickLead,
  slashOpen,
  slashResults,
  onRunSlash,
  variant,
}) {
  const cardPadding = variant === 'empty' ? 'p-4 pb-3' : 'px-4 pt-3.5 pb-2.5'

  return (
    <div className="relative">
      {(slashOpen || showMentions) && (
        <div className="absolute bottom-full mb-2 left-0 right-0 z-40">
          {slashOpen ? (
            <CommandMenu results={slashResults} onPick={onRunSlash} />
          ) : (
            <MentionMenu results={mentionResults} onPick={onPickLead} />
          )}
        </div>
      )}

      {attachedLead && (
        <div className="mb-2.5">
          <LeadContextChip
            lead={attachedLead}
            expanded={leadExpanded}
            onToggle={onToggleLead}
            onRemove={onRemoveLead}
          />
        </div>
      )}

      <div className={`border border-slate-200 rounded-[18px] bg-white shadow-sm ${cardPadding}`}>
        <textarea
          rows={1}
          value={input}
          onChange={onInputChange}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          style={{ maxHeight: 140 }}
          className="w-full border-none outline-none resize-none text-[15px] text-slate-900 leading-relaxed bg-transparent"
        />
        <div className="flex items-center justify-end mt-2">
          <button
            type="button"
            onClick={onSend}
            className="w-[34px] h-[34px] rounded-[10px] bg-[#2563EB] hover:bg-[#1D4ED8] text-white flex items-center justify-center shadow-md shadow-blue-500/25 transition-colors"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
