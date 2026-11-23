import { Link } from 'react-router-dom'
import { PageHeader } from '../components/ui'

export default function NotFoundPage() {
  return (
    <>
      <PageHeader title="Página no encontrada" subtitle="La dirección que buscas no existe." />
      <Link to="/" className="text-sm font-medium text-green-700 underline">
        Volver al inicio
      </Link>
    </>
  )
}
