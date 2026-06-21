// ─── useCopilot — state keystone do Copiloto (P4, backend real) ─────────────
// Estado dirigido por SESSÕES persistidas: a sidebar lista as sessões, anexar um
// lead via @ cria uma NOVA sessão por lead, e cada mensagem vai/volta pela seam
// lib/copilotApi.js. O Send de um path grava no histórico WhatsApp do lead via
// sendMessage() (lib/api.js) — não chama API externa.

import { useCallback, useEffect, useReducer, useRef } from 'react'
import { COMMANDS } from '../data/copilot.js'
import {
  searchLeads,
  getLeadContext,
  createSession,
  attachLead,
  listSessions,
  getSession,
  postChat,
} from '../lib/copilotApi.js'
import { sendMessage } from '../lib/api.js'

// Primeiro nome do lead para o placeholder: remove "Dr."/"Dra." inicial e pega
// o primeiro token (mesma regra do protótipo).
const firstNameOf = (lead) =>
  lead.name.replace(/^Dr[a]?\.\s*/, '').split(' ')[0]

const initialState = {
  input: '',
  attachedLead: null,
  leadExpanded: false,
  showMentions: false,
  mentionQuery: '',
  mentionResults: [],
  slashOpen: false,
  slashQuery: '',
  isTyping: false,
  copiedKey: null,
  sentKey: null,
  nextId: 1, // ids locais (otimistas) das mensagens do usuário
  sessions: [],
  currentSessionId: null,
  messages: [],
  pendingLead: null, // lead aguardando confirmação de "nova conversa"
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_INPUT':
      return { ...state, input: action.value }

    case 'OPEN_SLASH':
      return {
        ...state,
        input: action.value,
        slashOpen: true,
        slashQuery: action.query,
        showMentions: false,
        mentionQuery: '',
      }

    case 'OPEN_MENTIONS':
      return {
        ...state,
        input: action.value,
        showMentions: true,
        mentionQuery: action.query,
        slashOpen: false,
        slashQuery: '',
      }

    case 'CLOSE_MENUS':
      return {
        ...state,
        input: action.value,
        slashOpen: false,
        slashQuery: '',
        showMentions: false,
        mentionQuery: '',
      }

    case 'SET_MENTION_RESULTS':
      return { ...state, mentionResults: action.results }

    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions }

    case 'ATTACH_LEAD': // anexa o lead à sessão ATUAL (mantém o thread)
      return {
        ...state,
        attachedLead: action.lead,
        currentSessionId: action.sessionId,
        input: action.input,
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
        leadExpanded: false,
        pendingLead: null,
      }

    case 'PICK_LEAD': // nova sessão por lead: thread limpo + lead anexado
      return {
        ...state,
        attachedLead: action.lead,
        currentSessionId: action.sessionId,
        messages: [],
        input: action.input,
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
        leadExpanded: false,
        isTyping: false,
        pendingLead: null,
      }

    case 'SET_PENDING_LEAD': // sessão já tem lead → pede confirmação de nova conversa
      return {
        ...state,
        pendingLead: action.lead,
        input: action.input,
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
      }

    case 'CLEAR_PENDING_LEAD':
      return { ...state, pendingLead: null }

    case 'OPEN_SESSION': // abre sessão existente da sidebar
      return {
        ...state,
        currentSessionId: action.sessionId,
        messages: action.messages,
        attachedLead: action.lead,
        input: '',
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
        slashOpen: false,
        slashQuery: '',
        leadExpanded: false,
        isTyping: false,
        pendingLead: null,
      }

    case 'SET_SESSION': // fixa a sessão atual (criada sob demanda no onSend/runSlash)
      return { ...state, currentSessionId: action.sessionId }

    case 'PUSH_USER': // push user msg + abre typing, limpando menus/input
      return {
        ...state,
        messages: [...state.messages, action.message],
        input: '',
        showMentions: false,
        mentionQuery: '',
        slashOpen: false,
        slashQuery: '',
        nextId: state.nextId + 1,
        isTyping: true,
      }

    case 'PUSH_ASSISTANT':
      return {
        ...state,
        messages: [...state.messages, action.message],
        isTyping: false,
      }

    case 'STOP_TYPING':
      return { ...state, isTyping: false }

    case 'TOGGLE_LEAD_EXPANDED':
      return { ...state, leadExpanded: !state.leadExpanded }

    case 'NEW_CHAT':
      return {
        ...state,
        currentSessionId: null,
        messages: [],
        attachedLead: null,
        input: '',
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
        slashOpen: false,
        slashQuery: '',
        leadExpanded: false,
        isTyping: false,
        pendingLead: null,
      }

    case 'SET_COPIED':
      return { ...state, copiedKey: action.key }

    case 'SET_SENT':
      return { ...state, sentKey: action.key }

    default:
      return state
  }
}

