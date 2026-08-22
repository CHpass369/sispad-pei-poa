/**
 * Modelo y reglas puras de la Matriz de Formulación POAU.
 *
 * Desagrega cada acción de corto plazo del POA en operaciones, actividades y
 * tareas específicas (RE-SPO, Artículo 14 inciso b y Cuadro 3), con
 * programación FÍSICA mensual. La matriz no lleva programación financiera:
 * los requerimientos y su presupuesto se tratan por separado (Cuadro 4).
 */

/** Meses de la gestión, en el orden en que se programan. */
export const MESES = [
  'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
  'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
] as const;

export type Mes = (typeof MESES)[number];

/** Programación física mensual. */
export type ProgramacionMensual = Record<string, number | null>;

export function programacionVacia(): ProgramacionMensual {
  return MESES.reduce<ProgramacionMensual>((acc, mes) => {
    acc[mes] = null;
    return acc;
  }, {});
}

export function totalAnual(programacion: ProgramacionMensual): number {
  return MESES.reduce(
    (total, mes) => total + (Number(programacion[mes]) || 0),
    0,
  );
}

/** Tipos de operación que reconoce el RE-SPO. */
export const TIPOS_OPERACION = [
  { valor: 'FUNCIONAMIENTO', etiqueta: 'De funcionamiento' },
  { valor: 'INVERSION', etiqueta: 'De inversión' },
];

/** Cabecera heredada del POA y del PEI: se repite en cada fila. */
export interface CabeceraPoau {
  codigoProductoPei: string;
  accionInstitucionalEspecifica: string;
  indicadorProceso: string;
  codigoAccionCortoPlazo: string;
  accionCortoPlazo: string;
  categoriaProgramatica: string;
  denominacionCategoria: string;
  accionPoaId: string | null;
  gestion: number;
}

export function cabeceraVacia(): CabeceraPoau {
  return {
    codigoProductoPei: '',
    accionInstitucionalEspecifica: '',
    indicadorProceso: '',
    codigoAccionCortoPlazo: '',
    accionCortoPlazo: '',
    categoriaProgramatica: '',
    denominacionCategoria: '',
    accionPoaId: null,
    // Sin gestión: la pone el asistente con la del candado (ADR-007). Un
    // literal acá reintroduce el año fijo por la puerta de atrás.
    gestion: 0,
  };
}

/** Ficha de medición compartida por operaciones y actividades. */
export interface IndicadorPoau {
  indicador: string;
  formula: string;
  unidadMedida: string;
  lineaBase: number | null;
  meta: number | null;
}

export function indicadorVacio(): IndicadorPoau {
  return {
    indicador: '',
    formula: 'N/A',
    unidadMedida: '',
    lineaBase: null,
    meta: null,
  };
}

/** Tarea específica: el nivel más desagregado del POAU. */
export interface TareaForm {
  denominacion: string;
  responsable: string;
  fechaInicio: string;
  fechaFin: string;
  programacion: ProgramacionMensual;
}

export function tareaVacia(): TareaForm {
  return {
    denominacion: '',
    responsable: '',
    fechaInicio: '',
    fechaFin: '',
    programacion: programacionVacia(),
  };
}

/** Actividad: desagregación opcional de la operación. */
export interface ActividadForm {
  denominacion: string;
  productoIntermedio: string;
  indicador: IndicadorPoau;
  fechaInicio: string;
  fechaFin: string;
  ponderacion: number | null;
  programacion: ProgramacionMensual;
  tareas: TareaForm[];
}

export function actividadVacia(): ActividadForm {
  return {
    denominacion: '',
    productoIntermedio: '',
    indicador: indicadorVacio(),
    fechaInicio: '',
    fechaFin: '',
    ponderacion: null,
    programacion: programacionVacia(),
    tareas: [],
  };
}

/** Operación: producto intermedio que conduce al resultado de la acción. */
export interface OperacionForm {
  denominacion: string;
  tipoOperacion: string;
  productoIntermedio: string;
  unidadEjecutora: string;
  indicador: IndicadorPoau;
  fechaInicio: string;
  fechaFin: string;
  ponderacion: number | null;
  programacion: ProgramacionMensual;
  actividades: ActividadForm[];
}

export function operacionVacia(): OperacionForm {
  return {
    denominacion: '',
    tipoOperacion: 'FUNCIONAMIENTO',
    productoIntermedio: '',
    unidadEjecutora: '',
    indicador: indicadorVacio(),
    fechaInicio: '',
    fechaFin: '',
    ponderacion: null,
    programacion: programacionVacia(),
    actividades: [],
  };
}

