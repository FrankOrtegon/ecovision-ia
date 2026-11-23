import { CLASS_INFO } from '../constants/classes'
import type { AveragedMetrics, Curve, PerClassMetrics } from '../types/api'
import { num } from '../utils/format'

interface Props {
  perClass: PerClassMetrics[]
  macro: AveragedMetrics
  weighted: AveragedMetrics
  roc: Curve[]
  pr: Curve[]
  aucMacro: number | null
  apMacro: number | null
}

export default function MetricsTable({ perClass, macro, weighted, roc, pr, aucMacro, apMacro }: Props) {
  const auc = new Map(roc.map((c) => [c.label, c.score]))
  const ap = new Map(pr.map((c) => [c.label, c.score]))
  const th = 'px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-slate-500'
  const td = 'px-3 py-2 text-right tabular-nums'
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <caption className="sr-only">Métricas por categoría</caption>
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Categoría</th>
            <th scope="col" className={th}>Precision</th>
            <th scope="col" className={th}>Recall</th>
            <th scope="col" className={th}>F1</th>
            <th scope="col" className={th}>AUC</th>
            <th scope="col" className={th}>AP</th>
            <th scope="col" className={th}>Soporte</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {perClass.map((m) => (
            <tr key={m.label}>
              <th scope="row" className="px-3 py-2 text-left font-medium text-slate-800">
                <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CLASS_INFO[m.label].color }} aria-hidden />
                {CLASS_INFO[m.label].es}
              </th>
              <td className={td}>{num(m.precision)}</td>
              <td className={td}>{num(m.recall)}</td>
              <td className={td}>{num(m.f1)}</td>
              <td className={td}>{num(auc.get(m.label))}</td>
              <td className={td}>{num(ap.get(m.label))}</td>
              <td className={td}>{m.support}</td>
            </tr>
          ))}
        </tbody>
        <tfoot className="border-t-2 border-slate-200 bg-slate-50 font-medium">
          <tr>
            <th scope="row" className="px-3 py-2 text-left">Macro</th>
            <td className={td}>{num(macro.precision)}</td>
            <td className={td}>{num(macro.recall)}</td>
            <td className={td}>{num(macro.f1)}</td>
            <td className={td}>{num(aucMacro)}</td>
            <td className={td}>{num(apMacro)}</td>
            <td className={td}>{perClass.reduce((a, b) => a + b.support, 0)}</td>
          </tr>
          <tr>
            <th scope="row" className="px-3 py-2 text-left">Ponderado</th>
            <td className={td}>{num(weighted.precision)}</td>
            <td className={td}>{num(weighted.recall)}</td>
            <td className={td}>{num(weighted.f1)}</td>
            <td className={td}>—</td>
            <td className={td}>—</td>
            <td className={td}>—</td>
          </tr>
        </tfoot>
      </table>
      <p className="mt-2 text-xs text-slate-500">n/d: métrica no calculable porque la categoría no tiene ejemplos suficientes.</p>
    </div>
  )
}
