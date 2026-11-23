import { AxiosError, type AxiosResponse } from 'axios'
import { describe, expect, it } from 'vitest'
import { ApiError, toApiError } from './api'

const withResponse = (status: number, data: unknown) => {
  const err = new AxiosError('fallo', 'ERR_BAD_REQUEST')
  err.response = { status, data } as AxiosResponse
  return err
}

describe('toApiError', () => {
  it('usa el código y mensaje uniformes del backend', () => {
    const e = toApiError(withResponse(422, { detail: { code: 'bad_csv', message: 'CSV inválido' } }))
    expect(e).toBeInstanceOf(ApiError)
    expect(e.code).toBe('bad_csv')
    expect(e.message).toBe('CSV inválido')
    expect(e.status).toBe(422)
  })
  it('traduce errores de red', () => {
    const e = toApiError(new AxiosError('Network Error', 'ERR_NETWORK'))
    expect(e.code).toBe('network')
    expect(e.message).toMatch(/No se pudo conectar/)
  })
  it('traduce el tiempo de espera agotado', () => {
    expect(toApiError(new AxiosError('timeout', 'ECONNABORTED')).code).toBe('timeout')
  })
  it('maneja respuestas sin el formato esperado', () => {
    expect(toApiError(withResponse(413, '<html>')).code).toBe('file_too_large')
    expect(toApiError(withResponse(500, null)).message).toMatch(/HTTP 500/)
  })
  it('maneja errores desconocidos', () => {
    expect(toApiError('algo').code).toBe('unknown')
  })
})
