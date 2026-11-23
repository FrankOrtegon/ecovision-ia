import { ImageOff, RotateCcw, ScanSearch } from 'lucide-react'
import { useEffect, useState } from 'react'
import Dropzone from '../components/Dropzone'
import ProbabilityBars from '../components/ProbabilityBars'
import { Alert, Badge, Button, Card, EmptyState, PageHeader, Spinner } from '../components/ui'
import { CLASS_INFO } from '../constants/classes'
import { predictImage, type ApiError } from '../services/api'
import { useHealth } from '../services/HealthContext'
import type { PredictResponse } from '../types/api'
import { formatBytes, validateImage } from '../utils/files'
import { pct } from '../utils/format'

export default function ClassifierPage() {
  const { limits, health } = useHealth()
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [response, setResponse] = useState<PredictResponse | null>(null)

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const reset = () => {
    setFile(null)
    setPreviewUrl(null)
    setFileError(null)
    setError(null)
    setResponse(null)
  }

  const onFiles = (files: File[]) => {
    const f = files[0]
    if (!f) return
    setResponse(null)
    setError(null)
    const err = validateImage(f, limits)
    if (err) {
      setFileError(err)
      setFile(null)
      setPreviewUrl(null)
      return
    }
    setFileError(null)
    setFile(f)
  }

  const classify = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      setResponse(await predictImage(file))
    } catch (e) {
      setError(e as ApiError)
    } finally {
      setLoading(false)
    }
  }

  const result = response?.result
  const modelDown = health !== null && !health.model_configured

  return (
    <>
      <PageHeader
        title="Clasificador individual"
        subtitle="Carga una imagen y el modelo indicará la categoría del material aparente con la probabilidad de cada clase."
      />
      {modelDown && (
        <div className="mb-4">
          <Alert kind="warning" title="El modelo no está configurado en el servidor">
            Puedes preparar la imagen, pero la clasificación no estará disponible hasta que el servidor tenga sus credenciales.
          </Alert>
        </div>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="1. Imagen" description={`JPG, JPEG, PNG o WEBP. Máximo ${limits.max_image_mb} MB.`}>
          <div className="space-y-4">
            <Dropzone
              accept={limits.allowed_extensions.join(',')}
              disabled={loading}
              title={file ? 'Cambiar imagen' : 'Arrastra una imagen o haz clic para elegirla'}
              hint="Una foto con el objeto bien visible y fondo claro suele funcionar mejor."
              onFiles={onFiles}
            />
            {fileError && <Alert kind="error">{fileError}</Alert>}
            {file && previewUrl && (
              <div className="animate-fade-in">
                <img src={previewUrl} alt={`Vista previa de ${file.name}`} className="max-h-72 w-full rounded-lg border border-slate-200 bg-slate-100 object-contain" />
                <p className="mt-2 truncate text-xs text-slate-500">
                  {file.name} · {formatBytes(file.size)}
                </p>
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button onClick={classify} disabled={!file || modelDown} loading={loading} icon={<ScanSearch className="h-4 w-4" />}>
                {loading ? 'Clasificando…' : 'Clasificar imagen'}
              </Button>
              {(file || response || error) && (
                <Button variant="secondary" onClick={reset} disabled={loading} icon={<RotateCcw className="h-4 w-4" />}>
                  Limpiar
                </Button>
              )}
            </div>
          </div>
        </Card>

        <Card title="2. Resultado">
          {loading && <Spinner label="Consultando el modelo…" />}
          {!loading && error && (
            <Alert kind="error" title="No se pudo clasificar la imagen">
              {error.message}
            </Alert>
          )}
          {!loading && !error && !result && (
            <EmptyState icon={<ImageOff className="h-6 w-6" />} title="Aún no hay resultados">
              Elige una imagen y presiona “Clasificar imagen”.
            </EmptyState>
          )}
          {!loading && result && (
            <div className="space-y-4 animate-fade-in">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Categoría predicha</p>
                  <p data-testid="predicted-label" className="mt-1 flex items-center gap-2 text-3xl font-bold text-slate-900">
                    <span className="h-4 w-4 rounded-full" style={{ backgroundColor: CLASS_INFO[result.predicted_label].color }} aria-hidden />
                    {CLASS_INFO[result.predicted_label].es}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Confianza</p>
                  <p data-testid="confidence" className="mt-1 text-3xl font-bold text-green-700">{pct(result.confidence, 1)}</p>
                </div>
              </div>

              {result.low_confidence && (
                <Alert kind="warning" title="Confianza baja">
                  La probabilidad más alta es menor que {pct(limits.low_confidence_threshold, 0)}. El modelo no está seguro:
                  prueba con otra foto, con mejor luz y fondo claro, y no tomes esta predicción como definitiva.
                </Alert>
              )}

              <ProbabilityBars probabilities={result.probabilities} predicted={result.predicted_label} />

              {result.estimated_probabilities && (
                <p className="text-xs text-slate-500">
                  El proveedor del modelo no informa las clases con menos de ~1 % de probabilidad. Esos valores son una estimación
                  que reparte la probabilidad restante.
                </p>
              )}
              <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-3 text-xs">
                <Badge>Tiempo: {response?.latency_ms} ms</Badge>
                {result.resolved_model && <Badge>Modelo: {result.resolved_model}</Badge>}
              </div>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
