import type { Limits } from '../types/api'

export function extensionOf(name: string): string {
  const i = name.lastIndexOf('.')
  return i < 0 ? '' : name.slice(i).toLowerCase()
}

/** Valida formato y tamaño en el navegador. El backend vuelve a validar el contenido real. */
export function validateImage(file: File, limits: Limits): string | null {
  const ext = extensionOf(file.name)
  if (!limits.allowed_extensions.includes(ext)) {
    return `"${file.name}": formato no permitido. Usa JPG, JPEG, PNG o WEBP.`
  }
  if (file.size === 0) return `"${file.name}": el archivo está vacío.`
  if (file.size > limits.max_image_mb * 1024 * 1024) {
    return `"${file.name}": supera el tamaño máximo de ${limits.max_image_mb} MB.`
  }
  return null
}

export interface FileSelection {
  valid: File[]
  errors: string[]
}

/** Filtra archivos válidos, descarta duplicados por nombre y respeta el máximo de archivos. */
export function selectImages(files: File[], limits: Limits, maxCount: number, existing: File[] = []): FileSelection {
  const valid: File[] = []
  const errors: string[] = []
  const names = new Set(existing.map((f) => f.name))
  for (const f of files) {
    const err = validateImage(f, limits)
    if (err) {
      errors.push(err)
    } else if (names.has(f.name)) {
      errors.push(`"${f.name}": ya está en la lista (los nombres no pueden repetirse).`)
    } else if (existing.length + valid.length >= maxCount) {
      errors.push(`"${f.name}": se superó el máximo de ${maxCount} imágenes.`)
    } else {
      names.add(f.name)
      valid.push(f)
    }
  }
  return { valid, errors }
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}
