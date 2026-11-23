import type { ClassName } from '../types/api'

export const CLASS_NAMES: readonly ClassName[] = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

export interface ClassInfo {
  es: string
  en: string
  description: string
  color: string
}

export const CLASS_INFO: Record<ClassName, ClassInfo> = {
  cardboard: {
    es: 'Cartón',
    en: 'Cardboard',
    description: 'Cajas, empaques y láminas de cartón corrugado.',
    color: '#92400e',
  },
  glass: {
    es: 'Vidrio',
    en: 'Glass',
    description: 'Botellas, frascos y otros envases de vidrio.',
    color: '#0891b2',
  },
  metal: {
    es: 'Metal',
    en: 'Metal',
    description: 'Latas, tapas y objetos metálicos.',
    color: '#64748b',
  },
  paper: {
    es: 'Papel',
    en: 'Paper',
    description: 'Hojas, periódicos, volantes y papel en general.',
    color: '#d97706',
  },
  plastic: {
    es: 'Plástico',
    en: 'Plastic',
    description: 'Botellas, envases, bolsas y recipientes de plástico.',
    color: '#2563eb',
  },
  trash: {
    es: 'Otros residuos',
    en: 'Trash',
    description: 'Objetos que no encajan en las demás categorías, como envolturas, servilletas o espuma.',
    color: '#7c3aed',
  },
}

export const classLabel = (c: ClassName): string => CLASS_INFO[c].es