export default function useCopilot() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const scrollRef = useRef(null)
  const copyTimer = useRef(null)
  const sentTimer = useRef(null)

  // Carrega a lista de sessões da sidebar no mount.
  const refreshSessions = useCallback(async () => {
    try {
      const sessions = await listSessions()
      dispatch({ type: 'SET_SESSIONS', sessions })
    } catch {
      /* backend indisponível — sidebar fica vazia */
    }
  }, [])

  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  // Auto-scroll para o fim a cada nova mensagem ou enquanto "digitando".
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [state.messages, state.isTyping])

  // Limpa timeouts pendentes ao desmontar.
  useEffect(() => () => {
    clearTimeout(copyTimer.current)
    clearTimeout(sentTimer.current)
  }, [])

  const onInputChange = useCallback((e) => {
    const val = e.target.value
    const slash = val.match(/^\/([\w-]*)$/)
    if (slash) {
      dispatch({ type: 'OPEN_SLASH', value: val, query: slash[1] })
      return
    }
    const m = val.match(/(^|\s)@([^\s@]*)$/u)
    if (m) {
      const query = m[2]
      dispatch({ type: 'OPEN_MENTIONS', value: val, query })
      searchLeads(query).then((results) =>
        dispatch({ type: 'SET_MENTION_RESULTS', results })
      )
      return
    }
    dispatch({ type: 'CLOSE_MENUS', value: val })
  }, [])

  // Anexar lead via @:
  //  • sessão atual JÁ COM lead → não anexa; abre confirmação de "nova conversa".
  //  • sessão atual SEM lead → anexa o lead à sessão atual (mantém o thread);
  //    sem sessão ainda → cria a primeira com o lead.
  //  • se o backend recusar o anexo (409: a sessão já está vinculada a um lead, ex.:
  //    o chip foi removido mas o vínculo persiste) → cai na confirmação de nova conversa,
  //    NUNCA cria uma sessão silenciosamente.
  const pickLead = useCallback(async (summary) => {
    const input = state.input.replace(/(^|\s)@[^\s@]*$/u, '$1')
    const full = await getLeadContext(summary.id)
    if (state.attachedLead) {
      dispatch({ type: 'SET_PENDING_LEAD', lead: full, input })
      return
    }
    if (state.currentSessionId) {
      try {
        const session = await attachLead(state.currentSessionId, summary.id)
        dispatch({ type: 'ATTACH_LEAD', lead: full, sessionId: session.id, input })
        refreshSessions()
      } catch (err) {
        if (err.status !== 409) throw err
        dispatch({ type: 'SET_PENDING_LEAD', lead: full, input })
      }
      return
    }
    const session = await createSession(summary.id)
    dispatch({ type: 'ATTACH_LEAD', lead: full, sessionId: session.id, input })
    refreshSessions()
  }, [state.input, state.attachedLead, state.currentSessionId, refreshSessions])

  // Confirma o pendingLead → cria NOVA sessão (thread limpo) com esse lead.
  const confirmNewSession = useCallback(async () => {
    const pending = state.pendingLead
    if (!pending) return
    const session = await createSession(pending.id)
    dispatch({ type: 'PICK_LEAD', lead: pending, sessionId: session.id, input: '' })
    refreshSessions()
  }, [state.pendingLead, refreshSessions])

  const cancelNewSession = useCallback(
    () => dispatch({ type: 'CLEAR_PENDING_LEAD' }),
    [],
  )

  // Abre uma sessão da sidebar: carrega mensagens (+ contexto do lead se houver).
  const openSession = useCallback(async (sessionId) => {
    const { session, messages } = await getSession(sessionId)
    let lead = null
    if (session.leadId) {
      try {
        lead = await getLeadContext(session.leadId)
      } catch {
        /* lead removido — segue sem chip */
      }
    }
    dispatch({ type: 'OPEN_SESSION', sessionId, messages, lead })
  }, [])

  // Garante uma sessão atual; cria uma (com o lead anexado, se houver) sob demanda.
  const ensureSession = useCallback(async () => {
    if (state.currentSessionId) return state.currentSessionId
    const session = await createSession(state.attachedLead?.id ?? null)
    dispatch({ type: 'SET_SESSION', sessionId: session.id })
    return session.id
  }, [state.currentSessionId, state.attachedLead])

  const onSend = useCallback(async () => {
    const text = state.input.trim()
    if (!text) return
    const userMsg = { id: `u-${state.nextId}`, role: 'user', kind: 'text', text }
    dispatch({ type: 'PUSH_USER', message: userMsg })
    try {
      const sessionId = await ensureSession()
      const reply = await postChat(sessionId, { text })
      dispatch({ type: 'PUSH_ASSISTANT', message: reply })
      refreshSessions()
    } catch {
      dispatch({ type: 'STOP_TYPING' })
    }
  }, [state.input, state.nextId, ensureSession, refreshSessions])

  const runSlash = useCallback(async (cmd) => {
    const label = COMMANDS.find((c) => c.cmd === cmd)?.label || cmd
    const userMsg = { id: `u-${state.nextId}`, role: 'user', kind: 'text', text: label }
    dispatch({ type: 'PUSH_USER', message: userMsg })
    try {
      const sessionId = await ensureSession()
      const reply = await postChat(sessionId, { command: cmd })
      dispatch({ type: 'PUSH_ASSISTANT', message: reply })
      refreshSessions()
    } catch {
      dispatch({ type: 'STOP_TYPING' })
    }
  }, [state.nextId, ensureSession, refreshSessions])

  // slashResults: COMMANDS filtrado pela slashQuery (cmd ou label).
  const slashQ = state.slashQuery.toLowerCase()
  const slashResults = COMMANDS.filter(
    (c) => c.cmd.toLowerCase().includes(slashQ) || c.label.toLowerCase().includes(slashQ)
  )

  const onKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (state.slashOpen) {
        const first = slashResults[0]
        if (first) {
          runSlash(first.cmd)
          return
        }
      }
      if (state.showMentions) {
        const first = state.mentionResults[0]
        if (first) {
          pickLead(first)
          return
        }
      }
      onSend()
    }
  }, [state.slashOpen, state.showMentions, state.mentionResults, slashResults, runSlash, pickLead, onSend])

  // Remover o lead anexado: como o vínculo lead↔sessão é fixo no backend, "tirar o lead"
  // significa sair da conversa dele → reinicia num chat limpo (a sessão fica na sidebar).
  // Isso evita o dessincronismo (chip sem lead, mas sessão ainda vinculada) que fazia o
  // próximo anexo criar uma sessão nova silenciosamente.
  const removeLead = useCallback(() => dispatch({ type: 'NEW_CHAT' }), [])

  const toggleLeadExpanded = useCallback(
    () => dispatch({ type: 'TOGGLE_LEAD_EXPANDED' }),
    []
  )

  const newChat = useCallback(() => dispatch({ type: 'NEW_CHAT' }), [])

  const copyVariant = useCallback((key, text) => {
    try {
      navigator.clipboard?.writeText(text)
    } catch {
      // clipboard indisponível — ignora silenciosamente.
    }
    dispatch({ type: 'SET_COPIED', key })
    clearTimeout(copyTimer.current)
    copyTimer.current = setTimeout(
      () => dispatch({ type: 'SET_COPIED', key: null }),
      1600
    )
  }, [])

  // Envia o texto de um path para o histórico WhatsApp do lead anexado.
  const sendToHistory = useCallback(async (key, text) => {
    const leadId = state.attachedLead?.id
    if (!leadId) return
    dispatch({ type: 'SET_SENT', key: `${key}:sending` })
    try {
      await sendMessage(leadId, text)
      dispatch({ type: 'SET_SENT', key: `${key}:sent` })
      clearTimeout(sentTimer.current)
      sentTimer.current = setTimeout(
        () => dispatch({ type: 'SET_SENT', key: null }),
        1600
      )
    } catch {
      dispatch({ type: 'SET_SENT', key: null })
    }
  }, [state.attachedLead])

  const placeholder = state.attachedLead
    ? `Pergunte sobre ${firstNameOf(state.attachedLead)}...`
    : 'Pergunte, digite / para comandos ou @ para anexar um lead...'

  return {
    userName: 'Dra. Ana',
    isEmpty: state.messages.length === 0,
    messages: state.messages,
    input: state.input,
    placeholder,
    isTyping: state.isTyping,
    attachedLead: state.attachedLead,
    leadExpanded: state.leadExpanded,
    showMentions: state.showMentions,
    mentionResults: state.mentionResults,
    slashOpen: state.slashOpen,
    slashResults,
    copiedKey: state.copiedKey,
    sentKey: state.sentKey,
    sessions: state.sessions,
    currentSessionId: state.currentSessionId,
    pendingLead: state.pendingLead,
    scrollRef,
    onInputChange,
    onKeyDown,
    onSend,
    pickLead,
    confirmNewSession,
    cancelNewSession,
    runSlash,
    removeLead,
    toggleLeadExpanded,
    newChat,
    openSession,
    copyVariant,
    sendToHistory,
  }
}
