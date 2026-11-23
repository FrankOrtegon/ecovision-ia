import type { ClassName } from '../types/api'
import { CLASS_NAMES } from '../constants/classes'

/** Evita inyección de fórmulas al abrir el CSV en Excel o Sheets. */
function escapeCell(value: unknown): string {
  let s = value === null || value === undefined ? '' : String(value)
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function toCsv(columns: string[], rows: Array<Record<string, unknown>>): string {
  const lines = [columns.map(escapeCell).join(',')]
  for (const row of rows) lines.push(columns.map((c) => escapeCell(row[c])).join(','))
  return lines.join('\n') + '\n'
}

export function downloadText(filename: string, content: string, mime = 'text/csv;charset=utf-8'): void {
  // BOM para que Excel reconozca UTF-8.
  const blob = new Blob([mime.startsWith('text/csv') ? '\ufeff' : '', content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export interface LabelRow {
  filename: string
  true_label: ClassName
}

export interface ParsedLabels {
  rows: LabelRow[]
  errors: string[]
}

function splitLine(line: string): string[] {
  const out: string[] = []
  let cur = ''
  let quoted = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        cur += '"'
        i++
      } else if (ch === '"') quoted = false
      else cur += ch
    } else if (ch === '"') quoted = true
    else if (ch === ',') {
      out.push(cur)
      cur = ''
    } else cur += ch
  }
  out.push(cur)
  return out.map((c) => c.trim())
}

/** Lectura previa del CSV de etiquetas (formato: cabecera filename,true_label). El backend valida de nuevo. */
export function parseLabelsCsv(text: string): ParsedLabels {
  const lines = text.replace(/^\ufeff/, '').split(/\r?\n/).filter((l) => l.trim() !== '')
  const errors: string[] = []
  const head = lines[0] ? splitLine(lines[0]).map((c) => c.toLowerCase()) : []
  const iName = head.indexOf('filename')
  const iLabel = head.indexOf('true_label')
  if (iName < 0 || iLabel < 0) {
    return { rows: [], errors: ['El CSV debe tener la cabecera "filename,true_label".'] }
  }
  const rows: LabelRow[] = []
  const seen = new Set<string>()
  const invalid = new Set<string>()
  for (const line of lines.slice(1)) {
    const cells = splitLine(line)
    const filename = (cells[iName] ?? '').trim()
    const label = (cells[iLabel] ?? '').trim().toLowerCase()
    if (!filename) continue
    if (!(CLASS_NAMES as readonly string[]).includes(label)) {
      invalid.add(label || '(vacía)')
      continue
    }
    if (seen.has(filename)) {
      errors.push(`Nombre repetido en el CSV: ${filename}`)
      continue
    }
    seen.add(filename)
    rows.push({ filename, true_label: label as ClassName })
  }
  if (invalid.size) {
    errors.push(`Etiquetas no válidas: ${[...invalid].slice(0, 5).join(', ')}. Permitidas: ${CLASS_NAMES.join(', ')}.`)
  }
  if (!rows.length && !errors.length) errors.push('El CSV no tiene filas.')
  return { rows, errors }
}

export interface MatchSummary {
  matched: number
  imagesWithoutLabel: string[]
  labelsWithoutImage: string[]
}

export function matchLabels(imageNames: string[], rows: LabelRow[]): MatchSummary {
  const labelNames = new Set(rows.map((r) => r.filename))
  const imgNames = new Set(imageNames)
  return {
    matched: imageNames.filter((n) => labelNames.has(n)).length,
    imagesWithoutLabel: imageNames.filter((n) => !labelNames.has(n)),
    labelsWithoutImage: rows.map((r) => r.filename).filter((n) => !imgNames.has(n)),
  }
}

export const LABELS_TEMPLATE = 'filename,true_label\nejemplo_1.jpg,glass\nejemplo_2.jpg,plastic\n'
