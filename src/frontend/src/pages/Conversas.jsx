import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Phone,
  MoreVertical,
  Plus,
  Send,
  GraduationCap,
  Upload,
  CheckCheck,
} from 'lucide-react'
import {
  getConversations,
  getLeadConversation,
  getLeadDetail,
  sendMessage,
  importChat,
  createDeal,
  clockTime,
} from '../lib/api.js'
import { spinLabel } from '../lib/profile.js'
import { personaMeta } from '../data/copilot.js'
import ImportTxtWizard from '../components/conversas/ImportTxtWizard.jsx'
import FunilPlacementModal from '../components/funil/FunilPlacementModal.jsx'

// ─── Helpers ──────────────────────────────────────────────────────────────────
const initials = (name) =>
  (name || '')
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

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
      <span className="text-[10px] font-bold text-slate-400 uppercase">{channel}</span>
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
          {conv.unread ? (
            <span className="w-2 h-2 bg-blue-600 rounded-full" />
          ) : null}
          <span className="text-[10px] text-slate-400">{clockTime(conv.lastMessageAt)}</span>
        </div>
      </div>
      <p className="text-xs text-slate-500 line-clamp-1 leading-relaxed">
        {conv.lastMessage ?? '—'}
      </p>
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
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
        </div>
        <div className="flex items-center justify-end gap-1">
          <span className="text-[10px] text-slate-400">
            {clockTime(msg.sentAt)} • {msg.read ? 'Lida' : 'Enviada'}
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
          <p className="text-sm leading-relaxed text-slate-900 whitespace-pre-wrap">{msg.text}</p>
        </div>
        <span className="text-[10px] text-slate-400">{clockTime(msg.sentAt)}</span>
      </div>
    </div>
  )
})

// ─── Conversas Page ───────────────────────────────────────────────────────────

