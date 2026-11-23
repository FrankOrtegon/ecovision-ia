import { CLASS_INFO } from '../constants/classes'
import type { ClassName } from '../types/api'

export default function ConfusionMatrix({ labels, matrix }: { labels: ClassName[]; matrix: number[][] }) {
  const rowTotals = matrix.map((r) => r.reduce((a, b) => a + b, 0))
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-1 text-center text-sm">
        <caption className="sr-only">Matriz de confusión: filas = clase real, columnas = clase predicha</caption>
        <thead>
          <tr>
            <th className="p-1 text-xs font-medium text-slate-500">Real ↓ / Predicho →</th>
            {labels.map((l) => (
              <th key={l} scope="col" className="p-1 text-xs font-medium text-slate-600">
                {CLASS_INFO[l].es}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th scope="row" className="whitespace-nowrap p-1 pr-2 text-right text-xs font-medium text-slate-600">
                {CLASS_INFO[labels[i] as ClassName].es}
              </th>
              {row.map((v, j) => {
                const total = rowTotals[i] ?? 0
                const share = total > 0 ? v / total : 0
                const diagonal = i === j
                const alpha = v === 0 ? 0 : 0.12 + 0.88 * share
                const bg = diagonal ? `rgba(22,163,74,${alpha})` : `rgba(239,68,68,${alpha})`
                return (
                  <td
                    key={j}
                    title={`Real: ${CLASS_INFO[labels[i] as ClassName].es} · Predicho: ${CLASS_INFO[labels[j] as ClassName].es} · ${v} (${(share * 100).toFixed(1)} % de la fila)`}
                    className="h-12 min-w-14 rounded-md border border-slate-200 font-medium"
                    style={{ backgroundColor: bg, color: alpha > 0.8 ? '#fff' : '#0f172a' }}
                  >
                    {v}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-500">Verde: aciertos (diagonal). Rojo: confusiones. La intensidad es la proporción de la fila.</p>
    </div>
  )
}
