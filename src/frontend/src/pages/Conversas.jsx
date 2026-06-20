import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react'
import {
  Phone,
  MoreVertical,
  Plus,
  Send,
  GraduationCap,
  GitBranch,
  PlusCircle,
  CheckCheck,
} from 'lucide-react'
import { conversations, messages as seedMessages, leads } from '../data/mock.js'

// ─── O(1) lookup maps (js-index-maps) ────────────────────────────────────────
const leadMap = new Map(leads.map((l) => [l.id, l]))

// Deep-clone seed messages into mutable Map so sends persist per session
const buildMessageMap = () =>
  new Map(
    Object.entries(seedMessages).map(([k, v]) => [Number(k), [...v]]),
  )

// ─── Helpers ──────────────────────────────────────────────────────────────────
const initials = (name) =>
  name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

const now = () => {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ─── Static mock data for right panel ────────────────────────────────────────
const LEAD_NOTES = {
  10: [
    'Interessada em trilhas de simulação clínica. Precisa de esclarecimentos sobre planos de pagamento até sexta-feira.',
    'Indicada pelo Dr. Aris. Lead com alta intenção de compra.',
  ],
  11: ['Confirmou inscrição. Aguardando documentação complementar.'],
  12: ['Perguntou sobre próxima turma. Enviar calendário assim que disponível.'],
  4:  ['Solicitou documentação sobre certificação do conselho.'],
}

const LEAD_ACTIVITY = {
  10: [
    { label: 'WhatsApp Recebido',  time: '12:46 Hoje',   active: true  },
    { label: 'E-mail Aberto',      time: '09:12 Hoje',   active: false },
    { label: 'Lead Criado',        time: '08:00 Ontem',  active: false },
  ],
  11: [
    { label: 'E-mail Recebido',    time: '10:12 Hoje',   active: true  },
    { label: 'Inscrição Confirmada', time: '09:45 Hoje', active: false },
  ],
  12: [
    { label: 'WhatsApp Recebido',  time: 'Ontem',        active: true  },
  ],
  4:  [
    { label: 'E-mail Recebido',    time: '24 Out',       active: true  },
  ],
}

// ─── Sub-components (rerender-no-inline-components) ──────────────────────────

const ChannelDot = memo(function ChannelDot({ channel }) {
  return channel === 'WhatsApp' ? (
    <div className="flex items-center gap-1.5 mt-2">
      <div className="w-3 h-3 rounded-full bg-emerald-500 flex items-center justify-center">
        <span className="text-white font-bold" style={{ fontSize: 7 }}>W</span>
      </div>
      <span className="text-[10px] font-bold text-slate-400 uppercase">WhatsApp</span>
    </div>
  ) : (
    <div className="flex items-center gap-1.5 mt-2">
      <div className="w-3 h-3 rounded-full bg-blue-500" />
      <span className="text-[10px] font-bold text-slate-400 uppercase">E-mail</span>
    </div>
  )
})

const ConversationItem = memo(function ConversationItem({ conv, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl transition-colors ${
        isActive
          ? 'bg-white border-l-4 border-blue-600 shadow-sm'
          : 'border-l-4 border-transparent hover:bg-white/60'
      }`}
    >
      <div className="flex justify-between items-start mb-1 gap-2">
        <span className={`text-xs font-bold truncate ${isActive ? 'text-blue-700' : 'text-slate-800'}`}>
          {conv.name}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          {conv.unread > 0 ? (
            <span className="w-4 h-4 bg-blue-600 rounded-full text-white flex items-center justify-center font-bold" style={{ fontSize: 9 }}>
              {conv.unread}
            </span>
          ) : null}
          <span className="text-[10px] text-slate-400">{conv.timestamp}</span>
        </div>
      </div>
      <p className="text-xs text-slate-500 line-clamp-1 leading-relaxed">{conv.lastMessage}</p>
      <ChannelDot channel={conv.channel} />
    </button>
  )
})

const MessageBubble = memo(function MessageBubble({ msg, leadInitials }) {
  return msg.sent ? (
    <div className="flex gap-3 max-w-2xl ml-auto flex-row-reverse">
      <div className="w-8 h-8 rounded-full bg-blue-600 shrink-0 mt-1 flex items-center justify-center text-white text-[10px] font-bold">
        AC
      </div>
      <div className="space-y-1 text-right">
        <div className="p-4 bg-[#2563EB] text-white rounded-2xl rounded-tr-none shadow-sm shadow-blue-100">
          <p className="text-sm leading-relaxed">{msg.text}</p>
        </div>
        <div className="flex items-center justify-end gap-1">
          <span className="text-[10px] text-slate-400">
            {msg.timestamp} • {msg.read ? 'Lida' : 'Enviada'}
          </span>
          <CheckCheck
            size={13}
            className={msg.read ? 'text-blue-500' : 'text-slate-300'}
          />
        </div>
      </div>
    </div>
  ) : (
    <div className="flex gap-3 max-w-2xl">
      <div className="w-8 h-8 rounded-full bg-slate-200 shrink-0 mt-1 flex items-center justify-center text-slate-600 text-[10px] font-bold">
        {leadInitials}
      </div>
      <div className="space-y-1">
        <div className="p-4 bg-slate-100 rounded-2xl rounded-tl-none">
          <p className="text-sm leading-relaxed text-slate-900">{msg.text}</p>
        </div>
        <span className="text-[10px] text-slate-400">
          {msg.timestamp} • {msg.channel}
        </span>
      </div>
    </div>
  )
})

const ActivityTimeline = memo(function ActivityTimeline({ items }) {
  return (
    <div className="space-y-4 relative before:content-[''] before:absolute before:left-[9px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
      {items.map((item, i) => (
        <div key={i} className="flex gap-3 relative">
          <div
            className={`w-5 h-5 rounded-full border-4 z-10 shrink-0 ${
              item.active ? 'border-blue-600 bg-white' : 'border-slate-200 bg-white'
            }`}
          />
          <div>
            <p className={`text-xs font-bold ${item.active ? 'text-slate-900' : 'text-slate-400'}`}>
              {item.label}
            </p>
            <p className="text-[10px] text-slate-400">{item.time}</p>
          </div>
        </div>
      ))}
    </div>
  )
})

// ─── Conversas Page ───────────────────────────────────────────────────────────

export default function Conversas() {
  const [activeConvId, setActiveConvId] = useState(conversations[0].id)
  const [filter, setFilter]             = useState('TODOS')
  const [inputText, setInputText]       = useState('')
  const [msgMap, setMsgMap]             = useState(buildMessageMap)

  const messagesEndRef = useRef(null)

  // Derived — no useEffect (rerender-derived-state-no-effect)
  const filteredConvs = useMemo(() => {
    if (filter === 'NÃO LIDOS') return conversations.filter((c) => c.unread > 0)
    if (filter === 'WHATSAPP')  return conversations.filter((c) => c.channel === 'WhatsApp')
    return conversations
  }, [filter])

  const activeConv  = conversations.find((c) => c.id === activeConvId) ?? conversations[0]
  const activeLead  = leadMap.get(activeConv.leadId)
  const chatMsgs    = msgMap.get(activeConv.leadId) ?? []
  const leadInit    = initials(activeConv.name)
  const notes       = LEAD_NOTES[activeConv.leadId]   ?? []
  const activity    = LEAD_ACTIVITY[activeConv.leadId] ?? []

  // Scroll to bottom when conversation changes or new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConvId, chatMsgs.length])

  const handleSelectConv = useCallback((id) => {
    setActiveConvId(id)
    setInputText('')
  }, [])

  const handleFilterChange = useCallback((f) => setFilter(f), [])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text) return
    const leadId = activeConv.leadId
    const newMsg = {
      id: Date.now(),
      text,
      sent: true,
      timestamp: now(),
      channel: activeConv.channel,
      read: false,
    }
    setMsgMap((prev) => {
      const next = new Map(prev)
      next.set(leadId, [...(next.get(leadId) ?? []), newMsg])
      return next
    })
    setInputText('')
  }, [inputText, activeConv])

  const handleKeyDown = useCallback(
    (e) => { if (e.key === 'Enter' && !e.shiftKey) handleSend() },
    [handleSend],
  )

  return (
    // Escape the Layout's p-6 to go full-bleed
    <div className="-mx-6 -my-6 flex h-[calc(100vh-64px)] overflow-hidden">

      {/* ── Left Panel: Lead list ─────────────────────────────────────────── */}
      <section className="w-80 flex flex-col bg-slate-50 border-r border-slate-100 overflow-hidden shrink-0">
        <div className="p-6 pb-4">
          <h2 className="font-headline text-xl font-bold text-slate-900 mb-4">Leads Ativos</h2>
          {/* Filter pills */}
          <div className="flex gap-2">
            {['TODOS', 'NÃO LIDOS', 'WHATSAPP'].map((f) => (
              <button
                key={f}
                onClick={() => handleFilterChange(f)}
                className={`px-3 py-1 text-[10px] font-bold rounded-full uppercase tracking-tighter transition-colors ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 text-slate-500 hover:bg-slate-300'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-3 space-y-1 pb-4">
          {filteredConvs.map((conv) => (
            <ConversationItem
              key={conv.id}
              conv={conv}
              isActive={conv.id === activeConvId}
              onClick={() => handleSelectConv(conv.id)}
            />
          ))}
        </div>
      </section>

      {/* ── Center Panel: Chat thread ─────────────────────────────────────── */}
      <section className="flex-1 flex flex-col bg-slate-50/50 overflow-hidden">
        {/* Chat header */}
        <div className="h-16 px-6 flex items-center justify-between bg-white/80 backdrop-blur-md border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-700 text-sm">
              {leadInit}
            </div>
            <div>
              <h3 className="font-headline text-sm font-bold text-slate-900">{activeConv.name}</h3>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-[10px] text-slate-500">
                  Online • respondendo via {activeConv.channel}
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-1">
            <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500">
              <Phone size={16} />
            </button>
            <button className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500">
              <MoreVertical size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="flex justify-center">
            <span className="px-4 py-1 bg-slate-100 text-[10px] font-bold text-slate-400 rounded-full uppercase tracking-widest">
              Hoje
            </span>
          </div>
          {chatMsgs.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} leadInitials={leadInit} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="p-4 bg-white border-t border-slate-100 shrink-0">
          <div className="flex items-center gap-3 bg-slate-100 rounded-2xl px-4 py-2">
            <button className="text-slate-400 hover:text-blue-600 transition-colors">
              <Plus size={18} />
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite uma mensagem..."
              className="flex-1 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
            />
            <button
              onClick={handleSend}
              className="text-blue-600 hover:text-blue-700 hover:scale-110 transition-all"
            >
              <Send size={17} />
            </button>
          </div>
        </div>
      </section>

      {/* ── Right Panel: Lead context ─────────────────────────────────────── */}
      <aside className="w-80 bg-white border-l border-slate-100 flex flex-col overflow-hidden shrink-0">
        {/* Avatar + name + actions */}
        <div className="p-6 text-center border-b border-slate-100">
          <div className="w-20 h-20 rounded-3xl bg-blue-50 mx-auto mb-4 flex items-center justify-center text-blue-600 font-bold text-2xl relative">
            {leadInit}
            <span className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 border-4 border-white rounded-full" />
          </div>
          <h2 className="font-headline text-base font-bold text-slate-900">{activeConv.name}</h2>
          <p className="text-xs text-slate-400 mb-4">
            {activeLead ? activeLead.course : 'Lead'}
          </p>
          <div className="flex gap-2 justify-center">
            <button className="px-4 py-1.5 bg-blue-50 text-blue-700 text-[10px] font-bold rounded-lg uppercase hover:bg-blue-100 transition-colors">
              Perfil
            </button>
            <button className="px-4 py-1.5 bg-slate-100 text-slate-600 text-[10px] font-bold rounded-lg uppercase hover:bg-slate-200 transition-colors">
              Matricular
            </button>
          </div>
        </div>

        {/* Scrollable detail sections */}
        <div className="flex-1 overflow-y-auto p-6 space-y-7">
          {/* Curso de interesse */}
          <div className="flex items-start gap-3">
            <GraduationCap size={18} className="text-blue-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-0.5">
                Curso de Interesse
              </p>
              <p className="text-sm font-semibold text-slate-900">
                {activeLead ? activeLead.course : '—'}
              </p>
            </div>
          </div>

          {/* Estágio no funil */}
          <div className="flex items-start gap-3">
            <GitBranch size={18} className="text-blue-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-1">
                Estágio no Funil
              </p>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-bold rounded">
                  {activeLead ? activeLead.stage : 'Novo'}
                </span>
                <span className="text-[10px] text-slate-400">80% Prob.</span>
              </div>
            </div>
          </div>

          {/* Notas rápidas */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Notas Rápidas
              </h4>
              <button className="text-blue-600 hover:text-blue-700 transition-colors">
                <PlusCircle size={16} />
              </button>
            </div>
            <div className="space-y-2">
              {notes.length > 0 ? notes.map((note, i) => (
                <div
                  key={i}
                  className="p-3 bg-slate-50 rounded-xl text-xs leading-relaxed text-slate-500 italic"
                >
                  "{note}"
                </div>
              )) : (
                <p className="text-xs text-slate-400 italic">Nenhuma nota ainda.</p>
              )}
            </div>
          </div>

          {/* Atividade recente */}
          <div>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
              Atividade Recente
            </h4>
            <ActivityTimeline items={activity} />
          </div>
        </div>
      </aside>
    </div>
  )
}
