import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'

// bundle-dynamic-imports: lazy-load all page components
const Analytics = lazy(() => import('./pages/Analytics.jsx'))
const Funil = lazy(() => import('./pages/Funil.jsx'))
const Conversas = lazy(() => import('./pages/Conversas.jsx'))
const Cursos = lazy(() => import('./pages/Cursos.jsx'))

function PageSkeleton() {
  return (
    <div className="animate-pulse space-y-4 p-2">
      <div className="h-8 bg-slate-200 rounded-lg w-1/3" />
      <div className="h-4 bg-slate-100 rounded w-1/2" />
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="h-32 bg-slate-200 rounded-xl" />
        <div className="h-32 bg-slate-200 rounded-xl" />
        <div className="h-32 bg-slate-200 rounded-xl" />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route
            index
            element={
              <Suspense fallback={<PageSkeleton />}>
                <Analytics />
              </Suspense>
            }
          />
          <Route
            path="funil"
            element={
              <Suspense fallback={<PageSkeleton />}>
                <Funil />
              </Suspense>
            }
          />
          <Route
            path="conversas"
            element={
              <Suspense fallback={<PageSkeleton />}>
                <Conversas />
              </Suspense>
            }
          />
          <Route
            path="cursos"
            element={
              <Suspense fallback={<PageSkeleton />}>
                <Cursos />
              </Suspense>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
