import { useState, useRef, useEffect, memo } from 'react'
import { Bot, Send, Sparkles, User, BarChart2, Users, AlertTriangle, FileText } from 'lucide-react'
import { coPilotoSeedMessages } from '../data/mock.js'

// ─── Simulated AI responses (baseado no playbook MR Digital) ─────────────────
function getAiResponse(userText) {
  const t = userText.toLowerCase()

  if (t.includes('elena')) {
    return 'Elena Rodriguez — perfil Recém-Especializada (33% de conversão, ciclo curto). Argumento central: segurança via GPS cirúrgico.\n\nMensagem sugerida: "Olá, Elena! Para a Especialização (24 meses, 1.200h — FOUSP/USP-SP), o pré-requisito é registro ativo no CRO e graduação em Odontologia. Sua passagem pela Imersão já é um diferencial enorme — você vai chegar com o fluxo digital dominado. Posso te conectar à Profa. Luciana Yamaguchi para uma conversa rápida esta semana?"\n\nEsse perfil fecha rápido quando sente que a continuidade da jornada é clara e segura.'
  }
  if (t.includes('persona') || t.includes('perfil') || t.includes('converte mais')) {
    return 'O Recém-Especializado tem a maior taxa de conversão — 33% — com o ciclo de venda mais curto. Sua dor é aguda: insegurança cirúrgica. A solução é direta: o fluxo digital como "GPS cirúrgico" que elimina o medo de erros irreversíveis.\n\nO Especialista Analógico representa 58% dos leads mas converte a 16% — jornada longa. Nunca o trate como iniciante: valide a experiência clínica dele antes de qualquer argumento tecnológico.\n\nO Iniciado Digital (19%, conv. 12,5%) tem o maior LTV potencial — upsell natural para o Master 3.0 após a Imersão.\n\nO Focado em Prótese (9%) não converte na Imersão — encaminhe diretamente para o Master 3.0 com argumento de Planejamento Reverso.'
  }
  if (t.includes('semana') || t.includes('performance') || t.includes('resumo')) {
    return 'Resumo desta semana:\n\nLeads novos: 12 (+4,2% vs semana anterior)\nConversas ativas: 4\nMatriculados: 2 (Dr. Fabio J. — Imersão · Dra. Mariana Luz — Master 3.0)\nReceita fechada: R$ 28.150\n\nDestaque positivo: tempo médio de resposta em 4m12s — abaixo da meta. Atenção: 3 leads em Negociando sem contato há +48h (Paulo Ferreira, Ricardo Oliveira, Sarah Jenkins) — risco de esfriamento. Recomendo reativação hoje.'
  }
  if (t.includes('churn') || t.includes('risco') || t.includes('perder')) {
    return 'Detectei 3 leads em risco de churn nos próximos 2 dias:\n\n• Dr. Paulo Ferreira — 2 dias sem contato, Negociando (Imersão). Perfil: Iniciado Digital. Argumento: destravar ROI do scanner com o fluxo completo da Imersão.\n\n• Dr. Ricardo Oliveira — 1 dia sem contato, Contatado (Master 3.0). Perfil: Focado em Prótese. Argumento: Planejamento Reverso — controle total da reabilitação antes mesmo da cirurgia.\n\n• Sarah Jenkins — sem resposta desde ontem (Imersão). Perfil: Recém-Especializada. Argumento: segurança cirúrgica via guias impressos em 3D com Neodent Easy-Guide.\n\nDeseja que eu gere as mensagens de reativação para cada um?'
  }
  if (t.includes('helena') || t.includes('proposta')) {
    return 'Dra. Helena Martins — perfil Especialista Analógico (Master 3.0, R$ 22.250). A proposta deve validar a experiência dela ANTES de qualquer argumento técnico.\n\nMensagem sugerida: "Dra. Helena, com sua bagagem clínica, o fluxo digital vai amplificar o que você já domina — não substituir. No Master 3.0, o Prof. Dr. Marcelo Romano conecta os princípios biológicos que você já conhece ao posicionamento apical preciso via planejamento digital: você opera com a confiança de quem tem décadas de experiência e a precisão de milímetro da cirurgia guiada. FOUSP/USP-SP, 100% clínico em pacientes reais."\n\nComplementar com case de ex-aluna com 15+ anos de experiência aumenta a conversão em até 40%.'
  }
  if (t.includes('paulo') || t.includes('reativ')) {
    return 'Dr. Paulo Ferreira — perfil Iniciado Digital (Imersão). A reativação deve tocar na dor do "ativo imobilizado".\n\nMensagem sugerida: "Dr. Paulo, muitos dentistas com scanner Sirios que passaram pela nossa Imersão descrevem o mesmo: o equipamento estava sendo usado só para moldagem digital — R$ 100k de scanner gerando o mesmo resultado que um alginato. Na Imersão, você aprende a conectar o scanner ao planejamento 3D reverso e à cirurgia guiada — saindo fazendo na semana seguinte. A próxima turma tem apenas 2 vagas. Consigo reservar uma para você até amanhã?"\n\nEsse perfil responde bem a urgência genuína e ROI concreto.'
  }
  if (t.includes('imersão') || t.includes('master') || t.includes('especialização') || t.includes('curso') || t.includes('produto')) {
    return 'Portfólio completo MR Digital — todos certificados pela FOUSP/USP-SP:\n\n1. Imersão em Implantodontia Digital — 3 dias (24h), presencial. Fluxo completo: enceramento digital, planejamento 3D, cirurgia guiada (Neodent Easy-Guide) e impressão 3D. Indicado para Especialista Analógico e Recém-Especializado.\n\n2. Master 3.0 — Aperfeiçoamento Clínico — 10 meses (160h), semanal. Atendimento de pacientes reais supervisionado por mestres e doutores da FOUSP (Profs. Marcelo Romano, Eduardo Perissinoto, Luciana Yamaguchi, Marcos Venturini). Indicado para Iniciado Digital (upsell) e Focado em Prótese.\n\n3. Especialização em Implantodontia Digital — 24 meses (1.200h). Formação completa: biologia peri-implantar, regeneração tecidual, PRF, CAD/CAM, levantamento de seio maxilar. A maior chancela acadêmica do mercado.'
  }
  return 'Entendido! No modelo consultivo SPIN da MR, o foco é sempre aprofundar a Implicação da dor antes de apresentar a solução. Quer que eu identifique o perfil de persona do lead e sugira a abertura de abordagem ideal?'
}

