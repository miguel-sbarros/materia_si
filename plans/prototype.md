# Captus CRM — Prototype Plan

> **Project**: Captus - MR Digital  
> **Scope**: Functional React SPA prototype with 5 screens  
> **Stack**: React 18 · React Router v6 · Tailwind CSS · Recharts · @dnd-kit/core  
> **Aesthetic Direction**: Professional & refined — dark sidebar with crisp white content area. Primary blue `#2563EB`, neutral slate backgrounds. Typography: `DM Sans` (display) + `Inter` (body). Subtle depth through layered shadows, not gradients. Think Bloomberg Terminal meets modern SaaS.

---

## Context Summary

**Product**: Captus is a CRM tailored for solo course creators and small education businesses in Brazil. Users manage leads (prospective students), track them through a sales pipeline, communicate via WhatsApp/email, and manage course cohorts with limited seats.

**Key pain points solved**:
- Scattered leads across WhatsApp, Instagram DMs, spreadsheets
- No visibility into pipeline stages or cohort capacity
- Manual follow-up with no alerts
- Re-opening a new cohort with no record of who was previously interested

**Primary persona**: Solo course creator who is simultaneously teacher, salesperson, and admin.

---

## Tech Architecture

```
src/
├── App.jsx                  # Router setup
├── components/
│   └── Layout.jsx           # Sidebar + topbar shell
├── pages/
│   ├── Analytics.jsx        # Page 1 — Dashboard
│   ├── Funil.jsx            # Page 2 — Kanban Pipeline
│   ├── Conversas.jsx        # Page 3 — Chat center
│   └── Cursos.jsx           # Page 4 — Course management
├── data/
│   └── mock.js              # All mock data in one file
└── index.css                # Tailwind directives + custom CSS vars
```

### Performance Rules to Apply (from Vercel guide)
- `rerender-no-inline-components` — define all sub-components outside parent render
- `rerender-memo` — memoize card lists and chart wrappers
- `rerender-derived-state-no-effect` — compute filtered/sorted lists during render, not in effects
- `bundle-dynamic-imports` — lazy-load Recharts charts with `React.lazy` + `Suspense`
- `js-index-maps` — use `Map` for O(1) lead lookups in Conversas panel
- `rendering-conditional-render` — use ternary (not `&&`) for conditional JSX

---

## Step 0 — Project Scaffolding

**Before coding, ask the user for the sketch of the Layout/Shell screen.**

### What to build
- Vite + React project initialized
- Tailwind CSS configured with custom palette
- `react-router-dom`, `recharts`, `@dnd-kit/core`, `lucide-react` installed
- Global CSS variables defined
- `mock.js` with all data for all 5 pages

### CSS Variables
```css
:root {
  --primary: #2563EB;
  --primary-dark: #1D4ED8;
  --sidebar-bg: #1E293B;
  --sidebar-text: #94A3B8;
  --sidebar-active: #2563EB;
  --bg: #F8FAFC;
  --card-bg: #FFFFFF;
  --border: #E2E8F0;
  --text-primary: #0F172A;
  --text-secondary: #64748B;
}
```

### Sketch request (Step 0)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Layout Shell** (sidebar + top bar) so the implementation matches your vision.

---

## Step 1 — Layout Shell (`Layout.jsx` + `App.jsx`)

### Sketch request (Step 1)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Layout Shell** (sidebar + topbar) if not yet shared.

### Components
**Sidebar** (fixed, `w-64`, `bg-[#1E293B]`):
- Logo area: "MR Digital" wordmark in white, `DM Sans` bold, top of sidebar
- Nav items (4): Análises, Funil, Conversas, Cursos — each with Lucide icon
  - Inactive: icon + label in `#94A3B8`
  - Active: left blue bar (`w-1 bg-[#2563EB]`), text white, bg `rgba(37,99,235,0.15)`
- Footer: user avatar (initials circle) + name + role in small gray text

