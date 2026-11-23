import { describe, expect, it } from 'vitest'
import { FALLBACK_LIMITS } from '../constants/defaults'
import { LABELS_TEMPLATE, matchLabels, parseLabelsCsv, toCsv } from './csv'
import { selectImages, validateImage } from './files'
import { formatDate, num, pct } from './format'

const file = (name: string, size = 1000) => new File([new Uint8Array(size)], name, { type: 'image/jpeg' })

describe('validateImage', () => {
  it('acepta JPG, JPEG, PNG y WEBP sin importar mayúsculas', () => {
    for (const n of ['a.jpg', 'a.JPEG', 'a.png', 'a.WebP']) expect(validateImage(file(n), FALLBACK_LIMITS)).toBeNull()
  })
  it('rechaza formatos no permitidos', () => {
    expect(validateImage(file('a.gif'), FALLBACK_LIMITS)).toMatch(/formato no permitido/)
    expect(validateImage(file('sin_extension'), FALLBACK_LIMITS)).toMatch(/formato no permitido/)
  })
  it('rechaza archivos vacíos y demasiado grandes', () => {
    expect(validateImage(file('a.jpg', 0), FALLBACK_LIMITS)).toMatch(/vacío/)
    expect(validateImage(file('a.jpg', 5 * 1024 * 1024 + 1), FALLBACK_LIMITS)).toMatch(/5 MB/)
  })
})

describe('selectImages', () => {
  it('descarta duplicados y respeta el máximo', () => {
    const existing = [file('a.jpg')]
    const { valid, errors } = selectImages([file('a.jpg'), file('b.jpg'), file('c.jpg')], FALLBACK_LIMITS, 2, existing)
    expect(valid.map((f) => f.name)).toEqual(['b.jpg'])
    expect(errors).toHaveLength(2)
    expect(errors[0]).toMatch(/ya está/)
    expect(errors[1]).toMatch(/máximo de 2/)
  })
})

describe('toCsv', () => {
  it('escapa comillas, comas y saltos de línea', () => {
    expect(toCsv(['a', 'b'], [{ a: 'x,y', b: 'di "hola"' }])).toBe('a,b\n"x,y","di ""hola"""\n')
  })
  it('neutraliza fórmulas de hoja de cálculo', () => {
    const out = toCsv(['f'], [{ f: '=HYPERLINK("x")' }, { f: '+1' }, { f: '@a' }, { f: '-2' }])
    expect(out).not.toMatch(/^=/m)
    expect(out.split('\n')[1]).toMatch(/^"'=/)
  })
})

describe('parseLabelsCsv', () => {
  it('lee la plantilla', () => {
    const r = parseLabelsCsv(LABELS_TEMPLATE)
    expect(r.errors).toEqual([])
    expect(r.rows).toEqual([
      { filename: 'ejemplo_1.jpg', true_label: 'glass' },
      { filename: 'ejemplo_2.jpg', true_label: 'plastic' },
    ])
  })
  it('exige la cabecera', () => {
    expect(parseLabelsCsv('nombre,clase\na.jpg,glass\n').errors[0]).toMatch(/cabecera/)
  })
  it('reporta etiquetas inválidas y nombres repetidos', () => {
    const r = parseLabelsCsv('filename,true_label\na.jpg,vidrio\nb.jpg,glass\nb.jpg,metal\n')
    expect(r.errors.join(' ')).toMatch(/vidrio/)
    expect(r.errors.join(' ')).toMatch(/repetido/)
  })
  it('acepta BOM, mayúsculas y comillas', () => {
    const r = parseLabelsCsv('\ufeffFilename,True_Label\r\n"a,1.jpg",GLASS\r\n')
    expect(r.errors).toEqual([])
    expect(r.rows[0]).toEqual({ filename: 'a,1.jpg', true_label: 'glass' })
  })
  it('avisa si no hay filas', () => {
    expect(parseLabelsCsv('filename,true_label\n').errors[0]).toMatch(/no tiene filas/)
  })
})

describe('matchLabels', () => {
  it('relaciona imágenes con etiquetas', () => {
    const rows = [
      { filename: 'a.jpg', true_label: 'glass' as const },
      { filename: 'z.jpg', true_label: 'metal' as const },
    ]
    expect(matchLabels(['a.jpg', 'b.jpg'], rows)).toEqual({
      matched: 1,
      imagesWithoutLabel: ['b.jpg'],
      labelsWithoutImage: ['z.jpg'],
    })
  })
})

describe('format', () => {
  it('muestra n/d para valores no calculables', () => {
    expect(pct(null)).toBe('n/d')
    expect(num(undefined)).toBe('n/d')
  })
  it('formatea porcentajes en español', () => {
    expect(pct(0.7854, 1)).toMatch(/78,5/)
  })
  it('formatea fechas y pendientes', () => {
    expect(formatDate(null)).toBe('Pendiente')
    expect(formatDate('2026-11-22')).toMatch(/2026/)
  })
})
