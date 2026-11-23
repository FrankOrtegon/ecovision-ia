import { ArrowRight, Cpu, ImageUp, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Alert, Card } from '../components/ui'
import { CLASS_INFO, CLASS_NAMES } from '../constants/classes'

const STEPS = [
  { icon: ImageUp, title: '1. Carga una imagen', text: 'Sube una foto JPG, PNG o WEBP del residuo. Se valida en tu navegador y de nuevo en el servidor.' },
  { icon: Cpu, title: '2. El modelo la analiza', text: 'El backend envía la imagen al modelo de visión por computador alojado en Roboflow. Tu clave nunca llega al navegador.' },
  { icon: Target, title: '3. Revisa la predicción', text: 'Obtienes la categoría del material aparente y la probabilidad de cada una de las seis clases.' },
]

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="animate-fade-in overflow-hidden rounded-2xl bg-gradient-to-br from-green-700 to-green-500 p-8 text-white shadow-sm sm:p-10">
        <p className="text-sm font-medium text-green-100">Visión por computador aplicada a la gestión ambiental</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">EcoVision IA</h1>
        <p className="mt-3 max-w-2xl text-green-50">
          Sistema inteligente de clasificación de residuos. Identifica el tipo de material aparente de una imagen entre seis
          categorías y muestra qué tan seguro está el modelo.
        </p>
        <Link
          to="/clasificador"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-green-700 shadow-sm transition-colors hover:bg-green-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        >
          Ir al clasificador <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Contexto">
          <p className="text-sm leading-relaxed text-slate-600">
            Las instituciones educativas y las organizaciones con programas de gestión ambiental necesitan separar bien los
            materiales para poder aprovecharlos. Identificar mal un material dificulta esa separación. Esta aplicación está
            pensada para estudiantes, docentes, personal administrativo y responsables de sostenibilidad.
          </p>
        </Card>
        <Card title="Objetivo">
          <p className="text-sm leading-relaxed text-slate-600">
            Clasificar imágenes de residuos con un modelo entrenado sobre el dataset público TrashNet, ofrecer la clasificación
            individual y por lotes, y medir el rendimiento del modelo con imágenes etiquetadas mediante precision, recall,
            F1, matriz de confusión, curvas ROC y AUC.
          </p>
        </Card>
      </div>

      <Alert kind="info" title="Alcance del sistema">
        EcoVision IA clasifica el <strong>material aparente</strong> según las categorías que aprendió. No determina si un
        residuo es reciclable ni cómo debe desecharse.
      </Alert>

      <section aria-labelledby="categorias">
        <h2 id="categorias" className="mb-3 text-lg font-semibold text-slate-900">
          Las seis categorías
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CLASS_NAMES.map((c) => (
            <li key={c} className="animate-fade-in rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: CLASS_INFO[c].color }} aria-hidden />
                <h3 className="font-semibold text-slate-900">{CLASS_INFO[c].es}</h3>
                <span className="text-xs text-slate-400">{CLASS_INFO[c].en}</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">{CLASS_INFO[c].description}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="como-funciona">
        <h2 id="como-funciona" className="mb-3 text-lg font-semibold text-slate-900">
          Cómo funciona
        </h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, text }) => (
            <li key={title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-3 inline-flex rounded-lg bg-green-50 p-2 text-green-600">
                <Icon className="h-5 w-5" aria-hidden />
              </div>
              <h3 className="font-semibold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