**Topbar** (sticky, `h-16`, white, border-bottom):
- Search field (left): placeholder "Buscar leads, pacientes ou cursos..." with search icon, `w-80`
- Right cluster: notification bell (badge count), settings gear icon, avatar

**Content area**: `flex-1 bg-[#F8FAFC] overflow-auto p-6`

**Routing**: React Router v6 `<Routes>` with paths `/`, `/funil`, `/conversas`, `/cursos`. Default route → Analytics.

---

## Step 2 — Analytics Dashboard (`Analytics.jsx`)

### Sketch request (Step 2)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Analytics Dashboard** screen before implementation begins.

### Layout (top to bottom)

#### Header row
- Left: Title "Visão Geral de Performance" (`text-2xl font-semibold`) + subtitle
- Right: "Últimos 30 Dias" (outline button) + "Exportar Relatório" (primary blue button)

#### KPI Cards row (3 cards, equal width)
| Card | Value | Badge | Subtext |
|------|-------|-------|---------|
| Total de Leads | 250 | +4.2% (green) | Leads qualificados no funil atual |
| Novos Leads Hoje | 12 | Ativos Agora (orange) | Novas oportunidades desde 00:00 |
| Taxa de Conversão | 18% | Top 5% (red) | Taxa de lead para matriculado |

Card design: white bg, `rounded-xl shadow-sm`, icon in colored circle, value in `text-3xl font-bold`, badge as pill.

#### Funil Status row (5 cards in a row)
Each card: label + number (bold) + colored progress bar
- Novo: 42, blue
- Contatado: 68, yellow
- Negociando: 31, orange
- Matriculado: 85, blue (highlighted with subtle blue bg)
- Perdido: 24, gray

#### Two-panel row

**Left panel — "Abandono por Estágio (SPIN)"**:
- Title + `recharts` stacked horizontal bar chart
- 4 rows: Situação (12% churn), Problema (28%), Implicação (45%), Necessidade (15%)
- Blue = retained, rose = churned
- Insight card below (dark blue bg `#1E3A5F`, white text): "O abandono é maior no estágio de **Implicação**..."

**Right panel — "Tendências de Conversa"**:
- Grouped bar chart (WhatsApp blue vs Chamadas gray) across 6 time periods
- Two mini-stat cards below: "Tempo Médio de Resposta: 4m 12s" and "Horário de Pico: 14:00–16:00"

#### Revenue chart (full width)
- Title "Histórico de receita mensal e projeção de crescimento"
- Recharts `BarChart` for Jan–Dez (last 6 solid, next 6 with dashed outline = projection)
- Right side: "FATURAMENTO TOTAL (ANO) R$ 1.428.500" in primary blue, "+15.4% vs. ano anterior"

**Performance**: wrap Recharts in `React.lazy` + `Suspense` with skeleton fallback.

---

## Step 3 — Funil Kanban (`Funil.jsx`)

### Sketch request (Step 3)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Funil/Kanban** screen before implementation begins.

### Layout

#### Header
- "Funil de Vendas" + subtitle
- "Importar Leads" (outline + upload icon) + "+ Novo Lead" (primary)
- Course/cohort filter dropdown

#### Kanban Board
`overflow-x-auto` container with 5 columns side by side.

**Column anatomy**:
```
[colored dot] COLUMN TITLE    [count badge]
─────────────────────────────
[Lead Card]
[Lead Card]
[+ Add card]
```

**Column configs**:
| Column | Dot Color | Count |
|--------|-----------|-------|
| NOVO | blue | 12 |
| CONTATADO | yellow | 08 |
| NEGOCIANDO | blue | — |
| MATRICULADO | green | — |
| PERDIDO | gray | — |

