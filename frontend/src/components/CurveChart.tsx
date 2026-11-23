import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CLASS_INFO } from '../constants/classes'
import type { Curve } from '../types/api'
import { num } from '../utils/format'

interface Props {
  curves: Curve[]
  kind: 'roc' | 'pr'
}

export default function CurveChart({ curves, kind }: Props) {
  const valid = curves.filter((c) => c.x && c.y && c.score !== null)
  const missing = curves.filter((c) => !(c.x && c.y && c.score !== null))
  const scoreName = kind === 'roc' ? 'AUC' : 'AP'

  return (
    <div>
      <div className="h-96 w-full" role="img" aria-label={kind === 'roc' ? 'Curvas ROC uno contra el resto' : 'Curvas Precision-Recall'}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart margin={{ left: 16, right: 16, top: 8, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0, 1]}
              tickCount={6}
              allowDuplicatedCategory={false}
              label={{ value: kind === 'roc' ? 'Tasa de falsos positivos' : 'Recall', position: 'insideBottom', offset: -12, fontSize: 12 }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              domain={[0, 1]}
              tickCount={6}
              label={{ value: kind === 'roc' ? 'Tasa de verdaderos positivos' : 'Precision', angle: -90, position: 'insideLeft', fontSize: 12 }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip formatter={(v) => num(Number(v), 3)} labelFormatter={(v) => `x = ${num(Number(v), 3)}`} />
            <Legend verticalAlign="bottom" height={64} wrapperStyle={{ fontSize: 12, paddingTop: 16 }} />
            {kind === 'roc' && <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#94a3b8" strokeDasharray="5 5" />}
            {valid.map((c) => (
              <Line
                key={c.label}
                data={(c.x as number[]).map((x, i) => ({ x, y: (c.y as number[])[i] }))}
                dataKey="y"
                name={`${CLASS_INFO[c.label].es} (${scoreName} ${num(c.score, 3)})`}
                stroke={CLASS_INFO[c.label].color}
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {missing.length > 0 && (
        <ul className="mt-2 space-y-1 text-xs text-amber-800">
          {missing.map((c) => (
            <li key={c.label}>
              <strong>{CLASS_INFO[c.label].es}:</strong> {c.note ?? 'no calculable'}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
