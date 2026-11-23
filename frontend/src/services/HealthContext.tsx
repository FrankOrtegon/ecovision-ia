import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { FALLBACK_LIMITS } from '../constants/defaults'
import type { Health, Limits } from '../types/api'
import { getHealth, type ApiError } from './api'

interface HealthState {
  health: Health | null
  error: ApiError | null
  loading: boolean
  limits: Limits
  refresh: () => void
}

const HealthContext = createContext<HealthState | null>(null)

export function HealthProvider({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(() => {
    setLoading(true)
    getHealth()
      .then((h) => {
        setHealth(h)
        setError(null)
      })
      .catch((e: ApiError) => {
        setHealth(null)
        setError(e)
      })
      .finally(() => setLoading(false))
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => refresh(), [refresh])

  const value = useMemo(
    () => ({ health, error, loading, limits: health?.limits ?? FALLBACK_LIMITS, refresh }),
    [health, error, loading, refresh],
  )
  return <HealthContext.Provider value={value}>{children}</HealthContext.Provider>
}

export function useHealth(): HealthState {
  const ctx = useContext(HealthContext)
  if (!ctx) throw new Error('useHealth debe usarse dentro de HealthProvider')
  return ctx
}
