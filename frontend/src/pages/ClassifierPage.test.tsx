import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../services/api'
import type { PredictResponse } from '../types/api'
import ClassifierPage from './ClassifierPage'

vi.mock('../services/api', async (orig) => {
  const actual = await orig<typeof import('../services/api')>()
  return { ...actual, predictImage: vi.fn(), getHealth: vi.fn().mockRejectedValue(new actual.ApiError('network', 'x')) }
})
import { predictImage } from '../services/api'
import { HealthProvider } from '../services/HealthContext'

const probs = (best: string, p: number) =>
  ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash'].map((label) => ({
    label: label as never,
    probability: label === best ? p : (1 - p) / 5,
  }))

const response = (best: string, p: number, low = false): PredictResponse => ({
  model_id: 'proyecto/1',
  latency_ms: 120,
  result: {
    filename: 'foto.jpg',
    predicted_label: best as never,
    confidence: p,
    low_confidence: low,
    probabilities: probs(best, p),
    estimated_probabilities: false,
    resolved_model: 'ws/modelo',
  },
})

function renderPage() {
  return render(
    <MemoryRouter>
      <HealthProvider>
        <ClassifierPage />
      </HealthProvider>
    </MemoryRouter>,
  )
}

const choose = (name: string, size = 1000) => {
  const input = screen.getByTestId('file-input') as HTMLInputElement
  fireEvent.change(input, { target: { files: [new File([new Uint8Array(size)], name, { type: 'image/jpeg' })] } })
}

describe('ClassifierPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('muestra estado vacío y el botón deshabilitado sin imagen', () => {
    renderPage()
    expect(screen.getByText('Aún no hay resultados')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Clasificar imagen/ })).toBeDisabled()
  })

  it('rechaza formatos inválidos sin llamar a la API', () => {
    renderPage()
    choose('documento.gif')
    expect(screen.getByRole('alert')).toHaveTextContent(/formato no permitido/)
    expect(predictImage).not.toHaveBeenCalled()
  })

  it('clasifica y muestra categoría, confianza y vista previa', async () => {
    vi.mocked(predictImage).mockResolvedValue(response('glass', 0.9))
    renderPage()
    choose('foto.jpg')
    expect(screen.getByAltText(/Vista previa de foto.jpg/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Clasificar imagen/ }))
    await waitFor(() => expect(screen.getByTestId('predicted-label')).toHaveTextContent('Vidrio'))
    expect(screen.getByTestId('confidence')).toHaveTextContent(/90,0/)
    expect(screen.queryByText('Confianza baja')).not.toBeInTheDocument()
  })

  it('avisa cuando la confianza es baja', async () => {
    vi.mocked(predictImage).mockResolvedValue(response('metal', 0.4, true))
    renderPage()
    choose('foto.jpg')
    fireEvent.click(screen.getByRole('button', { name: /Clasificar imagen/ }))
    await waitFor(() => expect(screen.getByText('Confianza baja')).toBeInTheDocument())
  })

  it('muestra el error sin bloquear la interfaz y permite reintentar', async () => {
    vi.mocked(predictImage).mockRejectedValueOnce(new ApiError('upstream_timeout', 'El modelo tardó demasiado en responder.'))
    renderPage()
    choose('foto.jpg')
    fireEvent.click(screen.getByRole('button', { name: /Clasificar imagen/ }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/tardó demasiado/))
    expect(screen.getByRole('button', { name: /Clasificar imagen/ })).toBeEnabled()
    vi.mocked(predictImage).mockResolvedValue(response('paper', 0.8))
    fireEvent.click(screen.getByRole('button', { name: /Clasificar imagen/ }))
    await waitFor(() => expect(screen.getByTestId('predicted-label')).toHaveTextContent('Papel'))
  })
})