// ---------------------------------------------------------------------------
// Codificación
// ---------------------------------------------------------------------------

export function codigoOperacion(codigoAccion: string, indice: number): string {
  if (!codigoAccion) return '';
  return `${codigoAccion}.${indice + 1}`;
}

export function codigoActividad(codigoOperacion: string, indice: number): string {
  if (!codigoOperacion) return '';
  return `${codigoOperacion}.${indice + 1}`;
}

export function codigoTarea(codigoActividad: string, indice: number): string {
  if (!codigoActividad) return '';
  return `${codigoActividad}.${indice + 1}`;
}

// ---------------------------------------------------------------------------
// Filas de la matriz
// ---------------------------------------------------------------------------

export type NivelFilaPoau = 'operacion' | 'actividad' | 'tarea';

export interface FilaMatrizPoau extends CabeceraPoau {
  nivel: NivelFilaPoau;
  codigo: string;
  operacion: string;
  actividad: string;
  tarea: string;
  productoIntermedio: string;
  unidadEjecutora: string;
  indicador: string;
  formula: string;
  unidadMedida: string;
  lineaBase: number | null;
  meta: number | null;
  fechaInicio: string;
  fechaFin: string;
  ponderacion: number | null;
  programacion: ProgramacionMensual;
  totalAnual: number;
}

function filaBase(cabecera: CabeceraPoau): CabeceraPoau {
  return { ...cabecera };
}

export function construirFilas(
  cabecera: CabeceraPoau,
  operaciones: OperacionForm[],
): FilaMatrizPoau[] {
  const filas: FilaMatrizPoau[] = [];

  operaciones.forEach((operacion, i) => {
    const codOperacion = codigoOperacion(cabecera.codigoAccionCortoPlazo, i);
    filas.push({
      ...filaBase(cabecera),
      nivel: 'operacion',
      codigo: codOperacion,
      operacion: operacion.denominacion,
      actividad: '',
      tarea: '',
      productoIntermedio: operacion.productoIntermedio,
      unidadEjecutora: operacion.unidadEjecutora,
      indicador: operacion.indicador.indicador,
      formula: operacion.indicador.formula,
      unidadMedida: operacion.indicador.unidadMedida,
      lineaBase: operacion.indicador.lineaBase,
      meta: operacion.indicador.meta,
      fechaInicio: operacion.fechaInicio,
      fechaFin: operacion.fechaFin,
      ponderacion: operacion.ponderacion,
      programacion: operacion.programacion,
      totalAnual: totalAnual(operacion.programacion),
    });

    operacion.actividades.forEach((actividad, j) => {
      const codActividad = codigoActividad(codOperacion, j);
      filas.push({
        ...filaBase(cabecera),
        nivel: 'actividad',
        codigo: codActividad,
        operacion: operacion.denominacion,
        actividad: actividad.denominacion,
        tarea: '',
        productoIntermedio: actividad.productoIntermedio,
        unidadEjecutora: operacion.unidadEjecutora,
        indicador: actividad.indicador.indicador,
        formula: actividad.indicador.formula,
        unidadMedida: actividad.indicador.unidadMedida,
        lineaBase: actividad.indicador.lineaBase,
        meta: actividad.indicador.meta,
        fechaInicio: actividad.fechaInicio,
        fechaFin: actividad.fechaFin,
        ponderacion: actividad.ponderacion,
        programacion: actividad.programacion,
        totalAnual: totalAnual(actividad.programacion),
      });

      actividad.tareas.forEach((tarea, k) => {
        filas.push({
          ...filaBase(cabecera),
          nivel: 'tarea',
          codigo: codigoTarea(codActividad, k),
          operacion: operacion.denominacion,
          actividad: actividad.denominacion,
          tarea: tarea.denominacion,
          productoIntermedio: '',
          unidadEjecutora: tarea.responsable,
          indicador: '',
          formula: '',
          unidadMedida: '',
          lineaBase: null,
          meta: null,
          fechaInicio: tarea.fechaInicio,
          fechaFin: tarea.fechaFin,
          ponderacion: null,
          programacion: tarea.programacion,
          totalAnual: totalAnual(tarea.programacion),
        });
      });
    });
  });

  return filas;
}