// ─── Quick action chips ───────────────────────────────────────────────────────
const SUGGESTIONS = [
  { label: 'Resumir performance desta semana', icon: BarChart2 },
  { label: 'Leads em risco de churn', icon: AlertTriangle },
  { label: 'Qual persona converte mais?', icon: Users },
  { label: 'Me explique os cursos da MR', icon: FileText },
]

// ─── Message bubble ───────────────────────────────────────────────────────────
const MessageBubble = memo(function MessageBubble({ msg }) {
  const isAssistant = msg.role === 'assistant'
  return (
    <div className={`flex gap-3 ${isAssistant ? 'items-start' : 'items-start flex-row-reverse'}`}>
      {/* Avatar */}
      <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isAssistant ? 'bg-[#2563EB]' : 'bg-slate-200'}`}>
        {isAssistant
          ? <Bot size={16} className="text-white" />
          : <User size={16} className="text-slate-500" />
        }
      </div>

      {/* Bubble */}
      <div className={`max-w-[72%] ${isAssistant ? '' : ''}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
            isAssistant
              ? 'bg-white border border-slate-100 shadow-sm text-slate-700 rounded-tl-sm'
              : 'bg-[#2563EB] text-white rounded-tr-sm'
          }`}
        >
          {msg.text}
        </div>
        <p className={`text-[10px] text-slate-400 mt-1.5 ${isAssistant ? 'ml-1' : 'mr-1 text-right'}`}>
          {msg.timestamp}
        </p>
      </div>
    </div>
  )
})

// ─── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex gap-3 items-start">
      <div className="shrink-0 w-8 h-8 rounded-full bg-[#2563EB] flex items-center justify-center">
        <Bot size={16} className="text-white" />
      </div>
      <div className="bg-white border border-slate-100 shadow-sm px-4 py-3 rounded-2xl rounded-tl-sm">
        <div className="flex gap-1 items-center h-4">
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

// ─── Copiloto Page ────────────────────────────────────────────────────────────
export default function Copiloto() {
  const [messages, setMessages] = useState(coPilotoSeedMessages)
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const nextId = useRef(coPilotoSeedMessages.length + 1)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  function now() {
    return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  function sendMessage(text) {
    const trimmed = text.trim()
    if (!trimmed) return

    const userMsg = { id: nextId.current++, role: 'user', text: trimmed, timestamp: now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    setTimeout(() => {
      const aiMsg = { id: nextId.current++, role: 'assistant', text: getAiResponse(trimmed), timestamp: now() }
      setMessages(prev => [...prev, aiMsg])
      setIsTyping(false)
    }, 1200)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] -mt-2">

      {/* ── Chat Header ── */}
      <div className="bg-white border border-slate-100 rounded-2xl shadow-sm px-6 py-4 mb-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#2563EB] flex items-center justify-center shadow-md shadow-blue-500/20">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 font-headline">Copiloto MR</h2>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <p className="text-[10px] text-slate-400 font-medium">Assistente de inteligência comercial · Online</p>
            </div>
          </div>
        </div>
        <span className="flex items-center gap-1.5 text-xs font-bold text-[#2563EB] bg-blue-50 px-3 py-1.5 rounded-full">
          <Sparkles size={12} />
          IA Generativa
        </span>
      </div>

      {/* ── Messages Area ── */}
      <div className="flex-1 overflow-y-auto bg-white border border-slate-100 rounded-2xl shadow-sm p-6 space-y-5 min-h-0">
        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* ── Quick Suggestions ── */}
      <div className="flex gap-2 mt-3 flex-wrap shrink-0">
        {SUGGESTIONS.map(s => (
          <button
            key={s.label}
            onClick={() => sendMessage(s.label)}
            disabled={isTyping}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-full text-xs font-semibold hover:border-blue-300 hover:text-[#2563EB] hover:bg-blue-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <s.icon size={11} />
            {s.label}
          </button>
        ))}
      </div>

      {/* ── Input Bar ── */}
      <div className="mt-3 shrink-0">
        <div className="flex gap-3 bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-sm focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-500/10 transition-all">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pergunte sobre seus leads, funil, follow-ups..."
            className="flex-1 resize-none text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none bg-transparent leading-relaxed"
            style={{ maxHeight: '96px' }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isTyping}
            className="self-end w-8 h-8 rounded-xl bg-[#2563EB] flex items-center justify-center text-white shadow-md shadow-blue-500/20 hover:bg-[#1D4ED8] transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none shrink-0"
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-center text-[10px] text-slate-300 mt-2">
          Enter para enviar · Shift+Enter para nova linha
        </p>
      </div>
    </div>
  )
}
