# Step 2 Review — Handoff for Next Session

## How to start

1. Read `plans/prototype.md` — full spec and implementation plan
2. Read all 4 prototype HTML files as visual reference:
   - `prototype/dashboard.html` — Analytics page (done)
   - `prototype/kanban.html` — Funil/Kanban page ← reference for Step 3
   - `prototype/chats.html` — Conversas page
   - `prototype/courses.html` — Cursos page
3. Read `plans/step_1_review.md` — context from Step 1
4. Read this file
5. Continue from **Step 3 — Funil Kanban**

---

## What is done

### Step 0 — Scaffolding ✓
See `plans/step_1_review.md` for full details.

### Step 1 — Layout Shell ✓
See `plans/step_1_review.md` for full details.

### Step 2 — Analytics Dashboard ✓

**Files created/modified:**

- `frontend/src/pages/Analytics.jsx` — full dashboard (was a stub)
- `frontend/src/components/charts/ConversationTrendsChart.jsx` — new lazy chunk
- `frontend/src/components/charts/RevenueChart.jsx` — new lazy chunk

**Sections implemented (top to bottom):**

1. **Page header** — title "Visão Geral de Performance" + subtitle + "Últimos 30 Dias" (outline) + "Exportar Relatório" (primary blue + Download icon) buttons
2. **KPI Cards row** (3-column grid) — Total de Leads (blue value, emerald badge), Novos Leads Hoje (orange badge), Taxa de Conversão (purple badge); each with colored icon circle, large value, and subtext
3. **Funnel Status row** (5-column grid) — Novo/Contatado/Negociando/Matriculado/Perdido; bar widths computed dynamically as `(count / maxCount) * 100%`; Matriculado highlighted in blue, Perdido in slate
4. **Two-panel charts row** (`grid-cols-12`):
   - Left (`col-span-5`): SPIN Abandonment — pure CSS horizontal bars (matches prototype HTML), opacity decreases per stage (1.0 → 0.8 → 0.6 → 0.4), red fill for churned portion, insight callout box with blue left border
   - Right (`col-span-7`): Conversation Trends — Recharts grouped BarChart (WhatsApp blue + Chamadas slate), two mini-stat cards below (Tempo Médio + Horário de Pico)
5. **Revenue chart** (full width) — Recharts BarChart; solid `#2563EB` bars for actuals (Jan–Jun), dashed-outline semi-transparent bars for projections (Jul–Dez) via custom `shape` prop on Bar; total revenue + growth rate displayed top-right

**Vercel performance rules applied:**

| Rule | Implementation |
|------|---------------|
| `rerender-no-inline-components` | `KpiCard`, `FunnelStageCard`, `SpinRow` defined at module scope |
| `rerender-memo` | All three card components wrapped in `React.memo` |
| `rerender-derived-state-no-effect` | `maxFunnelCount`, `KPI_CONFIG`, `SPIN_OPACITIES` computed at module level, not inside render |
| `bundle-dynamic-imports` | `ConversationTrendsChart` and `RevenueChart` are separate async chunks (verified in build output) |
| `rendering-conditional-render` | Ternaries used throughout (`isHighlighted ? ... : ...`) |

**Build output confirmed clean** — `✓ built in 260ms`, all chart chunks code-split correctly:
- `RevenueChart-*.js` — 1.61 kB
- `ConversationTrendsChart-*.js` — 8.33 kB
- `Analytics-*.js` — 9.95 kB

---

## Design notes (carry forward to all remaining steps)

- **Fonts**: `font-headline` class (Manrope) for headings/nav, Inter (default body). Both loaded via Google Fonts in `index.css`.
- **Sidebar**: light `bg-slate-50/90` — NOT dark. Active nav: `border-l-4 border-blue-600 bg-white text-blue-600 shadow-sm rounded-lg`.
- **Primary color**: `#2563EB` (plan spec), NOT `#004ac6` (prototype HTML).
- **Cards**: `bg-white rounded-2xl shadow-sm border border-slate-100` pattern used throughout.
- **Content padding**: Layout provides `p-6` inside `ml-64 pt-16`. Pages add their own `pb-8` and section spacing internally.
- **Chart skeleton**: `<div className="h-XX rounded-xl bg-slate-100 animate-pulse" />` used as Suspense fallback.

