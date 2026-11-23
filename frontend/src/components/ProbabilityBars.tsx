import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CLASS_INFO } from '../constants/classes'
import type { ClassProbability, ClassName } from '../types/api'
import { pct } from '../utils/format'

export default function ProbabilityBars({ probabilities, predicted }: { probabilities: ClassProbability[]; predicted: ClassName }) {
  const data = [...probabilities]
    .sort((a, b) => b.probability - a.probability)
    .map((p) => ({ name: CLASS_INFO[p.label].es, value: p.probability, label: p.label }))

  return (
    <div>
      <div className="h-64 w-full" role="img" aria-label={`Probabilidades por categoría. Mayor: ${CLASS_INFO[predicted].es}`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
            <XAxis type="number" domain={[0, 1]} tickFormatter={(v: number) => pct(v, 0)} tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 13 }} />
            <Tooltip formatter={(v) => pct(Number(v), 2)} cursor={{ fill: '#f1f5f9' }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false}>
              {data.map((d) => (
                <Cell key={d.label} fill={d.label === predicted ? '#16a34a' : '#cbd5e1'} />
              ))}
              <LabelList dataKey="value" position="right" formatter={(v) => pct(Number(v), 1)} style={{ fontSize: 12, fill: '#334155' }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>Probabilidades por categoría</caption>
        <tbody>
          {data.map((d) => (
            <tr key={d.label}>
              <th scope="row">{d.name}</th>
              <td>{pct(d.value, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
