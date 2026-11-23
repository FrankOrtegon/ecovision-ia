import { UploadCloud } from 'lucide-react'
import { useRef, useState, type DragEvent, type KeyboardEvent } from 'react'

interface Props {
  accept: string
  multiple?: boolean
  disabled?: boolean
  title: string
  hint: string
  onFiles: (files: File[]) => void
}

export default function Dropzone({ accept, multiple = false, disabled = false, title, hint, onFiles }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)

  const pick = (list: FileList | null) => {
    if (list && list.length) onFiles(Array.from(list))
    if (input.current) input.current.value = '' // permite volver a elegir el mismo archivo
  }
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setOver(false)
    if (!disabled) pick(e.dataTransfer.files)
  }
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      input.current?.click()
    }
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      aria-label={title}
      onClick={() => !disabled && input.current?.click()}
      onKeyDown={onKey}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 ${
        disabled ? 'cursor-not-allowed border-slate-200 bg-slate-50 opacity-60' : over ? 'border-green-500 bg-green-50' : 'border-slate-300 bg-white hover:border-green-400 hover:bg-green-50/40'
      }`}
    >
      <UploadCloud className="mb-2 h-8 w-8 text-green-600" aria-hidden />
      <p className="text-sm font-medium text-slate-800">{title}</p>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
      <input
        ref={input}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        data-testid="file-input"
        onChange={(e) => pick(e.target.files)}
        tabIndex={-1}
      />
    </div>
  )
}
