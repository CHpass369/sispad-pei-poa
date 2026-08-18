/**
 * Catálogos de la formulación POA.
 *
 * La categoría programática del clasificador presupuestario se compone de
 * tres segmentos —programa, proyecto y actividad— y se expresa concatenada:
 * `101 0 023`.
 */

export interface CategoriaProgramatica {
  programa: string;
  proyecto: string;
  actividad: string;
}

/** Anchos oficiales de cada segmento. */
export const ANCHO_PROGRAMA = 3;
export const ANCHO_PROYECTO = 1;
export const ANCHO_ACTIVIDAD = 3;

/**
 * Combinaciones de referencia aportadas por la entidad. NO son un catálogo
 * cerrado: sirven de atajo, y cualquier otra combinación válida se captura
 * a mano.
 */
export const CATEGORIAS_REFERENCIA: CategoriaProgramatica[] = [
  { programa: '000', proyecto: '0', actividad: '000' },
  { programa: '000', proyecto: '0', actividad: '001' },
  { programa: '001', proyecto: '0', actividad: '000' },
  { programa: '001', proyecto: '0', actividad: '001' },
  { programa: '097', proyecto: '0', actividad: '000' },
  { programa: '097', proyecto: '0', actividad: '001' },
  { programa: '097', proyecto: '0', actividad: '100' },
  { programa: '099', proyecto: '0', actividad: '000' },
  { programa: '099', proyecto: '0', actividad: '001' },
  { programa: '099', proyecto: '0', actividad: '002' },
  { programa: '100', proyecto: '0', actividad: '000' },
  { programa: '100', proyecto: '0', actividad: '008' },
  { programa: '101', proyecto: '0', actividad: '000' },
  { programa: '101', proyecto: '0', actividad: '010' },
  { programa: '101', proyecto: '0', actividad: '013' },
  { programa: '101', proyecto: '0', actividad: '015' },
  { programa: '101', proyecto: '0', actividad: '017' },
  { programa: '101', proyecto: '0', actividad: '019' },
  { programa: '101', proyecto: '0', actividad: '020' },
  { programa: '101', proyecto: '0', actividad: '021' },
  { programa: '101', proyecto: '0', actividad: '022' },
  { programa: '101', proyecto: '0', actividad: '023' },
];

/** Normaliza un segmento a su ancho oficial: "1" → "001". */
export function normalizarSegmento(valor: string, ancho: number): string {
  const limpio = (valor || '').trim().replace(/\D/g, '');
  if (!limpio) return '';
  return limpio.slice(-ancho).padStart(ancho, '0');
}

/**
 * La categoría programática es una concatenación, no un dato que se escriba:
 * se deriva de los tres segmentos.
 */
export function categoriaProgramatica(categoria: CategoriaProgramatica): string {
  const programa = normalizarSegmento(categoria.programa, ANCHO_PROGRAMA);
  const proyecto = normalizarSegmento(categoria.proyecto, ANCHO_PROYECTO);
  const actividad = normalizarSegmento(categoria.actividad, ANCHO_ACTIVIDAD);
  if (!programa || !proyecto || !actividad) return '';
  return `${programa} ${proyecto} ${actividad}`;
}

export function etiquetaCategoria(categoria: CategoriaProgramatica): string {
  return `${categoria.programa} ${categoria.proyecto} ${categoria.actividad}`;
}
