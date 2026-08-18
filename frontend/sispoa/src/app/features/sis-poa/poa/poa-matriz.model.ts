/**
 * Modelo y reglas puras de la Matriz de Formulación POA.
 *
 * Fusiona el Cuadro 1 "Articulación POA – PEI" (campos 1 a 8) con el
 * Cuadro 2 "Programación de Acciones a Corto Plazo" (campos 9, 10 y 11) del
 * Reglamento Específico del Sistema de Programación de Operaciones
 * (RE-SPO, GAM Sacaba 2025), Artículo 14.
 *
 * Los campos 1 a 8 tienen fuente PEI; los campos 9 a 11 los define la entidad
 * al programar la gestión (Anexo "Descripción de campos").
 *
 * Antes del presupuesto programado se intercala la categoría programática del
 * clasificador presupuestario (programa, proyecto y actividad), cuyo código
 * completo es la concatenación de los tres segmentos.
 */
import {
  ANCHO_ACTIVIDAD,
  ANCHO_PROGRAMA,
  ANCHO_PROYECTO,
  categoriaProgramatica,
  normalizarSegmento,
} from './poa-catalogos';

/** Cabecera con fuente PEI: campos 1 a 4 del Cuadro 1. */
export interface ArticulacionPeiPoa {
  /** (1) Código asignado a la Acción Institucional Específica. */
  codigoPei: string;
  /** (2) Denominación de la Acción Institucional Específica. */
  accionInstitucionalEspecifica: string;
  /** (3) Indicador definido para medir la Acción Institucional Específica. */
  indicadorProceso: string;
  /** (4) Área o Unidad organizacional responsable de la AIE. */
  areaResponsable: string;
  /** Identificador del producto institucional del PEI que origina la AIE. */
  productoPeiId: string | null;
  /** Contexto heredado del PEI, solo informativo en la matriz. */
  resultadoPei: string;
  codigoResultadoPei: string;
  unidadResponsableId: string | null;
}

export function articulacionVacia(): ArticulacionPeiPoa {
  return {
    codigoPei: '',
    accionInstitucionalEspecifica: '',
    indicadorProceso: '',
    areaResponsable: '',
    productoPeiId: null,
    resultadoPei: '',
    codigoResultadoPei: '',
    unidadResponsableId: null,
  };
}

/** Acción de corto plazo: campos 5 a 11 de la matriz fusionada. */
export interface AccionCortoPlazoForm {
  /** (5) Código de la acción de corto plazo. */
  codigo: string;
  /** (6) Denominación de la acción de corto plazo de la gestión. */
  denominacion: string;
  /** (7) Resultado esperado para el período fiscal programado. */
  resultadoEsperado: string;
  /** Segmento "programa" de la categoría programática. */
  programa: string;
  /** Segmento "proyecto" de la categoría programática. */
  proyecto: string;
  /** Segmento "actividad" de la categoría programática. */
  actividad: string;
  /** (8) Presupuesto programado para la gestión. */
  presupuestoProgramado: number | null;
  /** (9) Cargo del Responsable de Ejecución de la Acción de Corto Plazo. */
  cargoReacp: string;
  /** (10) Fecha prevista de inicio. */
  fechaInicio: string;
  /** (11) Fecha prevista de finalización. */
  fechaFin: string;
}

export function accionVacia(): AccionCortoPlazoForm {
  return {
    codigo: '',
    denominacion: '',
    resultadoEsperado: '',
    programa: '',
    proyecto: '0',
    actividad: '',
    presupuestoProgramado: null,
    cargoReacp: '',
    fechaInicio: '',
    fechaFin: '',
  };
}

// ---------------------------------------------------------------------------
// Codificación
// ---------------------------------------------------------------------------

/**
 * El código de la acción de corto plazo cuelga del código del producto
 * institucional del PEI: 907.1.1 → 907.1.1.1
 */
export function codigoAccion(codigoPei: string, indice: number): string {
  if (!codigoPei) return '';
  return `${codigoPei}.${indice + 1}`;
}

// ---------------------------------------------------------------------------
// Filas de la matriz fusionada (11 columnas)
// ---------------------------------------------------------------------------

export interface FilaMatrizPoa {
  codigoPei: string;
  accionInstitucionalEspecifica: string;
  indicadorProceso: string;
  areaResponsable: string;
  codigoAccion: string;
  accionCortoPlazo: string;
  resultadoEsperado: string;
  programa: string;
  proyecto: string;
  actividad: string;
  categoriaProgramatica: string;
  presupuestoProgramado: number | null;
  cargoReacp: string;
  fechaInicio: string;
  fechaFin: string;
}

