import axios from 'axios'
import type {
  BatchResponse,
  EvaluationResponse,
  Health,
  ModelInfo,
  PredictResponse,
} from '../types/api'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

const http = axios.create({ baseURL: API_BASE_URL, timeout: 60_000 })

export class ApiError extends Error {
  code: string
  status: number | undefined

  constructor(code: string, message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

/** Convierte cualquier error de red o de la API en un ApiError con mensaje en español. */
export function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) return err
  if (axios.isAxiosError(err)) {
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') {
      return new ApiError('timeout', 'La solicitud tardó demasiado. Intenta de nuevo con menos imágenes.')
    }
    if (!err.response) {
      return new ApiError(
        'network',
        'No se pudo conectar con el servidor. Verifica tu conexión o que el backend esté en ejecución.',
      )
    }
    const detail = (err.response.data as { detail?: { code?: string; message?: string } } | undefined)?.detail
    if (detail && typeof detail === 'object' && detail.message) {
      return new ApiError(detail.code ?? 'error', detail.message, err.response.status)
    }
    if (err.response.status === 413) {
      return new ApiError('file_too_large', 'Los archivos superan el tamaño permitido.', 413)
    }
    return new ApiError('error', `El servidor respondió con un error (HTTP ${err.response.status}).`, err.response.status)
  }
  return new ApiError('unknown', 'Ocurrió un error inesperado.')
}

async function call<T>(fn: () => Promise<{ data: T }>): Promise<T> {
  try {
    return (await fn()).data
  } catch (err) {
    throw toApiError(err)
  }
}

export const getHealth = (): Promise<Health> => call(() => http.get<Health>('/api/health', { timeout: 10_000 }))

export const getModelInfo = (): Promise<ModelInfo> => call(() => http.get<ModelInfo>('/api/model/info', { timeout: 10_000 }))

export function predictImage(file: File): Promise<PredictResponse> {
  const form = new FormData()
  form.append('file', file)
  return call(() => http.post<PredictResponse>('/api/predict', form))
}

export function predictBatch(files: File[]): Promise<BatchResponse> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return call(() => http.post<BatchResponse>('/api/predict/batch', form, { timeout: 300_000 }))
}

export function evaluateModel(
  files: File[],
  labelsCsv: File,
  onUploadProgress?: (fraction: number) => void,
): Promise<EvaluationResponse> {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  form.append('labels_csv', labelsCsv)
  return call(() =>
    http.post<EvaluationResponse>('/api/evaluate', form, {
      timeout: 900_000,
      onUploadProgress: (e) => {
        if (onUploadProgress && e.total) onUploadProgress(e.loaded / e.total)
      },
    }),
  )
}
