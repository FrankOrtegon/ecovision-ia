import { Download, FileStack, Play, RotateCcw, Trash2 } from 'lucide-react'
import { useState } from 'react'
import Dropzone from '../components/Dropzone'
import { Alert, Badge, Button, Card, EmptyState, PageHeader, Spinner, Stat } from '../components/ui'
import { CLASS_INFO, CLASS_NAMES } from '../constants/classes'
import { predictBatch, type ApiError } from '../services/api'
import { useHealth } from '../services/HealthContext'
import type { BatchResponse } from '../types/api'
import { downloadText, toCsv } from '../utils/csv'
import { formatBytes, selectImages } from '../utils/files'
import { pct } from '../utils/format'

export function batchToCsv(r: BatchResponse): string {
  const columns = ['filename', 'status', 'predicted_label', 'confidence', ...CLASS_NAMES.map((c) => `prob_${c}`), 'error']
  const rows = r.items.map((it) => {
    const row: Record<string, unknown> = {
      filename: it.filename,
      status: it.status === 'ok' ? 'ok' : 'error',
      predicted_label: it.result?.predicted_label ?? '',
      confidence: it.result ? it.result.confidence.toFixed(6) : '',
      error: it.error ?? '',
    }
    for (const c of CLASS_NAMES) {
      row[`prob_${c}`] = it.result ? (it.result.probabilities.find((p) => p.label === c)?.probability ?? 0).toFixed(6) : ''
    }
    return row
  })
  return toCsv(columns, rows)
}

export default function BatchPage() {
  const { limits, health } = useHealth()
  const [files, setFiles] = useState<File[]>([])
  const [problems, setProblems] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [response, setResponse] = useState<BatchResponse | null>(null)

  const onFiles = (picked: File[]) => {
    const { valid, errors } = selectImages(picked, limits, limits.max_batch_files, files)
    setProblems(errors)
    if (valid.length) {
      setFiles((prev) => [...prev, ...valid])
      setResponse(null)
      setError(null)
    }
  }

  const run = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      setResponse(await predictBatch(files))
    } catch (e) {
      setError(e as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFiles([])
    setProblems([])
    setResponse(null)
    setError(null)
  }

  const failedItems = response?.items.filter((i) => i.status === 'error') ?? []
  const modelDown = health !== null && !health.model_configured

  return (
    <>
      <PageHeader
        title="Procesamiento por lotes"
        subtitle={`Clasifica hasta ${limits.max_batch_files} imágenes a la vez y exporta los resultados a CSV.`}
      />
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2" title="1. Imágenes" description={`Máximo ${limits.max_batch_files} imágenes de ${limits.max_image_mb} MB.`}>
          <div className="space-y-4">
            <Dropzone
              multiple
              accept={limits.allowed_extensions.join(',')}
              disabled={loading}
              title="Arrastra imágenes o haz clic para elegirlas"
              hint="JPG, JPEG, PNG o WEBP"
              onFiles={onFiles}
            />
            {problems.length > 0 && (
              <Alert kind="warning" title="Algunos archivos no se agregaron">
                <ul className="list-disc space-y-0.5 pl-4">
                  {problems.slice(0, 6).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                  {problems.length > 6 && <li>y {problems.length - 6} más…</li>}
                </ul>
              </Alert>
            )}
            {files.length > 0 && (
              <ul className="max-h-64 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200 text-sm">
                {files.map((f) => (
                  <li key={f.name} className="flex items-center justify-between gap-2 px-3 py-2">
                    <span className="truncate" title={f.name}>
                      {f.name} <span className="text-xs text-slate-400">· {formatBytes(f.size)}</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setFiles((prev) => prev.filter((x) => x.name !== f.name))}
                      disabled={loading}
                      aria-label={`Quitar ${f.name}`}
                      className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-red-600 disabled:opacity-40"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex flex-wrap gap-2">
              <Button onClick={run} disabled={files.length === 0 || modelDown} loading={loading} icon={<Play className="h-4 w-4" />}>
                {loading ? 'Procesando…' : `Clasificar ${files.length || ''} imágenes`.replace('  ', ' ')}
              </Button>
              {(files.length > 0 || response) && (
                <Button variant="secondary" onClick={reset} disabled={loading} icon={<RotateCcw className="h-4 w-4" />}>
                  Limpiar
                </Button>
              )}
            </div>
            {modelDown && <Alert kind="warning">El modelo no está configurado en el servidor.</Alert>}
          </div>
        </Card>

        <Card
          className="lg:col-span-3"
          title="2. Resultados"
          actions={
            response && (
              <Button
                variant="secondary"
                icon={<Download className="h-4 w-4" />}
                onClick={() => downloadText('ecovision_lote.csv', batchToCsv(response))}
              >
                Exportar CSV
              </Button>
            )
          }
        >
          {loading && <Spinner label={`Procesando ${files.length} imágenes en el servidor…`} />}
          {!loading && error && (
            <Alert kind="error" title="No se pudo procesar el lote">
              {error.message}
            </Alert>
          )}
          {!loading && !error && !response && (
            <EmptyState icon={<FileStack className="h-6 w-6" />} title="Aún no hay resultados">
              Agrega imágenes y presiona “Clasificar”.
            </EmptyState>
          )}
          {!loading && response && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-3 gap-3">
                <Stat label="Total" value={String(response.total)} />
                <Stat label="Correctas" value={String(response.succeeded)} />
                <Stat label="Fallidas" value={String(response.failed)} />
              </div>
              {failedItems.length > 0 && (
                <Alert kind="error" title={`${failedItems.length} archivo(s) fallaron`}>
                  <ul className="list-disc space-y-0.5 pl-4">
                    {failedItems.map((i) => (
                      <li key={i.filename}>
                        <strong>{i.filename}:</strong> {i.error}
                      </li>
                    ))}
                  </ul>
                </Alert>
              )}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th scope="col" className="px-3 py-2">Archivo</th>
                      <th scope="col" className="px-3 py-2">Categoría</th>
                      <th scope="col" className="px-3 py-2 text-right">Confianza</th>
                      <th scope="col" className="px-3 py-2">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {response.items.map((it) => (
                      <tr key={it.filename} className={it.status === 'error' ? 'bg-red-50/50' : ''}>
                        <td className="max-w-48 truncate px-3 py-2" title={it.filename}>{it.filename}</td>
                        <td className="px-3 py-2">
                          {it.result ? (
                            <span className="inline-flex items-center gap-2">
                              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CLASS_INFO[it.result.predicted_label].color }} aria-hidden />
                              {CLASS_INFO[it.result.predicted_label].es}
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums">{it.result ? pct(it.result.confidence, 1) : '—'}</td>
                        <td className="px-3 py-2">
                          {it.status === 'error' ? (
                            <Badge tone="red">Error</Badge>
                          ) : it.result?.low_confidence ? (
                            <Badge tone="amber">Confianza baja</Badge>
                          ) : (
                            <Badge tone="green">Correcto</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-500">Tiempo total: {response.latency_ms} ms · Modelo: {response.model_id}</p>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