---

## Vercel Best Practices to apply (all remaining steps)

Rules live at `.claude/worktrees/sweet-leavitt/.claude/vercel-react-best-practices/rules/`

| Rule | What to do |
|------|-----------|
| `rerender-no-inline-components` | Define all sub-components outside the parent render function |
| `rerender-memo` | Wrap expensive list/card components in `React.memo` |
| `rerender-derived-state-no-effect` | Compute filtered/sorted lists during render, not in `useEffect` |
| `bundle-dynamic-imports` | Use `React.lazy` + `Suspense` for any Recharts charts |
| `js-index-maps` | Use `new Map(...)` for O(1) lead lookups in Conversas (Step 4) |
| `rendering-conditional-render` | Use `condition ? <A /> : null` instead of `condition && <A />` |

---

## Next steps

| Step | File | Status |
|------|------|--------|
| 2 | `src/pages/Analytics.jsx` | ✓ DONE |
| 3 | `src/pages/Funil.jsx` | **TODO — start here** |
| 4 | `src/pages/Conversas.jsx` | TODO |
| 5 | `src/pages/Cursos.jsx` | TODO |

### Step 3 instructions

Replace the stub `Funil.jsx` with the full Kanban pipeline. Reference `prototype/kanban.html` for exact layout and component structure. All lead data comes from `leads` in `src/data/mock.js`.

**Key implementation points:**

1. **Header** — "Funil de Vendas" title + subtitle + "Importar Leads" (outline + Upload icon) + "+ Novo Lead" (primary) buttons
2. **Kanban board** — `overflow-x-auto` container, 5 columns side by side with fixed `min-w-[260px]`
3. **Column anatomy** — colored dot + title + count badge header; scrollable card list below; "+ Adicionar card" footer
4. **Lead Card** — source badge (color-coded by channel), name, course, footer with clock + time-ago + avatar
5. **Negociando card extras** — "Prioridade" amber badge, progress bar, R$ value, calendar + follow-up label
6. **Drag & Drop** — `@dnd-kit/core` + `@dnd-kit/sortable`; `DndContext` wraps the board; `SortableContext` per column; `useSortable` on each card; `onDragEnd` updates local `useState` copy of leads
7. **"+ Novo Lead" Modal** — fields: Nome, E-mail, Telefone, Canal de Origem (select), Curso de Interesse (select); "Salvar" adds to NOVO column; ESC / outside-click closes; use `useEffect` cleanup for keyboard listener
8. **State**: keep leads in local `useState` initialized from `mock.js` leads; derive column buckets during render (not in effect)

**Columns config:**
```js
const COLUMNS = [
  { id: 'Novo',        label: 'NOVO',        dotColor: 'bg-blue-500'   },
  { id: 'Contatado',   label: 'CONTATADO',   dotColor: 'bg-yellow-500' },
  { id: 'Negociando',  label: 'NEGOCIANDO',  dotColor: 'bg-orange-500' },
  { id: 'Matriculado', label: 'MATRICULADO', dotColor: 'bg-green-500'  },
  { id: 'Perdido',     label: 'PERDIDO',     dotColor: 'bg-slate-400'  },
]
```

**Source badge colors:**
```js
const SOURCE_COLORS = {
  Instagram:    'bg-pink-50 text-pink-700',
  'Site Direto':'bg-blue-50 text-blue-700',
  WhatsApp:     'bg-green-50 text-green-700',
  Indicação:    'bg-indigo-50 text-indigo-700',
  'E-mail':     'bg-slate-50 text-slate-600',
}
```

Dev server: `cd frontend && npm run dev`
