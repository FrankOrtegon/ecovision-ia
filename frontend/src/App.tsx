import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'

// Las páginas con gráficos se cargan bajo demanda para reducir el tamaño inicial.
const ClassifierPage = lazy(() => import('./pages/ClassifierPage'))
const BatchPage = lazy(() => import('./pages/BatchPage'))
const EvaluationPage = lazy(() => import('./pages/EvaluationPage'))
const ModelInfoPage = lazy(() => import('./pages/ModelInfoPage'))

export default function App() {
  return (
    <Suspense fallback={<div className="p-8"><Spinner label="Cargando…" /></div>}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="clasificador" element={<ClassifierPage />} />
          <Route path="lotes" element={<BatchPage />} />
          <Route path="evaluacion" element={<EvaluationPage />} />
          <Route path="modelo" element={<ModelInfoPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
