import { Sparkles, Plus } from 'lucide-react'
import useCopilot from '../hooks/useCopilot.js'
import EmptyState from '../components/copiloto/EmptyState.jsx'
import Composer from '../components/copiloto/Composer.jsx'
import MessageList from '../components/copiloto/MessageList.jsx'

// ─── Copiloto — container da página ──────────────────────────────────────────
// Renderiza DENTRO do <Layout> existente (sidebar fixa + topbar de 64px já
// providos; a área de conteúdo já tem padding p-6). Toda a lógica vive em
// useCopilot(); aqui só montamos o composer (reusado nos dois estados) e
// alternamos entre o estado vazio e a conversa.
export default function Copiloto() {
  const vm = useCopilot()

  const composer = (
    <Composer
      input={vm.input}
      onInputChange={vm.onInputChange}
      onKeyDown={vm.onKeyDown}
      onSend={vm.onSend}
      placeholder={vm.placeholder}
      attachedLead={vm.attachedLead}
      leadExpanded={vm.leadExpanded}
      onToggleLead={vm.toggleLeadExpanded}
      onRemoveLead={vm.removeLead}
      showMentions={vm.showMentions}
      mentionResults={vm.mentionResults}
      onPickLead={vm.pickLead}
      slashOpen={vm.slashOpen}
      slashResults={vm.slashResults}
      onRunSlash={vm.runSlash}
      variant={vm.isEmpty ? 'empty' : 'bottom'}
    />
  )

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {vm.isEmpty ? (
        <EmptyState userName={vm.userName}>{composer}</EmptyState>
      ) : (
        <>
          {/* ── Header da conversa ── */}
          <div className="flex-none flex items-center justify-between pb-3.5 mb-1 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-[7px] bg-[#2563EB] flex items-center justify-center">
                <Sparkles size={13} className="text-white" />
              </span>
              <span className="font-headline text-sm font-bold text-slate-900">Copiloto MR</span>
            </div>
            <button
              type="button"
              onClick={vm.newChat}
              className="flex items-center gap-1.5 text-[13px] font-semibold text-slate-600 bg-white border border-slate-200 rounded-[10px] px-3 py-1.5 hover:bg-slate-50"
            >
              <Plus size={14} />
              Nova conversa
            </button>
          </div>

          {/* ── Thread de mensagens ── */}
          <MessageList
            messages={vm.messages}
            isTyping={vm.isTyping}
            copiedKey={vm.copiedKey}
            onCopyVariant={vm.copyVariant}
            scrollRef={vm.scrollRef}
          />

          {/* ── Composer inferior ── */}
          <div className="flex-none pt-4">
            <div className="max-w-[760px] mx-auto">
              {composer}
              <p className="text-center mt-2.5 text-[11px] text-slate-400">
                As mensagens são sugestões — copie e ajuste antes de enviar no WhatsApp.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
