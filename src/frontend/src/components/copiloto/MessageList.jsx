import { Sparkles, MessageCircle } from 'lucide-react'
import DraftCard from './DraftCard.jsx'
import Markdown from './Markdown.jsx'
import ThinkingIndicator from './ThinkingIndicator.jsx'

// Cabeçalho "Copiloto MR" reutilizado nas mensagens do assistente.
function AssistantHeader() {
  return (
    <div className="flex items-center gap-2 mb-2.5">
      <span className="w-5 h-5 rounded-md bg-[#2563EB] flex items-center justify-center">
        <Sparkles size={11} className="text-white" />
      </span>
      <span className="text-xs font-bold text-slate-500 font-headline">Copiloto MR</span>
    </div>
  )
}

// Lista rolável de mensagens da conversa: bolhas do usuário, respostas em texto
// e blocos de aconselhamento (drafts), além do indicador de digitação.
export default function MessageList({
  messages,
  isTyping,
  copiedKey,
  onCopyVariant,
  sentKey,
  onSendVariant,
  sendDisabled,
  scrollRef,
}) {
  return (
    <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-8 py-7">
      <div className="max-w-[760px] mx-auto flex flex-col gap-6">
        {messages.map((m) => (
          <div key={m.id} className="animate-mrfade">
            {m.role === 'user' && (
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-slate-100 text-slate-900 text-sm leading-relaxed px-4 py-3 rounded-2xl rounded-br-sm whitespace-pre-line">
                  {m.text}
                </div>
              </div>
            )}

            {m.role === 'assistant' && m.kind === 'text' && (
              <div>
                <AssistantHeader />
                <Markdown className="text-sm text-slate-700 leading-relaxed">
                  {m.text}
                </Markdown>
              </div>
            )}

            {m.role === 'assistant' && m.kind === 'drafts' && (
              <div>
                <AssistantHeader />
                <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-1.5">
                  Análise
                </div>
                <Markdown className="text-sm text-slate-700 leading-relaxed mb-5">
                  {m.reasoning}
                </Markdown>
                <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-2.5 flex items-center gap-1.5">
                  <MessageCircle size={12} className="text-green-500" />
                  Caminhos sugeridos
                </div>
                <div className="flex flex-col gap-2.5">
                  {(m.paths || []).map((p, i) => {
                    const key = `${m.id}-${i}`
                    return (
                      <DraftCard
                        key={i}
                        title={p.title}
                        rationale={p.rationale}
                        text={p.message}
                        copied={copiedKey === key}
                        onCopy={() => onCopyVariant(key, p.message)}
                        onSend={() => onSendVariant(key, p.message)}
                        sending={sentKey === `${key}:sending`}
                        sent={sentKey === `${key}:sent`}
                        sendDisabled={sendDisabled}
                      />
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        ))}

        {isTyping && <ThinkingIndicator />}
      </div>
    </div>
  )
}
