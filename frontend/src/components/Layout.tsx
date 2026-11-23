import { BarChart3, FileStack, Home, Info, Leaf, Menu, ScanSearch, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useHealth } from '../services/HealthContext'

const NAV = [
  { to: '/', label: 'Inicio', icon: Home },
  { to: '/clasificador', label: 'Clasificador', icon: ScanSearch },
  { to: '/lotes', label: 'Procesamiento por lotes', icon: FileStack },
  { to: '/evaluacion', label: 'Evaluación', icon: BarChart3 },
  { to: '/modelo', label: 'Acerca del modelo', icon: Info },
]

function ServiceStatus() {
  const { health, error, loading } = useHealth()
  let dot = 'bg-slate-300'
  let text = 'Comprobando servicio…'
  if (!loading && error) {
    dot = 'bg-red-500'
    text = 'Sin conexión con el servidor'
  } else if (health?.model_configured) {
    dot = 'bg-green-500'
    text = 'Servicio y modelo en línea'
  } else if (health) {
    dot = 'bg-amber-500'
    text = 'Servidor activo, modelo sin configurar'
  }
  return (
    <p className="flex items-center gap-2 text-xs text-slate-300" role="status">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden />
      {text}
    </p>
  )
}

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Principal" className="flex flex-col gap-1">
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive ? 'bg-green-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`
          }
        >
          <Icon className="h-4 w-4" aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-2 text-white">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-600">
        <Leaf className="h-5 w-5" aria-hidden />
      </span>
      <span className="text-lg font-semibold tracking-tight">EcoVision IA</span>
    </div>
  )
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden w-64 shrink-0 flex-col justify-between bg-slate-900 p-4 lg:flex lg:sticky lg:top-0 lg:h-screen">
        <div className="space-y-8">
          <Brand />
          <NavItems />
        </div>
        <div className="space-y-2 border-t border-slate-800 pt-4">
          <ServiceStatus />
          <p className="text-xs text-slate-500">Clasifica el material aparente; no determina si un residuo es reciclable.</p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between bg-slate-900 px-4 py-3 lg:hidden">
          <Brand />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="menu-movil"
            aria-label={open ? 'Cerrar menú' : 'Abrir menú'}
            className="rounded-lg p-2 text-white hover:bg-slate-800"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </header>
        {open && (
          <div id="menu-movil" className="animate-fade-in space-y-4 bg-slate-900 px-4 pb-4 lg:hidden">
            <NavItems onNavigate={() => setOpen(false)} />
            <ServiceStatus />
          </div>
        )}

        <main key={pathname} className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
        <footer className="border-t border-slate-200 px-4 py-4 text-center text-xs text-slate-500">
          EcoVision IA · Proyecto de maestría · Dataset TrashNet · Las imágenes se procesan sin almacenarse.
        </footer>
      </div>
    </div>
  )
}
