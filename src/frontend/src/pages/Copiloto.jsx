import { Sparkles, Plus } from 'lucide-react'
import useCopilot from '../hooks/useCopilot.js'
import EmptyState from '../components/copiloto/EmptyState.jsx'
import Composer from '../components/copiloto/Composer.jsx'
import MessageList from '../components/copiloto/MessageList.jsx'
import SessionSidebar from '../components/copiloto/SessionSidebar.jsx'
import ConfirmNewSessionModal from '../components/copiloto/ConfirmNewSessionModal.jsx'

// ─── Copiloto — container da página ──────────────────────────────────────────
// Renderiza DENTRO do <Layout> existente (sidebar global + topbar já providos).
// A página tem uma SEGUNDA sidebar in-page (sessões) à esquerda + a coluna de
// conversa à direita. Toda a lógica vive em useCopilot().
export default function Copiloto() {
  const vm = useCopilot()
  const sendDisabled = !vm.attachedLead

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
    <>
    <div className="flex flex-row h-[calc(100vh-7rem)]">
      <SessionSidebar
        sessions={vm.sessions}
        currentSessionId={vm.currentSessionId}
        onOpen={vm.openSession}
        onNew={vm.newChat}
      />

      <div className="flex-1 min-w-0 flex flex-col">
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
              sentKey={vm.sentKey}
              onSendVariant={vm.sendToHistory}
              sendDisabled={sendDisabled}
              scrollRef={vm.scrollRef}
            />

            {/* ── Composer inferior ── */}
            <div className="flex-none pt-4">
              <div className="max-w-[760px] mx-auto">
                {composer}
                <p className="text-center mt-2.5 text-[11px] text-slate-400">
                  As mensagens são sugestões — revise antes de enviar ao histórico do lead.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>

    {vm.pendingLead && (
      <ConfirmNewSessionModal
        leadName={vm.pendingLead.name}
        onConfirm={vm.confirmNewSession}
        onCancel={vm.cancelNewSession}
      />
    )}
    </>
  )
}
