import { AlertTriangle, CheckCircle2, Info, Loader2, XCircle } from 'lucide-react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-slate-600">{subtitle}</p>}
      </div>
      {actions}
    </div>
  )
}

export function Card({
  title,
  description,
  children,
  className = '',
  actions,
}: {
  title?: string
  description?: string
  children: ReactNode
  className?: string
  actions?: ReactNode
}) {
  return (
    <section className={`animate-fade-in rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {(title || actions) && (
        <header className="mb-4 flex flex-wrap items-start justify-between gap-2">
          <div>
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  )
}

type Variant = 'primary' | 'secondary' | 'ghost'
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  loading?: boolean
  icon?: ReactNode
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-green-600 text-white hover:bg-green-700 focus-visible:outline-green-600 disabled:bg-green-300',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 focus-visible:outline-slate-400 disabled:text-slate-400',
  ghost: 'text-slate-600 hover:bg-slate-100 focus-visible:outline-slate-400 disabled:text-slate-300',
}

export function Button({ variant = 'primary', loading, icon, children, disabled, className = '', ...rest }: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : icon}
      {children}
    </button>
  )
}

type AlertKind = 'error' | 'warning' | 'info' | 'success'
const ALERT_STYLES: Record<AlertKind, { box: string; icon: ReactNode }> = {
  error: { box: 'border-red-200 bg-red-50 text-red-800', icon: <XCircle className="h-5 w-5 shrink-0" aria-hidden /> },
  warning: { box: 'border-amber-200 bg-amber-50 text-amber-900', icon: <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden /> },
  info: { box: 'border-sky-200 bg-sky-50 text-sky-900', icon: <Info className="h-5 w-5 shrink-0" aria-hidden /> },
  success: { box: 'border-green-200 bg-green-50 text-green-900', icon: <CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden /> },
}

export function Alert({ kind = 'info', title, children }: { kind?: AlertKind; title?: string; children?: ReactNode }) {
  const s = ALERT_STYLES[kind]
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} className={`flex gap-3 rounded-lg border p-3 text-sm ${s.box}`}>
      {s.icon}
      <div className="min-w-0">
        {title && <p className="font-medium">{title}</p>}
        {children && <div className={title ? 'mt-0.5' : ''}>{children}</div>}
      </div>
    </div>
  )
}

export function EmptyState({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white/60 px-6 py-12 text-center">
      <div className="mb-3 rounded-full bg-green-50 p-3 text-green-600">{icon}</div>
      <p className="font-medium text-slate-800">{title}</p>
      {children && <p className="mt-1 max-w-md text-sm text-slate-500">{children}</p>}
    </div>
  )
}

export function Spinner({ label }: { label: string }) {
  return (
    <div role="status" className="flex items-center gap-3 text-sm text-slate-600">
      <Loader2 className="h-5 w-5 animate-spin text-green-600" aria-hidden />
      <span className="animate-pulse-soft">{label}</span>
    </div>
  )
}

export function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}

export function Badge({ children, tone = 'gray' }: { children: ReactNode; tone?: 'gray' | 'green' | 'red' | 'amber' }) {
  const tones = {
    gray: 'bg-slate-100 text-slate-700',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
    amber: 'bg-amber-100 text-amber-900',
  }
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>
}
