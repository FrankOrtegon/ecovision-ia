import { ExternalLink } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Alert, Badge, Card, PageHeader, Spinner } from '../components/ui'
import { CLASS_INFO } from '../constants/classes'
import { getModelInfo, type ApiError } from '../services/api'
import type { ModelInfo } from '../types/api'
import { formatDate } from '../utils/format'

const PENDING = <span className="text-slate-400">Pendiente</span>

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-3 gap-2 border-b border-slate-100 py-2.5 text-sm last:border-0">
      <dt className="font-medium text-slate-500">{label}</dt>
      <dd className="col-span-2 break-words text-slate-800">{children}</dd>
    </div>
  )
}

function KeyValues({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data)
  if (!entries.length) return PENDING
  return (
    <ul className="space-y-1">
      {entries.map(([k, v]) => (
        <li key={k}>
          <span className="text-slate-500">{k}:</span> {typeof v === 'object' ? JSON.stringify(v) : String(v)}
        </li>
      ))}
    </ul>
  )
}

export default function ModelInfoPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null)
  const [error, setError] = useState<ApiError | null>(null)

  useEffect(() => {
    getModelInfo().then(setInfo).catch((e: ApiError) => setError(e))
  }, [])

  return (
    <>
      <PageHeader title="Acerca del modelo" subtitle="Datos de procedencia, entrenamiento y limitaciones. Solo se muestran valores registrados de ejecuciones reales." />
      {error && (
        <Alert kind="error" title="No se pudo cargar la información del modelo">
          {error.message}
        </Alert>
      )}
      {!info && !error && <Spinner label="Cargando información del modelo…" />}
      {info && (
        <div className="space-y-6">
          {info.status === 'pending_training' && (
            <Alert kind="warning" title="Entrenamiento pendiente de registrar">
              {info.notes ?? 'Aún no se han registrado los datos del entrenamiento.'}
            </Alert>
          )}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Modelo" actions={<Badge tone={info.status === 'ready' ? 'green' : 'amber'}>{info.status === 'ready' ? 'Listo' : 'Pendiente'}</Badge>}>
              <dl>
                <Row label="Nombre">{info.name}</Row>
                <Row label="Versión">{info.version ?? PENDING}</Row>
                <Row label="Identificador">{info.model_id ?? PENDING}</Row>
                <Row label="Arquitectura">{info.architecture ?? PENDING}</Row>
                <Row label="Plataforma">{info.platform}</Row>
                <Row label="Fecha de entrenamiento">{formatDate(info.trained_at)}</Row>
              </dl>
            </Card>
            <Card title="Dataset">
              <dl>
                <Row label="Origen">{info.dataset}</Row>
                <Row label="Enlace">
                  <a href={info.dataset_url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-green-700 underline">
                    Repositorio de TrashNet <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                  </a>
                </Row>
                <Row label="Categorías">
                  <div className="flex flex-wrap gap-1.5">
                    {info.classes.map((c) => (
                      <Badge key={c}>{CLASS_INFO[c].es}</Badge>
                    ))}
                  </div>
                </Row>
              </dl>
            </Card>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Configuración de entrenamiento">
              <KeyValues data={info.training_config} />
            </Card>
            <Card title="Métricas obtenidas">
              {info.metrics ? (
                <KeyValues data={info.metrics} />
              ) : (
                <p className="text-sm text-slate-500">
                  Aún no se han registrado métricas oficiales. Se publicarán después de evaluar el modelo sobre el conjunto de
                  prueba. Puedes calcularlas con tus propias imágenes en la sección Evaluación.
                </p>
              )}
            </Card>
          </div>
          <Card title="Limitaciones conocidas">
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700">
              {info.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </>
  )
}
