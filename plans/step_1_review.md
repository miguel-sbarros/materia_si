# Step 1 Review — Handoff for Next Session

## How to start

1. Read `plans/prototype.md` — full spec and implementation plan
2. Read all 4 prototype HTML files as visual reference:
   - `prototype/dashboard.html` — Analytics page
   - `prototype/kanban.html` — Funil/Kanban page
   - `prototype/chats.html` — Conversas page
   - `prototype/courses.html` — Cursos page
3. Read this file
4. Continue from **Step 2 — Analytics Dashboard**

---

## What is done

### Step 0 — Scaffolding
- Vite + React 18 project at `frontend/`
- Tailwind CSS v4 via `@tailwindcss/vite` plugin (no `tailwind.config.js` needed — uses `@import "tailwindcss"` in CSS)
- Installed packages: `react-router-dom`, `recharts`, `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`, `lucide-react`
- `frontend/src/index.css` — Tailwind import + Google Fonts (Manrope + Inter) + CSS vars
- `frontend/src/data/mock.js` — all mock data: `currentUser`, `leads`, `conversations`, `messages`, `courses`, `cohort`, `analyticsData`

### Step 1 — Layout Shell
- `frontend/src/App.jsx` — React Router v6, 4 routes (`/`, `/funil`, `/conversas`, `/cursos`), all pages lazy-loaded with `React.lazy` + `Suspense`
- `frontend/src/components/Layout.jsx` — sidebar + topbar shell using `<Outlet />`
  - Sidebar: MR Digital logo, 4 nav items with lucide-react icons, user footer (initials avatar + name + role)
  - Active nav: blue left border + white bg + blue text
  - Topbar: search bar (w-80), bell (with red dot badge), settings, avatar
- Stub pages created (just placeholders): `Analytics.jsx`, `Funil.jsx`, `Conversas.jsx`, `Cursos.jsx`

---

## Design notes (from reading the prototype HTMLs)

- **Fonts**: Manrope (headlines/nav) + Inter (body). Already loaded via Google Fonts in `index.css`.
- **Sidebar**: light (`bg-slate-50/90`), NOT dark — the prototype HTMLs use a light sidebar, overriding the dark spec in `prototype.md`.
- **Icons**: The prototypes use Material Symbols Outlined. We switched to **lucide-react** as specified in the plan.
- **Primary color**: The prototype HTML uses `#004ac6` as `primary` but the plan spec says `#2563EB`. Stick with `#2563EB` (plan spec).
- **Active nav style**: `border-l-4 border-blue-600 bg-white text-blue-600 shadow-sm rounded-lg`

---

## Vercel Best Practices to apply (all steps)

Rules live at `.claude/worktrees/sweet-leavitt/.claude/vercel-react-best-practices/rules/`

Apply these throughout every component you write:

| Rule | What to do |
|------|-----------|
| `rerender-no-inline-components` | Define all sub-components outside the parent render function |
| `rerender-memo` | Wrap expensive list/card components in `React.memo` |
| `rerender-derived-state-no-effect` | Compute filtered/sorted lists during render, not in `useEffect` |
| `bundle-dynamic-imports` | Use `React.lazy` + `Suspense` for Recharts charts (already done for pages) |
| `js-index-maps` | Use `new Map(...)` for O(1) lead lookups in Conversas |
| `rendering-conditional-render` | Use `condition ? <A /> : null` instead of `condition && <A />` |

---

## Next steps

| Step | File | Status |
|------|------|--------|
| 2 | `src/pages/Analytics.jsx` | **TODO — start here** |
| 3 | `src/pages/Funil.jsx` | TODO |
| 4 | `src/pages/Conversas.jsx` | TODO |
| 5 | `src/pages/Cursos.jsx` | TODO |

### Step 2 instructions
Replace the stub `Analytics.jsx` with the full dashboard. Use `recharts` for charts, wrapped in `React.lazy` + `Suspense` with a skeleton fallback. Reference `prototype/dashboard.html` for exact layout and component structure. All data comes from `analyticsData` in `src/data/mock.js`.

Dev server: `cd frontend && npm run dev`