**Lead Card** (`bg-white rounded-lg shadow-sm p-3 mb-2 cursor-grab`):
- Source badge: INSTAGRAM (green), SITE DIRETO (blue), WHATSAPP (green-dark), INDICAÇÃO (indigo)
- Lead name (bold `text-sm`)
- Course of interest (gray `text-xs`)
- Footer: clock icon + "2h atrás" (left) | avatar circle (right)

**Negociando card extras**:
- "Prioridade" badge (top-right corner, amber)
- Progress bar (blue)
- "R$ 12.400,00" value
- Calendar icon + "Follow-up" label

**Drag & Drop**: `@dnd-kit/core` with `DndContext`, `SortableContext` per column. `useSortable` hook on each card. On drop, update local state.

**"+ Novo Lead" Modal**:
Fields: Nome, E-mail, Telefone, Canal de Origem (select), Curso de Interesse (select).
"Salvar" adds card to NOVO column. ESC or outside click closes.

---

## Step 4 — Conversas Chat (`Conversas.jsx`)

### Sketch request (Step 4)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Conversas** screen before implementation begins.

### Three-panel layout (`h-[calc(100vh-64px)] flex`)

#### Left Panel (25% width) — Lead List
- Header: "Leads Ativos"
- Filter pills: TODOS (active=blue), NÃO LIDOS, WHATSAPP
- Lead list items:
  - Name (bold) + timestamp (right)
  - Message preview (1 line, truncated)
  - Channel badge (WHATSAPP green, E-MAIL blue)
- Selected item: `border-l-2 border-[#2563EB] bg-blue-50`

#### Center Panel (45% width) — Chat Thread
- Header: avatar + name + "Online • respondendo via WhatsApp" + phone icon + menu icon
- Messages area (`overflow-y-auto flex-1`):
  - Received: gray bubble, left-aligned, with avatar
  - Sent: `bg-[#2563EB]` bubble, right-aligned, white text, company avatar
  - Each: timestamp + channel label + read status ("Lida ✓✓")
- Footer: text input + attachment button (+) + send button (blue arrow)
- Scroll to bottom on mount: `useEffect` + `scrollIntoView`

#### Right Panel (30% width) — Lead Context
- Avatar (large, initials) + name + role/description
- Action buttons: "PERFIL" (outline) + "MATRICULAR" (outline)
- Sections (each with title + content):
  - **CURSO DE INTERESSE**: course name + icon
  - **ESTÁGIO NO FUNIL**: badge "Negociação" + "80% Prob."
  - **NOTAS RÁPIDAS**: cards with `bg-[#F8FAFC]`, italic text, (+) button to add
  - **ATIVIDADE RECENTE**: vertical timeline with colored dots; each item: type + timestamp

**Performance**: `useMemo` on filtered lead list. `useCallback` on send handler.

---

## Step 5 — Cursos (`Cursos.jsx`)

### Sketch request (Step 5)
> **STOP — Before proceeding:** Share the sketch/wireframe for the **Cursos** screen before implementation begins.

### Two internal views (toggle via `useState`)

#### View 1 — Course List
- Title "Cursos Ativos"
- Grid (`grid-cols-3 gap-4`): one card per course
  - Course name (bold)
  - Short description
  - Modality badges: Presencial, Híbrido, EAD
  - "X turmas ativas" count
  - Click → View 2

#### View 2 — Cohort Detail

**Breadcrumb**: `CURSOS > IMERSÃO EM IMPLANTODONTIA DIGITAL` (clickable back to View 1)

**Header**: course name + "Editar Ementa" (outline) + "Matricular Aluno" (primary with + icon)

**Metrics row (3 cards)**:
| Card | Content |
|------|---------|
| MATRÍCULAS | 24/30, blue progress bar (80%) |
| PERÍODO LETIVO | 01 Mai 2026 → 12 Dez 2026, badges: PRESENCIAL, HÍBRIDO, TURMA T2 |
| INVESTIMENTO | "R$ 22.250 / vaga" (dark blue bg, white text), "Receita Prevista: R$ 534.000,00" |

