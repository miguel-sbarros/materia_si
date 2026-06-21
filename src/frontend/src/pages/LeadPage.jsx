import { useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Check, Upload, Pencil, X } from 'lucide-react'
import { getLeadDetail, importChat, updateLead, moveDeal, clockTime } from '../lib/api.js'
import { spinLabel, fmtDuration } from '../lib/profile.js'
import { PERSONA_META } from '../data/copilot.js'
import { INPUT_CLASS, SOURCES } from '../components/funil/constants.js'

// Fallback neutro (slate) quando a persona é nula/desconhecida — placeholder até P3.
// Não usar o DEFAULT_META do copiloto (azul) aqui: a página do lead distingue
// "persona definida" de "ainda sem análise de IA".
const SLATE_META = { color: '#475569', bg: '#F1F5F9' }
const personaTint = (persona) => PERSONA_META[persona] || SLATE_META

// Estágios/colunas válidos para o deal (mesmos alvos do PATCH /deals): abertos + terminais.
const STAGE_OPTIONS = ['Novo', 'Contatado', 'Negociando', 'Aprovado', 'Matriculado', 'Perdido']

function initialsOf(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// Badge da coluna/estágio do deal — mesma paleta do Kanban.
const COLUMN_BADGE = {
  Novo: 'bg-slate-100 text-slate-600',
  Contatado: 'bg-blue-50 text-blue-600',
  Negociando: 'bg-amber-50 text-amber-700',
  Aprovado: 'bg-green-50 text-green-700',
  Matriculado: 'bg-emerald-50 text-emerald-700',
  Perdido: 'bg-red-50 text-red-600',
}

function SectionLabel({ children }) {
  return (
    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-2">
      {children}
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div>
      <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-0.5">
        {label}
      </div>
      <div className="text-sm text-slate-700 font-medium">{value}</div>
    </div>
  )
}

// Campo de formulário (rótulo + input/select) usado no modo de edição inline.
function Field({ label, children }) {
  return (
    <div>
      <label className="block text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-1">
        {label}
      </label>
      {children}
    </div>
  )
}

// Paleta das listas de itens da análise (dor/desejo/objeção/comentário).
const CHIP_TONE = {
  dor: 'bg-red-50 text-red-700',
  desejo: 'bg-emerald-50 text-emerald-700',
  objecao: 'bg-amber-50 text-amber-700',
  comentario: 'bg-slate-100 text-slate-600',
}

function Chips({ label, items, tone }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-1.5">
        {label}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((it, i) => (
          <span key={i} className={`text-xs font-medium px-2 py-1 rounded-lg ${tone}`}>
            {it}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function LeadPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)

  // Edição inline (sem modal): dados do lead + estágio de cada deal.
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', source: '' })
  const [dealForm, setDealForm] = useState({}) // dealId → { column, lostReason }
  const [localError, setLocalError] = useState(null)

  const { data: lead, isLoading, isError, error } = useQuery({
    queryKey: ['leadDetail', id],
    queryFn: () => getLeadDetail(id),
    retry: false,
  })

  // Salva tudo: PATCH /leads/{id} (dados de contato) + PATCH /deals/{id} para cada deal
  // cujo estágio mudou. Perdido exige motivo (validado no cliente antes de enviar).
  const saveMut = useMutation({
    mutationFn: async () => {
      await updateLead(id, {
        name: form.name.trim(),
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        source: form.source || null,
      })
      for (const d of lead.deals) {
        const df = dealForm[d.id]
        if (df && df.column !== d.column) {
          await moveDeal(d.id, {
            column: df.column,
            lostReason: df.column === 'Perdido' ? df.lostReason.trim() : null,
          })
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leadDetail', id] })
      queryClient.invalidateQueries({ queryKey: ['deals'] }) // nome/origem/estágio refletem no Funil
      setEditing(false)
    },
  })

  const startEdit = () => {
    if (!lead) return
    setForm({
      name: lead.name || '',
      email: lead.email || '',
      phone: lead.phone || '',
      source: lead.source || '',
    })
    setDealForm(
      Object.fromEntries(lead.deals.map((d) => [d.id, { column: d.column, lostReason: '' }])),
    )
    setLocalError(null)
    saveMut.reset()
    setEditing(true)
  }

  const cancelEdit = () => {
    setEditing(false)
    setLocalError(null)
  }

  const handleSave = () => {
    if (!form.name.trim()) {
      setLocalError('O nome é obrigatório.')
      return
    }
    // Perdido exige motivo.
    const missingReason = lead.deals.some((d) => {
      const df = dealForm[d.id]
      return df && df.column !== d.column && df.column === 'Perdido' && !df.lostReason.trim()
    })
    if (missingReason) {
      setLocalError('Informe o motivo da perda para mover uma negociação a Perdido.')
      return
    }
    setLocalError(null)
    saveMut.mutate()
  }

  const setDeal = (dealId, patch) =>
    setDealForm((prev) => ({ ...prev, [dealId]: { ...prev[dealId], ...patch } }))

  // A página já conhece o lead → importa direto para ele (.txt e .zip), sem wizard.
  const importMut = useMutation({
    mutationFn: (file) => importChat(file, { leadId: id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leadDetail', id] })
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (err) => {
      window.alert(`Falha ao importar: ${err.message}`)
    },
  })

  const handleImportClick = () => fileInputRef.current?.click()
  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) importMut.mutate(file)
    e.target.value = '' // permite re-selecionar o mesmo arquivo
  }

  const importButton = (
    <>
      <button
        type="button"
        onClick={handleImportClick}
        disabled={importMut.isPending}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-[10px] font-bold rounded-lg uppercase hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        <Upload size={12} />
        {importMut.isPending ? 'Importando…' : 'Importar conversa'}
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip,.txt"
        className="hidden"
        onChange={handleFileChange}
      />
    </>
  )

  const backButton = (
    <button
      type="button"
      onClick={() => navigate(-1)}
      className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-700 transition-colors mb-5"
    >
      <ArrowLeft size={16} />
      Voltar
    </button>
  )

  if (isLoading) {
    return (
      <div className="max-w-3xl">
        {backButton}
        <p className="text-sm text-slate-400">Carregando lead...</p>
      </div>
    )
  }

  if (isError || !lead) {
    const notFound = error?.status === 404
    return (
      <div className="max-w-3xl">
        {backButton}
        <p className="text-sm text-red-600">
          {notFound ? 'Lead não encontrado.' : 'Não foi possível carregar o lead.'}
        </p>
      </div>
    )
  }

  const profile = lead.profile
  const meta = personaTint(profile?.persona)

  return (
    <div className="max-w-3xl pb-10">
      <div className="flex items-center justify-between">
        {backButton}
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button
                type="button"
                onClick={cancelEdit}
                disabled={saveMut.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-[10px] font-bold rounded-lg uppercase hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                <X size={12} />
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saveMut.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-[10px] font-bold rounded-lg uppercase hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                <Check size={12} />
                {saveMut.isPending ? 'Salvando…' : 'Salvar'}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={startEdit}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-[10px] font-bold rounded-lg uppercase hover:bg-slate-50 transition-colors"
              >
                <Pencil size={12} />
                Editar
              </button>
              {importButton}
            </>
          )}
        </div>
      </div>

      {editing && (localError || saveMut.isError) ? (
        <p className="text-sm font-semibold text-red-600 mb-3">
          {localError || saveMut.error?.message}
        </p>
      ) : null}

      {/* Cabeçalho — avatar tingido por persona + nome + badge */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <div className="flex items-center gap-3.5 px-6 py-5">
          <span
            className="w-12 h-12 rounded-full flex items-center justify-center text-base font-bold font-headline shrink-0"
            style={{ background: meta.bg, color: meta.color }}
          >
            {initialsOf(editing ? form.name : lead.name)}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              {editing ? (
                <input
                  value={form.name}
                  onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                  placeholder="Nome do lead"
                  className={`${INPUT_CLASS} max-w-xs font-headline font-bold`}
                />
              ) : (
                <h2 className="font-headline text-xl font-extrabold text-slate-900 tracking-tight">
                  {lead.name}
                </h2>
              )}
              <span
                className="text-[11px] font-bold px-2 py-0.5 rounded-full"
                style={{ background: meta.bg, color: meta.color }}
              >
                {profile?.persona || 'Sem persona'}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
              <Check size={12} className="text-green-500" />
              Perfil e histórico carregados
            </div>
          </div>
        </div>

        {/* Dados do lead — grade de atributos (leitura) ou formulário (edição) */}
        <div className="border-t border-slate-100 bg-slate-50 px-6 py-5">
          {editing ? (
            <div className="grid grid-cols-2 gap-x-8 gap-y-4">
              <Field label="Email">
                <input
                  value={form.email}
                  onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                  type="email"
                  placeholder="email@exemplo.com"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Telefone">
                <input
                  value={form.phone}
                  onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
                  type="tel"
                  placeholder="(11) 99999-0000"
                  className={INPUT_CLASS}
                />
              </Field>
              <Field label="Origem">
                <select
                  value={form.source}
                  onChange={(e) => setForm((p) => ({ ...p, source: e.target.value }))}
                  className={INPUT_CLASS}
                >
                  <option value="">Selecione...</option>
                  {SOURCES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </Field>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-x-8 gap-y-3.5">
              {lead.attributes.map((attr) => (
                <div key={attr.label}>
                  <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400 mb-0.5">
                    {attr.label}
                  </div>
                  <div className="text-sm text-slate-700 font-medium">{attr.value}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Análise da conversa (IA, P3) — somente leitura */}
      <div className="bg-white border border-slate-200 rounded-2xl px-6 py-5 mt-5">
        <SectionLabel>Análise da conversa (IA)</SectionLabel>
        {profile ? (
          <div className="flex flex-col gap-4">
            {profile.summary ? (
              <p className="text-sm text-slate-600 leading-relaxed">{profile.summary}</p>
            ) : null}
            <div className="grid grid-cols-2 gap-x-8 gap-y-3.5">
              <Metric
                label="Score"
                value={profile.leadScore != null ? `${profile.leadScore}/100` : '—'}
              />
              <Metric label="Estágio SPIN" value={spinLabel(profile.currentSpinStage)} />
              <Metric label="Especialidade" value={profile.especialidade || '—'} />
              <Metric label="Experiência" value={profile.experiencia || '—'} />
              <Metric
                label="Latência média (resposta)"
                value={fmtDuration(profile.medianSellerLatencySeconds)}
              />
              <Metric
                label="Abandono"
                value={
                  profile.isAbandoned
                    ? `Sim — ${spinLabel(profile.abandonSpinStage)}`
                    : 'Não'
                }
              />
            </div>
            <Chips label="Dores" items={profile.dores} tone={CHIP_TONE.dor} />
            <Chips label="Desejos" items={profile.desejos} tone={CHIP_TONE.desejo} />
            <Chips label="Objeções" items={profile.objecoes} tone={CHIP_TONE.objecao} />
            <Chips label="Comentários" items={profile.comentarios} tone={CHIP_TONE.comentario} />
            {profile.personaReasoning ? (
              <p className="text-xs text-slate-400 italic">{profile.personaReasoning}</p>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-slate-400">
            Sem análise ainda. Importe a conversa (4+ mensagens) para gerar o perfil
            automaticamente.
          </p>
        )}
      </div>

      {/* Deals — visão multi-curso (estágio editável no modo de edição) */}
      <div className="bg-white border border-slate-200 rounded-2xl px-6 py-5 mt-5">
        <SectionLabel>Negociações ({lead.deals.length})</SectionLabel>
        {lead.deals.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhuma negociação registrada.</p>
        ) : (
          <div className="flex flex-col gap-2.5">
            {lead.deals.map((d) => {
              const df = dealForm[d.id] || { column: d.column, lostReason: '' }
              return (
                <div
                  key={d.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 px-4 py-3"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-slate-900 truncate">{d.course}</div>
                    <div className="text-xs text-slate-400 truncate">{d.cohortName}</div>
                  </div>
                  {editing ? (
                    <div className="flex items-center gap-2 shrink-0">
                      {df.column === 'Perdido' && df.column !== d.column ? (
                        <input
                          value={df.lostReason}
                          onChange={(e) => setDeal(d.id, { lostReason: e.target.value })}
                          placeholder="Motivo da perda"
                          className={`${INPUT_CLASS} w-40 py-1.5 text-xs`}
                        />
                      ) : null}
                      <select
                        value={df.column}
                        onChange={(e) => setDeal(d.id, { column: e.target.value })}
                        className={`${INPUT_CLASS} w-36 py-1.5 text-xs`}
                      >
                        {STAGE_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${
                        COLUMN_BADGE[d.column] || 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {d.column}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Histórico WhatsApp — bolhas (lead esquerda branca / vendedor direita #DCF8C6) */}
      <div className="bg-white border border-slate-200 rounded-2xl px-6 py-5 mt-5">
        <SectionLabel>Histórico de conversa</SectionLabel>
        {lead.conversation.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhuma mensagem importada ainda.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {lead.conversation.map((m) =>
              m.sent ? (
                <div key={m.id} className="flex justify-end">
                  <div
                    className="max-w-[78%] text-sm leading-relaxed px-3 py-2 rounded-tl-xl rounded-tr-xl rounded-bl-xl"
                    style={{ background: '#DCF8C6', color: '#1F3D2B' }}
                  >
                    <div className="whitespace-pre-line">{m.text}</div>
                    {m.sentAt ? (
                      <div className="text-[10px] text-[#1F3D2B]/50 text-right mt-1">
                        {clockTime(m.sentAt)}
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : (
                <div key={m.id} className="flex justify-start">
                  <div className="max-w-[78%] bg-white border border-slate-200 text-slate-700 text-sm leading-relaxed px-3 py-2 rounded-tl-xl rounded-tr-xl rounded-br-xl">
                    <div className="whitespace-pre-line">{m.text}</div>
                    {m.sentAt ? (
                      <div className="text-[10px] text-slate-400 text-right mt-1">
                        {clockTime(m.sentAt)}
                      </div>
                    ) : null}
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}