export function construirFilas(
  articulacion: ArticulacionPeiPoa,
  acciones: AccionCortoPlazoForm[],
  correlativoBase = 1,
): FilaMatrizPoa[] {
  return acciones.map((accion, indice) => ({
    codigoPei: articulacion.codigoPei,
    accionInstitucionalEspecifica: articulacion.accionInstitucionalEspecifica,
    indicadorProceso: articulacion.indicadorProceso,
    areaResponsable: articulacion.areaResponsable,
    codigoAccion:
      accion.codigo ||
      codigoAccion(articulacion.codigoPei, correlativoBase - 1 + indice),
    accionCortoPlazo: accion.denominacion,
    resultadoEsperado: accion.resultadoEsperado,
    programa: normalizarSegmento(accion.programa, ANCHO_PROGRAMA),
    proyecto: normalizarSegmento(accion.proyecto, ANCHO_PROYECTO),
    actividad: normalizarSegmento(accion.actividad, ANCHO_ACTIVIDAD),
    categoriaProgramatica: categoriaProgramatica(accion),
    presupuestoProgramado: accion.presupuestoProgramado,
    cargoReacp: accion.cargoReacp,
    fechaInicio: accion.fechaInicio,
    fechaFin: accion.fechaFin,
  }));
}

export function presupuestoTotal(acciones: AccionCortoPlazoForm[]): number {
  return acciones.reduce(
    (total, a) => total + (Number(a.presupuestoProgramado) || 0),
    0,
  );
}

// ---------------------------------------------------------------------------
// Validaciones
// ---------------------------------------------------------------------------

export type SeveridadHallazgo = 'error' | 'aviso';

export interface Hallazgo {
  severidad: SeveridadHallazgo;
  seccion: string;
  mensaje: string;
}

function fueraDeGestion(fecha: string, gestion: number): boolean {
  if (!fecha) return false;
  const anio = Number(fecha.slice(0, 4));
  return Number.isFinite(anio) && anio !== gestion;
}

/**
 * Contrasta el borrador contra el RE-SPO. Los "error" bloquean el registro;
 * los "aviso" solo advierten.
 */
export function validarMatriz(
  articulacion: ArticulacionPeiPoa,
  acciones: AccionCortoPlazoForm[],
  gestion: number,
): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];

  if (!articulacion.productoPeiId) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación PEI',
      mensaje:
        'El Artículo 13 exige que las acciones de corto plazo estén articuladas con el PEI: seleccione la acción institucional específica de origen.',
    });
  }
  if (!articulacion.indicadorProceso.trim()) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Articulación PEI',
      mensaje:
        'Sin indicador de proceso no se podrá medir la acción institucional específica ni evaluar su eficacia.',
    });
  }
  if (!articulacion.areaResponsable.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación PEI',
      mensaje:
        'Identifique el área o unidad organizacional responsable de la acción institucional específica.',
    });
  }

  if (!acciones.length) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Acciones de corto plazo',
      mensaje: 'Programe al menos una acción de corto plazo para la gestión.',
    });
  }

  acciones.forEach((accion, indice) => {
    const etiqueta = `Acción ${indice + 1}`;
    if (!accion.denominacion.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Registre la denominación de la acción de corto plazo.',
      });
    }
    if (!accion.resultadoEsperado.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje:
          'El resultado esperado es la base de la evaluación de eficacia (logrado / esperado).',
      });
    }
    if (!accion.cargoReacp.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje:
          'Defina el cargo del REACP: es quien establece las fechas y responde por la ejecución.',
      });
    }
    if (!accion.fechaInicio || !accion.fechaFin) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Establezca las fechas previstas de inicio y finalización.',
      });
    } else if (accion.fechaFin < accion.fechaInicio) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'La fecha de finalización no puede ser anterior a la de inicio.',
      });
    }
    if (
      fueraDeGestion(accion.fechaInicio, gestion) ||
      fueraDeGestion(accion.fechaFin, gestion)
    ) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: `Las fechas caen fuera de la gestión ${gestion} que se está programando.`,
      });
    }
    if (!categoriaProgramatica(accion)) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje:
          'Complete la categoría programática: programa, proyecto y actividad del clasificador presupuestario.',
      });
    }
    if (
      accion.presupuestoProgramado === null ||
      Number(accion.presupuestoProgramado) <= 0
    ) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: 'La acción no tiene presupuesto programado para la gestión.',
      });
    }
  });

  return hallazgos;
}

export function tieneErrores(hallazgos: Hallazgo[]): boolean {
  return hallazgos.some(h => h.severidad === 'error');
}