export function ponderacionTotal(operaciones: OperacionForm[]): number {
  return operaciones.reduce((total, o) => total + (Number(o.ponderacion) || 0), 0);
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

function validarProgramacion(
  meta: number | null,
  programacion: ProgramacionMensual,
  etiqueta: string,
  hallazgos: Hallazgo[],
): void {
  const total = totalAnual(programacion);
  if (total === 0) {
    hallazgos.push({
      severidad: 'error',
      seccion: etiqueta,
      mensaje: 'Distribuya la meta en los meses de la gestión: la programación física está vacía.',
    });
    return;
  }
  if (meta !== null && Math.abs(total - Number(meta)) > 0.001) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: etiqueta,
      mensaje: `La suma mensual (${total}) no coincide con la meta declarada (${meta}).`,
    });
  }
}

export function validarMatriz(
  cabecera: CabeceraPoau,
  operaciones: OperacionForm[],
): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];
  const gestion = Number(cabecera.gestion);

  if (!cabecera.accionPoaId) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación POA',
      mensaje:
        'El POAU desagrega una acción de corto plazo del POA: seleccione la acción de origen.',
    });
  }
  if (!operaciones.length) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Operaciones',
      mensaje: 'Determine al menos una operación que conduzca al resultado esperado.',
    });
  }

  const ponderacion = ponderacionTotal(operaciones);
  if (operaciones.length && Math.abs(ponderacion - 100) > 0.01) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Operaciones',
      mensaje: `La ponderación de las operaciones suma ${ponderacion}%: debería totalizar 100%.`,
    });
  }

  operaciones.forEach((operacion, i) => {
    const etiqueta = `Operación ${i + 1}`;
    if (!operacion.denominacion.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Registre la denominación de la operación.',
      });
    }
    if (!operacion.productoIntermedio.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'La operación debe declarar su producto intermedio esperado.',
      });
    }
    if (!operacion.unidadEjecutora.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Identifique el área o unidad organizacional ejecutora.',
      });
    }
    if (!operacion.indicador.indicador.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Sin indicador la operación no se puede seguir ni cuantificar.',
      });
    }
    if (!operacion.indicador.unidadMedida.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Falta la unidad de medida del indicador.',
      });
    }
    if (!operacion.fechaInicio || !operacion.fechaFin) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Establezca las fechas previstas de inicio y finalización.',
      });
    } else if (operacion.fechaFin < operacion.fechaInicio) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'La fecha de finalización no puede ser anterior a la de inicio.',
      });
    }
    if (
      fueraDeGestion(operacion.fechaInicio, gestion) ||
      fueraDeGestion(operacion.fechaFin, gestion)
    ) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: `Las fechas caen fuera de la gestión ${gestion}.`,
      });
    }
    validarProgramacion(operacion.indicador.meta, operacion.programacion, etiqueta, hallazgos);

    operacion.actividades.forEach((actividad, j) => {
      const etiquetaActividad = `${etiqueta} · Actividad ${j + 1}`;
      if (!actividad.denominacion.trim()) {
        hallazgos.push({
          severidad: 'error',
          seccion: etiquetaActividad,
          mensaje: 'Registre la denominación de la actividad.',
        });
      }
      if (!actividad.indicador.indicador.trim()) {
        hallazgos.push({
          severidad: 'error',
          seccion: etiquetaActividad,
          mensaje: 'La actividad necesita un indicador propio para su seguimiento.',
        });
      }
      validarProgramacion(
        actividad.indicador.meta,
        actividad.programacion,
        etiquetaActividad,
        hallazgos,
      );

      actividad.tareas.forEach((tarea, k) => {
        const etiquetaTarea = `${etiquetaActividad} · Tarea ${k + 1}`;
        if (!tarea.denominacion.trim()) {
          hallazgos.push({
            severidad: 'error',
            seccion: etiquetaTarea,
            mensaje: 'Registre la denominación de la tarea específica.',
          });
        }
        if (!tarea.fechaInicio || !tarea.fechaFin) {
          hallazgos.push({
            severidad: 'error',
            seccion: etiquetaTarea,
            mensaje: 'Establezca las fechas previstas de inicio y finalización de la tarea.',
          });
        } else if (tarea.fechaFin < tarea.fechaInicio) {
          hallazgos.push({
            severidad: 'error',
            seccion: etiquetaTarea,
            mensaje: 'La fecha de finalización no puede ser anterior a la de inicio.',
          });
        }
        if (totalAnual(tarea.programacion) === 0) {
          hallazgos.push({
            severidad: 'aviso',
            seccion: etiquetaTarea,
            mensaje: 'La tarea no tiene programación física mensual cargada.',
          });
        }
      });
    });
  });

  return hallazgos;
}

export function tieneErrores(hallazgos: Hallazgo[]): boolean {
  return hallazgos.some(h => h.severidad === 'error');
}
