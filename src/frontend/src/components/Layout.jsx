import { useState, useEffect, useRef } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { BarChart2, Filter, MessageCircle, GraduationCap, Bot, Bell, Settings, Search } from 'lucide-react'
import { currentUser } from '../data/mock.js'
import { searchLeads } from '../lib/api.js'

// ─── Sub-components defined outside render (rerender-no-inline-components) ───

function Logo() {
  return (
    <div className="px-6 mb-10 flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl overflow-hidden shrink-0">
        <img src="/logo-mr.png" alt="MR Digital" className="w-full h-full object-cover" />
      </div>
      <div>
        <h1 className="text-base font-bold text-slate-900 tracking-tight leading-none font-headline">
          MR Digital
        </h1>
        <p className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold mt-0.5">
          CRM Educacional
        </p>
      </div>
    </div>
  )
}

const NAV_ITEMS = [
  { to: '/', label: 'Análises', Icon: BarChart2 },
  { to: '/funil', label: 'Funil', Icon: Filter },
  { to: '/conversas', label: 'Conversas', Icon: MessageCircle },
  { to: '/cursos', label: 'Cursos', Icon: GraduationCap },
  { to: '/copiloto', label: 'Copiloto', Icon: Bot },
]

function NavItem( {to, label, Icon} ) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        isActive
          ? 'flex items-center gap-3 px-4 py-3 rounded-lg border-l-4 border-blue-600 bg-white text-blue-600 text-sm font-semibold font-headline shadow-sm transition-colors'
          : 'flex items-center gap-3 px-4 py-3 rounded-lg text-slate-500 hover:bg-slate-100 text-sm font-semibold font-headline transition-colors'
      }
    >
      <Icon size={18} />
      <span>{label}</span>
    </NavLink>
  )
}

function SidebarFooter() {
  return (
    <div className="px-6 pt-6 border-t border-slate-200/60 mt-auto">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
          {currentUser.initials}
        </div>
        <div className="overflow-hidden">
          <p className="text-xs font-bold text-slate-800 truncate">{currentUser.name}</p>
          <p className="text-[10px] text-slate-400 truncate">{currentUser.role}</p>
        </div>
      </div>
    </div>
  )
}

function LeadSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const boxRef = useRef(null)

  // Busca debounced (300ms) na rota /leads?q=. A limpeza acontece no callback do
  // timeout (não síncrono no corpo do effect) — searchLeads resolve [] para termo vazio.
  useEffect(() => {
    const term = query.trim()
    const t = setTimeout(() => {
      searchLeads(term)
        .then(setResults)
        .catch(() => setResults([]))
    }, term ? 300 : 0)
    return () => clearTimeout(t)
  }, [query])

  // Fecha o dropdown ao clicar fora.
  useEffect(() => {
    function onClick(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  function selectLead(id) {
    navigate(`/leadpage/${id}`)
    setQuery('')
    setResults([])
    setOpen(false)
  }

  return (
    <div ref={boxRef} className="relative w-80">
      <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        placeholder="Buscar leads, pacientes ou cursos..."
        className="w-full bg-slate-100 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      />
      {open && query.trim() ? (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden z-50">
          {results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-slate-400">Nenhum lead encontrado.</div>
          ) : (
            results.map((lead) => (
              <button
                key={lead.id}
                type="button"
                onClick={() => selectLead(lead.id)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 transition-colors"
              >
                <span className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-[11px] font-bold text-slate-500 shrink-0">
                  {lead.initials}
                </span>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-slate-800 truncate">{lead.name}</div>
                  <div className="text-[11px] text-slate-400 truncate">
                    {lead.persona || lead.stage || 'Lead'}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      ) : null}
    </div>
  )
}

function Topbar() {
  return (
    <header className="fixed top-0 right-0 w-[calc(100%-16rem)] h-16 flex justify-between items-center px-8 z-40 bg-white border-b border-slate-100">
      {/* Search */}
      <LeadSearch />

      {/* Right cluster */}
      <div className="flex items-center gap-5">
        <button className="relative text-slate-500 hover:text-slate-700 transition-colors">
          <Bell size={19} />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <button className="text-slate-500 hover:text-slate-700 transition-colors">
          <Settings size={19} />
        </button>
        <div className="w-px h-6 bg-slate-200" />
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600">MR Digital</span>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-bold">
            {currentUser.initials}
          </div>
        </div>
      </div>
    </header>
  )
}

// ─── Layout Shell ─────────────────────────────────────────────────────────────

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="h-screen w-64 fixed left-0 top-0 flex flex-col py-6 bg-slate-50/90 backdrop-blur-xl border-r border-slate-200/60 z-50">
        <Logo />
        <nav className="flex-1 px-4 space-y-1">
          {NAV_ITEMS.map(item => (
            <NavItem key={item.to} to={item.to} label={item.label} Icon={item.Icon} />
          ))}
        </nav>
        <SidebarFooter />
      </aside>

      {/* Topbar */}
      <Topbar />

      {/* Content area */}
      <main className="ml-64 pt-16 min-h-screen bg-slate-50">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
