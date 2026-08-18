/**
 * Catálogos de la formulación del PEI 2026-2030.
 *
 * El marco nacional (ejes PGDESA, componentes PDESA y ODS) vive en
 * `shared/catalogos/pgdesa.catalogo`, compartido con el PAD: ambos
 * instrumentos articulan a la misma planificación nacional.
 */
export {
  EJES_PGDESA,
  CATALOGO_ODS,
} from '../../../shared/catalogos/pgdesa.catalogo';
export type {
  EjePgdesa,
  ComponentePdesa,
} from '../../../shared/catalogos/pgdesa.catalogo';

/**
 * Acciones de cambio admitidas para el resultado institucional.
 * Guía §3.2: Resultado = acción de cambio (pretérito perfecto compuesto)
 * + variable de resultado.
 */
export const ACCIONES_DE_CAMBIO: string[] = [
  'Se ha incrementado',
  'Se ha reducido',
  'Se ha fortalecido',
  'Se ha ampliado',
  'Se ha mejorado',
  'Se ha consolidado',
];

/**
 * Condiciones de estado admitidas para el producto institucional.
 * Guía §3.3: Producto = bien, servicio o norma + condición de estado.
 */
export const CONDICIONES_DE_ESTADO: string[] = [
  'elaborado',
  'emitido',
  'implementado',
  'entregado',
  'construido',
  'prestado',
  'realizado',
];

/** Guía §3.3: clasificación del producto institucional. */
export const TIPOS_PRODUCTO: { valor: string; etiqueta: string; ayuda: string }[] = [
  {
    valor: 'TERMINAL',
    etiqueta: 'Terminal',
    ayuda: 'Orientado al beneficiario final.',
  },
  {
    valor: 'FINAL',
    etiqueta: 'Final',
    ayuda: 'Entregado a otras entidades como insumo para productos terminales.',
  },
  {
    valor: 'INTERMEDIO',
    etiqueta: 'Intermedio',
    ayuda: 'Ligado al funcionamiento o gasto administrativo vital de la entidad.',
  },
];

/** Gestiones del quinquenio de planificación. */
export const GESTIONES_PEI = ['2026', '2027', '2028', '2029', '2030'] as const;

export type GestionPei = (typeof GESTIONES_PEI)[number];
