// ─── useCopilot — state keystone do Copiloto ────────────────────────────────
// Porta a lógica de prototype/Copiloto WhatsApp.dc.html (class DCLogic) para um
// hook React idiomático. Toda a geração de resposta passa pela seam assíncrona
// em lib/copilotApi.js (searchLeads / getLeadContext / postCopilotChat).

import { useCallback, useEffect, useReducer, useRef } from 'react'
import { COPILOT_LEADS, DRAFTS, COMMANDS } from '../data/copilot.js'
import {
  searchLeads,
  getLeadContext,
  postCopilotChat,
} from '../lib/copilotApi.js'

// Primeiro nome do lead para o placeholder: remove "Dr."/"Dra." inicial e pega
// o primeiro token (mesma regra do protótipo).
const firstNameOf = (lead) =>
  lead.name.replace(/^Dr[a]?\.\s*/, '').split(' ')[0]

// ─── Estado inicial (seed = Elena, id 10) ───────────────────────────────────
const seedLead = COPILOT_LEADS.find((l) => l.id === 10)
const seedDraft = DRAFTS[10]

const initialState = {
  input: '',
  attachedLead: seedLead,
  leadExpanded: false,
  showMentions: false,
  mentionQuery: '',
  mentionResults: [],
  slashOpen: false,
  slashQuery: '',
  isTyping: false,
  copiedKey: null,
  nextId: 3,
  messages: [
    { id: 1, role: 'user', kind: 'text', text: 'Qual a melhor mensagem para destravar a matrícula dela na Especialização?' },
    { id: 2, role: 'assistant', kind: 'drafts', reasoning: seedDraft.reasoning, variants: seedDraft.variants },
  ],
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

    case 'PICK_LEAD':
      return {
        ...state,
        attachedLead: action.lead,
        input: action.input,
        showMentions: false,
        mentionQuery: '',
        mentionResults: [],
        leadExpanded: false,
      }

    case 'PUSH_USER': // push user msg + open typing, clearing menus/input
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
        nextId: state.nextId + 1,
        isTyping: false,
      }

    case 'REMOVE_LEAD':
      return { ...state, attachedLead: null }

    case 'TOGGLE_LEAD_EXPANDED':
      return { ...state, leadExpanded: !state.leadExpanded }

    case 'NEW_CHAT':
      return {
        ...state,
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
      }

    case 'SET_COPIED':
      return { ...state, copiedKey: action.key }

    default:
      return state
  }
}

export default function useCopilot() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const scrollRef = useRef(null)
  const copyTimer = useRef(null)

  // Auto-scroll para o fim a cada nova mensagem ou enquanto "digitando".
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [state.messages, state.isTyping])

  // Limpa o timeout de "copiado" ao desmontar.
  useEffect(() => () => clearTimeout(copyTimer.current), [])

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

  const pickLead = useCallback(async (summary) => {
    const full = await getLeadContext(summary.id)
    // Remove o "@query" final do input (mesma regra do protótipo).
    const input = state.input.replace(/(^|\s)@[^\s@]*$/u, '$1')
    dispatch({ type: 'PICK_LEAD', lead: full, input })
  }, [state.input])

  const onSend = useCallback(async () => {
    const text = state.input.trim()
    if (!text) return
    const userMsg = { id: state.nextId, role: 'user', kind: 'text', text }
    const nextMessages = [...state.messages, userMsg]
    dispatch({ type: 'PUSH_USER', message: userMsg })
    const result = await postCopilotChat({
      messages: nextMessages,
      leadId: state.attachedLead?.id,
    })
    dispatch({
      type: 'PUSH_ASSISTANT',
      message: { id: userMsg.id + 1, ...result },
    })
  }, [state.input, state.nextId, state.messages, state.attachedLead])

  const runSlash = useCallback(async (cmd) => {
    const label = COMMANDS.find((c) => c.cmd === cmd)?.label || cmd
    const userMsg = { id: state.nextId, role: 'user', kind: 'text', text: label }
    dispatch({ type: 'PUSH_USER', message: userMsg })
    const result = await postCopilotChat({ messages: state.messages, command: cmd })
    dispatch({
      type: 'PUSH_ASSISTANT',
      message: { id: userMsg.id + 1, ...result },
    })
  }, [state.nextId, state.messages])

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

  const removeLead = useCallback(() => dispatch({ type: 'REMOVE_LEAD' }), [])

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
    scrollRef,
    onInputChange,
    onKeyDown,
    onSend,
    pickLead,
    runSlash,
    removeLead,
    toggleLeadExpanded,
    newChat,
    copyVariant,
  }
}
