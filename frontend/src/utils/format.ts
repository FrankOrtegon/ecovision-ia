const pctFmt = (digits: number) =>
  new Intl.NumberFormat('es-CO', { style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits })

export function pct(value: number | null | undefined, digits = 1): string {
  return value === null || value === undefined ? 'n/d' : pctFmt(digits).format(value)
}

export function num(value: number | null | undefined, digits = 3): string {
  return value === null || value === undefined
    ? 'n/d'
    : new Intl.NumberFormat('es-CO', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
}

export function formatDate(iso: string | null): string {
  if (!iso) return 'Pendiente'
  const d = new Date(`${iso}T00:00:00`)
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })
}
