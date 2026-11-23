/** Contratos de la API del backend (espejo de backend/app/schemas/models.py). */

export type ClassName = 'cardboard' | 'glass' | 'metal' | 'paper' | 'plastic' | 'trash'

export interface Limits {
  max_image_mb: number
  max_batch_files: number
  max_eval_files: number
  low_confidence_threshold: number
  allowed_extensions: string[]
}

export interface Health {
  status: 'ok' | 'degraded'
  version: string
  environment: string
  model_configured: boolean
  limits: Limits
}

export interface ClassProbability {
  label: ClassName
  probability: number
}

export interface PredictionResult {
  filename: string
  predicted_label: ClassName
  confidence: number
  low_confidence: boolean
  probabilities: ClassProbability[]
  estimated_probabilities: boolean
  resolved_model: string | null
}

export interface PredictResponse {
  result: PredictionResult
  model_id: string
  latency_ms: number
}

export interface BatchItem {
  filename: string
  status: 'ok' | 'error'
  result: PredictionResult | null
  error: string | null
  error_code: string | null
}

export interface BatchResponse {
  items: BatchItem[]
  total: number
  succeeded: number
  failed: number
  model_id: string
  latency_ms: number
}

export interface ModelInfo {
  status: 'ready' | 'pending_training'
  name: string
  version: string | null
  model_id: string | null
  dataset: string
  dataset_url: string
  platform: string
  architecture: string | null
  classes: ClassName[]
  training_config: Record<string, unknown>
  trained_at: string | null
  metrics: Record<string, unknown> | null
  limitations: string[]
  notes: string | null
}

export interface PerClassMetrics {
  label: ClassName
  support: number
  predicted: number
  precision: number | null
  recall: number | null
  f1: number | null
}

export interface AveragedMetrics {
  precision: number | null
  recall: number | null
  f1: number | null
}

export interface Curve {
  label: ClassName
  x: number[] | null
  y: number[] | null
  score: number | null
  note: string | null
}

export interface Confusion {
  true: ClassName
  predicted: ClassName
  count: number
  share_of_true_class: number
}

export interface EvaluationRow {
  filename: string
  true_label: ClassName
  predicted_label: ClassName
  confidence: number
  probabilities: ClassProbability[]
}

export interface EvaluationResponse {
  model_id: string
  resolved_models: string[]
  n_requested: number
  n_evaluated: number
  n_estimated_probabilities: number
  accuracy: number
  per_class: PerClassMetrics[]
  macro: AveragedMetrics
  weighted: AveragedMetrics
  confusion_matrix: { labels: ClassName[]; matrix: number[][] }
  roc: Curve[]
  auc_macro: number | null
  auc_macro_note: string | null
  pr: Curve[]
  ap_macro: number | null
  top_confusions: Confusion[]
  rows: EvaluationRow[]
  failed: BatchItem[]
  unmatched_images: string[]
  unmatched_labels: string[]
  warnings: string[]
}
