import { BarChart3, Download, FileText, Play, RotateCcw, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import ConfusionMatrix from '../components/ConfusionMatrix'
import CurveChart from '../components/CurveChart'
import Dropzone from '../components/Dropzone'
import MetricsTable from '../components/MetricsTable'
import { Alert, Button, Card, EmptyState, PageHeader, Spinner, Stat } from '../components/ui'
import { CLASS_INFO, CLASS_NAMES } from '../constants/classes'
import { evaluateModel, type ApiError } from '../services/api'
import { useHealth } from '../services/HealthContext'
import type { EvaluationResponse } from '../types/api'
import { LABELS_TEMPLATE, downloadText, matchLabels, parseLabelsCsv, toCsv, type ParsedLabels } from '../utils/csv'
import { selectImages } from '../utils/files'
import { num, pct } from '../utils/format'

export function metricsToCsv(r: EvaluationResponse): string {
  const auc = new Map(r.roc.map((c) => [c.label, c.score]))
  const ap = new Map(r.pr.map((c) => [c.label, c.score]))
  const rows: Array<Record<string, unknown>> = r.per_class.map((m) => ({
    categoria: m.label,
    precision: m.precision ?? '',
    recall: m.recall ?? '',
    f1: m.f1 ?? '',
    auc: auc.get(m.label) ?? '',
    ap: ap.get(m.label) ?? '',
    soporte: m.support,
  }))
  rows.push({ categoria: 'macro', precision: r.macro.precision ?? '', recall: r.macro.recall ?? '', f1: r.macro.f1 ?? '', auc: r.auc_macro ?? '', ap: r.ap_macro ?? '', soporte: r.n_evaluated })
  rows.push({ categoria: 'ponderado', precision: r.weighted.precision ?? '', recall: r.weighted.recall ?? '', f1: r.weighted.f1 ?? '', auc: '', ap: '', soporte: r.n_evaluated })
  rows.push({ categoria: 'accuracy', f1: '', precision: '', recall: '', auc: '', ap: '', soporte: r.n_evaluated, exactitud: r.accuracy })
  return toCsv(['categoria', 'precision', 'recall', 'f1', 'auc', 'ap', 'soporte', 'exactitud'], rows)
}

export function predictionsToCsv(r: EvaluationResponse): string {
  const columns = ['filename', 'true_label', 'predicted_label', 'confidence', ...CLASS_NAMES.map((c) => `prob_${c}`)]
  const rows = r.rows.map((row) => {
    const out: Record<string, unknown> = {
      filename: row.filename,
      true_label: row.true_label,
      predicted_label: row.predicted_label,
      confidence: row.confidence.toFixed(6),
    }
    for (const c of CLASS_NAMES) out[`prob_${c}`] = (row.probabilities.find((p) => p.label === c)?.probability ?? 0).toFixed(6)
    return out
  })
  return toCsv(columns, rows)
}

export default function EvaluationPage() {
  const { limits, health } = useHealth()
  const [images, setImages] = useState<File[]>([])
  const [imageProblems, setImageProblems] = useState<string[]>([])
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [parsed, setParsed] = useState<ParsedLabels | null>(null)
  const [uploadFraction, setUploadFraction] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [result, setResult] = useState<EvaluationResponse | null>(null)

  useEffect(() => {
    if (!csvFile) return
    let cancelled = false
    csvFile.text().then((t) => {
      if (!cancelled) setParsed(parseLabelsCsv(t))
    })
    return () => {
      cancelled = true
    }
  }, [csvFile])

  const match = useMemo(
    () => (parsed ? matchLabels(images.map((f) => f.name), parsed.rows) : null),
    [images, parsed],
  )
  const modelDown = health !== null && !health.model_configured
  const canRun = !!csvFile && !!parsed && parsed.errors.length === 0 && !!match && match.matched > 0 && !modelDown

  const onImages = (picked: File[]) => {
    const { valid, errors } = selectImages(picked, limits, limits.max_eval_files, images)
    setImageProblems(errors)
    if (valid.length) {
      setImages((prev) => [...prev, ...valid])
      setResult(null)
      setError(null)
    }
  }

  const onCsv = (files: File[]) => {
    const f = files[0]
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.csv')) {
      setParsed({ rows: [], errors: ['El archivo de etiquetas debe ser un .csv.'] })
      setCsvFile(null)
      return
    }
    setCsvFile(f)
    setResult(null)
    setError(null)
  }

  const run = async () => {
    if (!csvFile) return
    // Solo se envían las imágenes que tienen etiqueta.
    const labelled = new Set(parsed?.rows.map((r) => r.filename))
    const toSend = images.filter((f) => labelled.has(f.name))
    setLoading(true)
    setUploadFraction(0)
    setError(null)
    setResult(null)
    try {
      setResult(await evaluateModel(toSend, csvFile, setUploadFraction))
    } catch (e) {
      setError(e as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setImages([])
    setImageProblems([])
    setCsvFile(null)
    setParsed(null)
    setResult(null)
    setError(null)
  }

  return (
    <>
      <PageHeader
        title="Evaluación del modelo"
        subtitle="Sube imágenes con su etiqueta real. El modelo las clasifica y se calculan precision, recall, F1, matriz de confusión, curvas ROC y AUC."
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="1. Imágenes etiquetadas" description={`Hasta ${limits.max_eval_files} imágenes de ${limits.max_image_mb} MB.`}>
          <div className="space-y-4">
            <Dropzone
              multiple
              accept={limits.allowed_extensions.join(',')}
              disabled={loading}
              title="Arrastra las imágenes o haz clic para elegirlas"
              hint="JPG, JPEG, PNG o WEBP. Los nombres de archivo deben coincidir con el CSV."
              onFiles={onImages}
            />
            {imageProblems.length > 0 && (
              <Alert kind="warning" title="Algunos archivos no se agregaron">
                <ul className="list-disc space-y-0.5 pl-4">
                  {imageProblems.slice(0, 5).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                  {imageProblems.length > 5 && <li>y {imageProblems.length - 5} más…</li>}
                </ul>
              </Alert>
            )}
            {images.length > 0 && (
              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span>{images.length} imágenes seleccionadas</span>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setImages([])}
                  className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-red-600 disabled:opacity-40"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden /> Quitar todas
                </button>
              </div>
            )}
          </div>
        </Card>

        <Card
          title="2. CSV de etiquetas"
          description="Columnas obligatorias: filename,true_label."
          actions={
            <Button variant="ghost" icon={<FileText className="h-4 w-4" />} onClick={() => downloadText('plantilla_etiquetas.csv', LABELS_TEMPLATE)}>
              Plantilla
            </Button>
          }
        >
          <div className="space-y-4">
            <Dropzone accept=".csv,text/csv" disabled={loading} title={csvFile ? `Cambiar CSV (${csvFile.name})` : 'Arrastra el CSV o haz clic para elegirlo'} hint={`UTF-8. Etiquetas válidas: ${CLASS_NAMES.join(', ')}.`} onFiles={onCsv} />
            {parsed && parsed.errors.length > 0 && (
              <Alert kind="error" title="Problemas en el CSV">
                <ul className="list-disc space-y-0.5 pl-4">
                  {parsed.errors.map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              </Alert>
            )}
            {parsed && match && parsed.errors.length === 0 && (
              <div className="grid grid-cols-3 gap-3">
                <Stat label="Filas del CSV" value={String(parsed.rows.length)} />
                <Stat label="Coinciden" value={String(match.matched)} />
                <Stat label="Sin etiqueta" value={String(match.imagesWithoutLabel.length)} hint="Se omiten" />
              </div>
            )}
            {parsed && match && match.labelsWithoutImage.length > 0 && (
              <Alert kind="warning">{match.labelsWithoutImage.length} fila(s) del CSV no tienen imagen y se omitirán.</Alert>
            )}
            {modelDown && <Alert kind="warning">El modelo no está configurado en el servidor.</Alert>}
            <div className="flex flex-wrap gap-2">
              <Button onClick={run} disabled={!canRun} loading={loading} icon={<Play className="h-4 w-4" />}>
                {loading ? 'Evaluando…' : 'Evaluar modelo'}
              </Button>
              {(images.length > 0 || csvFile || result) && (
                <Button variant="secondary" onClick={reset} disabled={loading} icon={<RotateCcw className="h-4 w-4" />}>
                  Limpiar
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>

      <div className="mt-6 space-y-6">
        {loading && (
          <Card>
            <Spinner
              label={
                uploadFraction < 1
                  ? `Subiendo imágenes… ${pct(uploadFraction, 0)}`
                  : 'El servidor está clasificando las imágenes. Puede tardar unos minutos.'
              }
            />
          </Card>
        )}
        {!loading && error && (
          <Alert kind="error" title="No se pudo completar la evaluación">
            {error.message}
          </Alert>
        )}
        {!loading && !error && !result && (
          <EmptyState icon={<BarChart3 className="h-6 w-6" />} title="Aún no hay resultados">
            Sube las imágenes y el CSV, y presiona “Evaluar modelo”.
          </EmptyState>
        )}

        {!loading && result && <Results result={result} />}
      </div>
    </>
  )
}

function Results({ result }: { result: EvaluationResponse }) {
  const downloads = (
    <div className="flex flex-wrap gap-2">
      <Button variant="secondary" icon={<Download className="h-4 w-4" />} onClick={() => downloadText('evaluacion_metricas.csv', metricsToCsv(result))}>
        Métricas (CSV)
      </Button>
      <Button variant="secondary" icon={<Download className="h-4 w-4" />} onClick={() => downloadText('evaluacion_predicciones.csv', predictionsToCsv(result))}>
        Predicciones (CSV)
      </Button>
      <Button
        variant="secondary"
        icon={<Download className="h-4 w-4" />}
        onClick={() => downloadText('evaluacion_completa.json', JSON.stringify(result, null, 2), 'application/json')}
      >
        Todo (JSON)
      </Button>
    </div>
  )
  return (
    <div className="space-y-6 animate-fade-in">
      <Card title="Resumen" actions={downloads} description={`Modelo: ${result.resolved_models.join(', ') || result.model_id} · ${result.n_evaluated} de ${result.n_requested} imágenes evaluadas`}>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <Stat label="Accuracy" value={pct(result.accuracy, 1)} />
          <Stat label="Precision macro" value={num(result.macro.precision)} />
          <Stat label="Recall macro" value={num(result.macro.recall)} />
          <Stat label="F1 macro" value={num(result.macro.f1)} />
          <Stat label="F1 ponderado" value={num(result.weighted.f1)} />
          <Stat label="AUC macro" value={num(result.auc_macro)} hint={result.auc_macro === null ? 'No calculable' : undefined} />
        </div>
        {result.auc_macro_note && <p className="mt-3 text-xs text-amber-800">{result.auc_macro_note}</p>}
      </Card>

      {result.warnings.length > 0 && (
        <Alert kind="warning" title="Advertencias">
          <ul className="list-disc space-y-0.5 pl-4">
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Alert>
      )}

      <Card title="Métricas por categoría">
        <MetricsTable perClass={result.per_class} macro={result.macro} weighted={result.weighted} roc={result.roc} pr={result.pr} aucMacro={result.auc_macro} apMacro={result.ap_macro} />
      </Card>

      <Card title="Matriz de confusión">
        <ConfusionMatrix labels={result.confusion_matrix.labels} matrix={result.confusion_matrix.matrix} />
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Curvas ROC (uno contra el resto)" description="Calculadas con las probabilidades por clase.">
          <CurveChart curves={result.roc} kind="roc" />
        </Card>
        <Card title="Curvas Precision-Recall" description="Útiles cuando las clases están desbalanceadas.">
          <CurveChart curves={result.pr} kind="pr" />
        </Card>
      </div>

      <Card title="Confusiones más frecuentes">
        {result.top_confusions.length === 0 ? (
          <p className="text-sm text-slate-500">No hubo confusiones entre categorías.</p>
        ) : (
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" className="px-3 py-2">Real</th>
                <th scope="col" className="px-3 py-2">Predicho</th>
                <th scope="col" className="px-3 py-2 text-right">Imágenes</th>
                <th scope="col" className="px-3 py-2 text-right">% de la clase real</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {result.top_confusions.slice(0, 8).map((c) => (
                <tr key={`${c.true}-${c.predicted}`}>
                  <td className="px-3 py-2">{CLASS_INFO[c.true].es}</td>
                  <td className="px-3 py-2">{CLASS_INFO[c.predicted].es}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{c.count}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{pct(c.share_of_true_class, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {(result.failed.length > 0 || result.unmatched_images.length > 0 || result.unmatched_labels.length > 0) && (
        <Card title="Archivos no incluidos en las métricas">
          <div className="space-y-3 text-sm">
            {result.failed.length > 0 && (
              <Alert kind="error" title={`${result.failed.length} imagen(es) fallaron`}>
                <ul className="list-disc space-y-0.5 pl-4">
                  {result.failed.map((f) => (
                    <li key={f.filename}>
                      <strong>{f.filename}:</strong> {f.error}
                    </li>
                  ))}
                </ul>
              </Alert>
            )}
            {result.unmatched_images.length > 0 && <p><strong>Sin etiqueta en el CSV:</strong> {result.unmatched_images.join(', ')}</p>}
            {result.unmatched_labels.length > 0 && <p><strong>Etiquetas sin imagen:</strong> {result.unmatched_labels.join(', ')}</p>}
          </div>
        </Card>
      )}
    </div>
  )
}