export default function Conversas() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [activeLeadId, setActiveLeadId] = useState(null)
  const [filter, setFilter] = useState('TODOS')
  const [inputText, setInputText] = useState('')
  const [wizardFile, setWizardFile] = useState(null) // .txt aguardando vínculo a um lead
  const [placementLead, setPlacementLead] = useState(null) // { id, name } p/ posicionar no Funil (.zip)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  const { data: convs = [] } = useQuery({
    queryKey: ['conversations'],
    queryFn: getConversations,
  })

  // Seleção inicial: primeira conversa quando a lista carrega.
  const effectiveLeadId =
    activeLeadId ?? (convs.length > 0 ? convs[0].leadId : null)

  const { data: thread } = useQuery({
    queryKey: ['conversation', effectiveLeadId],
    queryFn: () => getLeadConversation(effectiveLeadId),
    enabled: effectiveLeadId != null,
  })

  const chatMsgs = thread?.messages ?? []

  // Perfil de IA (P3) do lead ativo — alimenta o painel direito.
  const { data: leadDetail } = useQuery({
    queryKey: ['leadDetail', effectiveLeadId],
    queryFn: () => getLeadDetail(effectiveLeadId),
    enabled: effectiveLeadId != null,
  })
  const profile = leadDetail?.profile ?? null

  const filteredConvs = useMemo(() => {
    if (filter === 'NÃO LIDOS') return convs.filter((c) => c.unread)
    if (filter === 'WHATSAPP') return convs.filter((c) => c.channel === 'WhatsApp')
    return convs
  }, [filter, convs])

  const activeConv = convs.find((c) => c.leadId === effectiveLeadId) ?? null
  const activeName = activeConv?.name ?? ''
  const leadInit = initials(activeName)

  const sendMut = useMutation({
    mutationFn: (text) => sendMessage(effectiveLeadId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', effectiveLeadId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  // Posiciona um lead recém-criado no Funil (turma + estágio aberto) → cria o deal.
  const placeOnFunil = useCallback(
    (leadId, placement) => {
      if (!placement) return
      createDeal(leadId, placement)
        .then(() => {
          queryClient.invalidateQueries({ queryKey: ['deals'] })
          queryClient.invalidateQueries({ queryKey: ['leadDetail', leadId] })
        })
        .catch((err) => window.alert(`Falha ao posicionar no Funil: ${err.message}`))
    },
    [queryClient],
  )

  const importMut = useMutation({
    // `placement` (do wizard .txt "novo lead") é repassado para criar o deal após o import.
    mutationFn: ({ file, leadId, leadName }) => importChat(file, { leadId, leadName }),
    onSuccess: (summary, { placement }) => {
      setWizardFile(null)
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (summary?.leadId) {
        setActiveLeadId(summary.leadId)
        queryClient.invalidateQueries({ queryKey: ['conversation', summary.leadId] })
        queryClient.invalidateQueries({ queryKey: ['leadDetail', summary.leadId] })
        if (summary.createdLead && placement) {
          // Fluxo .txt "novo lead": placement já coletado upfront no wizard.
          placeOnFunil(summary.leadId, placement)
        } else if (summary.createdLead) {
          // Fluxo .zip que criou lead: pede o posicionamento agora.
          setPlacementLead({ id: summary.leadId, name: summary.leadName ?? '' })
        }
      }
    },
    onError: (err) => {
      // .zip falha com alert; o wizard (.txt) mostra o erro inline.
      if (!wizardFile) window.alert(`Falha ao importar: ${err.message}`)
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [effectiveLeadId, chatMsgs.length])

  const handleSelectConv = useCallback((leadId) => {
    setActiveLeadId(leadId)
    setInputText('')
  }, [])

  const handleFilterChange = useCallback((f) => setFilter(f), [])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text || effectiveLeadId == null) return
    sendMut.mutate(text)
    setInputText('')
  }, [inputText, effectiveLeadId, sendMut])

  const handleKeyDown = useCallback(
    (e) => { if (e.key === 'Enter' && !e.shiftKey) handleSend() },
    [handleSend],
  )

  const handleImportClick = useCallback(() => fileInputRef.current?.click(), [])
  const handleFileChange = useCallback(
    (e) => {
      const file = e.target.files?.[0]
      // .zip carrega o telefone no nome → importa direto. .txt nu → wizard (vincular lead).
      if (file) {
        if (file.name.toLowerCase().endsWith('.zip')) importMut.mutate({ file })
        else setWizardFile(file)
      }
      e.target.value = '' // permite re-selecionar o mesmo arquivo
    },
    [importMut],
  )

  const handleWizardConfirm = useCallback(
    ({ leadId, leadName, placement }) =>
      importMut.mutate({ file: wizardFile, leadId, leadName, placement }),
    [importMut, wizardFile],
  )

  const handleWizardCancel = useCallback(() => {
    if (!importMut.isPending) setWizardFile(null)
  }, [importMut.isPending])

  // Modal de posicionamento no Funil (fluxo .zip que criou um lead novo).
  const placeMut = useMutation({
    mutationFn: ({ leadId, cohortId, stage }) => createDeal(leadId, { cohortId, stage }),
    onSuccess: (_card, { leadId }) => {
      setPlacementLead(null)
      queryClient.invalidateQueries({ queryKey: ['deals'] })
      queryClient.invalidateQueries({ queryKey: ['leadDetail', leadId] })
    },
  })

  const handlePlacementConfirm = useCallback(
    ({ cohortId, stage }) =>
      placementLead && placeMut.mutate({ leadId: placementLead.id, cohortId, stage }),
    [placeMut, placementLead],
  )

  const handlePlacementCancel = useCallback(() => {
    // Pular: o lead fica fora do quadro (decisão aceita).
    if (!placeMut.isPending) setPlacementLead(null)
  }, [placeMut.isPending])

  return (
    // Escape the Layout's p-6 to go full-bleed
    <div className="-mx-6 -my-6 flex h-[calc(100vh-64px)] overflow-hidden">

      {/* ── Left Panel: Lead list ─────────────────────────────────────────── */}
      <section className="w-80 flex flex-col bg-slate-50 border-r border-slate-100 overflow-hidden shrink-0">
        <div className="p-6 pb-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-headline text-xl font-bold text-slate-900">Leads Ativos</h2>
            <button
              onClick={handleImportClick}
              disabled={importMut.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-[10px] font-bold rounded-lg uppercase hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <Upload size={12} />
              {importMut.isPending ? 'Importando…' : 'Importar'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,.txt"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
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
          {filteredConvs.length > 0 ? (
            filteredConvs.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isActive={conv.leadId === effectiveLeadId}
                onClick={() => handleSelectConv(conv.leadId)}
              />
            ))
          ) : (
            <p className="px-3 text-xs text-slate-400 italic">
              Nenhuma conversa. Importe um export do WhatsApp para começar.
            </p>
          )}
        </div>
      </section>

      {/* ── Center Panel: Chat thread ─────────────────────────────────────── */}
      <section className="flex-1 flex flex-col bg-slate-50/50 overflow-hidden">
        {/* Chat header */}
        <div className="h-16 px-6 flex items-center justify-between bg-white/80 backdrop-blur-md border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center font-bold text-blue-700 text-sm">
              {leadInit || '—'}
            </div>
            <div>
              <h3 className="font-headline text-sm font-bold text-slate-900">
                {activeName || 'Selecione uma conversa'}
              </h3>
              {activeConv ? (
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-[10px] text-slate-500">
                    via {activeConv.channel}
                  </span>
                </div>
              ) : null}
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
              disabled={effectiveLeadId == null}
              className="flex-1 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={effectiveLeadId == null || sendMut.isPending}
              className="text-blue-600 hover:text-blue-700 hover:scale-110 transition-all disabled:opacity-50"
            >
              <Send size={17} />
            </button>
          </div>
        </div>
      </section>

      {/* ── Right Panel: Lead context ─────────────────────────────────────── */}
      <aside className="w-80 bg-white border-l border-slate-100 flex flex-col overflow-hidden shrink-0">
        {/* Avatar + name + actions — clicável: abre a página do lead */}
        <button
          type="button"
          onClick={() => effectiveLeadId != null && navigate(`/leadpage/${effectiveLeadId}`)}
          disabled={effectiveLeadId == null}
          className="w-full p-6 text-center border-b border-slate-100 enabled:hover:bg-slate-50 transition-colors disabled:cursor-default"
        >
          <div
            className="w-20 h-20 rounded-3xl mx-auto mb-4 flex items-center justify-center font-bold text-2xl relative"
            style={
              profile?.persona
                ? { background: personaMeta(profile.persona).bg, color: personaMeta(profile.persona).color }
                : { background: '#EFF6FF', color: '#2563EB' }
            }
          >
            {leadInit || '—'}
            {activeConv ? (
              <span className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 border-4 border-white rounded-full" />
            ) : null}
          </div>
          <h2 className="font-headline text-base font-bold text-slate-900">
            {activeName || '—'}
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            {effectiveLeadId != null ? 'Ver perfil do lead' : 'Lead'}
          </p>
        </button>

        {/* Detail sections (perfil completo chega em P3) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-7">
          <div className="flex items-start gap-3">
            <GraduationCap size={18} className="text-blue-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-0.5">
                Canal
              </p>
              <p className="text-sm font-semibold text-slate-900">
                {activeConv?.channel ?? '—'}
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
              Perfil do Lead
            </h4>
            {profile ? (
              <div className="space-y-4">
                {profile.persona ? (
                  <span
                    className="inline-block text-[11px] font-bold px-2 py-0.5 rounded-full"
                    style={{
                      background: personaMeta(profile.persona).bg,
                      color: personaMeta(profile.persona).color,
                    }}
                  >
                    {profile.persona}
                  </span>
                ) : null}
                {profile.summary ? (
                  <p className="text-xs text-slate-500 leading-relaxed">{profile.summary}</p>
                ) : null}
                <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-0.5">
                      Score
                    </p>
                    <p className="text-sm font-semibold text-slate-900">
                      {profile.leadScore != null ? `${profile.leadScore}/100` : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-0.5">
                      Estágio SPIN
                    </p>
                    <p className="text-sm font-semibold text-slate-900">
                      {spinLabel(profile.currentSpinStage)}
                    </p>
                  </div>
                </div>
                {profile.dores?.length ? (
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-1.5">
                      Dores
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {profile.dores.map((d, i) => (
                        <span
                          key={i}
                          className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-red-50 text-red-700"
                        >
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {profile.desejos?.length ? (
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mb-1.5">
                      Desejos
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {profile.desejos.map((d, i) => (
                        <span
                          key={i}
                          className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-700"
                        >
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                <button
                  type="button"
                  onClick={() =>
                    effectiveLeadId != null && navigate(`/leadpage/${effectiveLeadId}`)
                  }
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                >
                  Ver análise completa →
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                Persona, dores e desejos aparecem após importar a conversa (4+ mensagens).
              </p>
            )}
          </div>
        </div>
      </aside>

      {wizardFile ? (
        <ImportTxtWizard
          fileName={wizardFile.name}
          onCancel={handleWizardCancel}
          onConfirm={handleWizardConfirm}
          submitting={importMut.isPending}
          error={importMut.isError ? importMut.error?.message : null}
        />
      ) : null}

      {placementLead ? (
        <FunilPlacementModal
          leadName={placementLead.name}
          onCancel={handlePlacementCancel}
          onConfirm={handlePlacementConfirm}
          submitting={placeMut.isPending}
          error={placeMut.isError ? placeMut.error?.message : null}
        />
      ) : null}
    </div>
  )
}
