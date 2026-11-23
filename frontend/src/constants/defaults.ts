import type { Limits } from '../types/api'

/** Valores de respaldo si el backend no responde. Los valores reales vienen de /api/health. */
export const FALLBACK_LIMITS: Limits = {
  max_image_mb: 5,
  max_batch_files: 20,
  max_eval_files: 500,
  low_confidence_threshold: 0.6,
  allowed_extensions: ['.jpeg', '.jpg', '.png', '.webp'],
}