**Cronograma (vertical timeline)**:
- Month nav arrows (top right)
- Each item: circle with date (left) | content block (right)
  - Title: "Módulo 01: Fundamentos"
  - Subtitle: time + location + description
  - Red badge "PRESENÇA OBRIGATÓRIA" for evaluations

**Documentos table**:
- "Gerenciar Documentos" title + "Fazer Upload" button
- Table: Nome | Tipo | Data de Upload | Ações (download icon, delete icon)
- 3 mock rows (PDF, DOCX, ZIP)

**Alunos Matriculados list**:
- Title + "24 perfis ativos para a turma ACD-2026"
- Search field + filter button + export button
- Student cards: avatar | name + email | matrícula date | STATUS badge (PAGO & ATIVO green, PARCELADO amber) | FREQUÊNCIA (100%, 92%)
- "VER TODOS OS 24 ALUNOS MATRICULADOS" button

---

## Mock Data Overview (`src/data/mock.js`)

```js
export const currentUser = { name: "Dra. Ana Costa", role: "Coordenadora Comercial", initials: "AC" }

export const leads = [ /* 12 leads with: id, name, email, phone, source, course, stage, lastContact, value, assignee */ ]

export const conversations = [ /* 5 leads with: id, leadId, messages[], lastMessage, unread, channel */ ]

export const messages = { /* leadId → Message[] with: id, text, sent(bool), timestamp, channel, read */ }

export const courses = [ /* 3 courses with: id, name, description, modalities[], cohorts[] */ ]

export const cohort = { /* 1 detailed cohort: students[], schedule[], documents[], metrics */ }

export const analyticsData = { kpis, funnelStages, spinAbandonment, conversationTrends, revenue }
```

---

## Implementation Order

| Step | File | Depends On | Sketch Required |
|------|------|------------|-----------------|
| 0 | Scaffolding + mock.js | — | — |
| 1 | Layout.jsx + App.jsx | mock.js | YES — Layout sketch |
| 2 | Analytics.jsx | Layout | YES — Analytics sketch |
| 3 | Funil.jsx | Layout | YES — Funil sketch |
| 4 | Conversas.jsx | Layout | YES — Conversas sketch |
| 5 | Cursos.jsx | Layout | YES — Cursos sketch |

---

## Workflow Protocol

For **each step above**, the agent must:

1. Announce which page is next
2. **Ask the user to share the sketch/photo for that page**
3. Wait for the sketch
4. Analyze the sketch and reconcile with the prompt spec
5. Implement the component
6. Ask for review before moving to the next step

---

## Design System Reference

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Primary | `#2563EB` | Buttons, active states, links, chart bars |
| Primary Dark | `#1D4ED8` | Hover states |
| Sidebar | `#1E293B` | Sidebar background |
| Background | `#F8FAFC` | Page background |
| Card | `#FFFFFF` | Card backgrounds |
| Border | `#E2E8F0` | Dividers, input borders |
| Text Primary | `#0F172A` | Headings, bold text |
| Text Secondary | `#64748B` | Subtitles, timestamps |
| Success | `#16A34A` | PAGO & ATIVO, positive badges |
| Warning | `#D97706` | PARCELADO, Ativos Agora |
| Danger | `#DC2626` | Perdido, Presença Obrigatória |

### Typography
- Display: `DM Sans` (headings, nav labels, card titles)
- Body: `Inter` (table cells, messages, form labels)
- Load via Google Fonts in `index.html`

### Component Patterns
- Cards: `bg-white rounded-xl shadow-sm border border-[#E2E8F0] p-5`
- Primary button: `bg-[#2563EB] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1D4ED8]`
- Outline button: `border border-[#E2E8F0] text-[#0F172A] rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#F8FAFC]`
- Badge: `text-xs font-semibold px-2 py-0.5 rounded-full`
- Input: `border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563EB]`
