/**
 * Catálogos de la formulación del PAD 2026-2030.
 *
 * El marco nacional (ejes PGDESA, componentes PDESA y ODS) vive en
 * `shared/catalogos/pgdesa.catalogo`, compartido con el PEI: ambos
 * instrumentos articulan a la misma planificación nacional.
 *
 * Fuente metodológica: "Guía Metodológica para la Formulación de Planes
 * Autónomos de Desarrollo 2026-2030" (MPDyMA), §4 Planificación para el
 * Desarrollo y §4.5 Matrices de Planificación PAD.
 */
export {
  EJES_PGDESA,
  CATALOGO_ODS,
} from '../../../shared/catalogos/pgdesa.catalogo';
export type {
  EjePgdesa,
  ComponentePdesa,
} from '../../../shared/catalogos/pgdesa.catalogo';

/** Gestiones del quinquenio del PAD. */
export const GESTIONES_PAD = ['2026', '2027', '2028', '2029', '2030'] as const;

export type GestionPad = (typeof GESTIONES_PAD)[number];

/**
 * Acciones de cambio del resultado territorial.
 * Guía PAD §4.4: la redacción del resultado va en tiempo pretérito,
 * definiendo la acción y la condición de la acción que se ha cambiado.
 */
export const ACCIONES_DE_CAMBIO_PAD: string[] = [
  'Se ha incrementado',
  'Se ha reducido',
  'Se ha mejorado',
  'Se ha ampliado',
  'Se ha fortalecido',
  'Se ha consolidado',
];

/** Respuesta admitida en la columna CUENTA CON FINANCIAMIENTO de la Matriz A. */
export const OPCIONES_FINANCIAMIENTO = [
  { valor: true, etiqueta: 'SÍ' },
  { valor: false, etiqueta: 'NO' },
];

/**
 * Cantidad oficial de instrumentos internacionales, según la guía PAD §4.5.2:
 * 17 ODS, 35 metas NDC, 19 principios NDT.
 */
export const TOPES_ACUERDOS = { ods: 17, ndc: 35, ndt: 19 };
