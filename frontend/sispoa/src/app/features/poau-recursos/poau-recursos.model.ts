/**
 * Modelo y reglas puras de la Matriz de Programación Presupuestaria del POAU.
 *
 * Es la contraparte financiera de la programación física: determina los
 * requerimientos de bienes y servicios de cada acción, su clasificación
 * presupuestaria y el mes en que se necesita el pago
 * (RE-SPO, Artículo 14 inciso c y Cuadro 4).
 */

export const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
] as const;

/**
 * Tipos de gasto de la clasificación presupuestaria boliviana.
 *
 * Es una convención escrita acá y no un catálogo importado: `tipo_gasto` es un
 * `CharField` libre en `AsignacionObjetoGasto` y no hay tabla maestra ni
 * `choices` en el backend. Se fija la lista para que el campo deje de recibir
 * texto suelto; el día que exista el catálogo, esto se reemplaza por él.
 */
export const TIPOS_GASTO = ['Funcionamiento', 'Inversión'] as const;

/**
 * El grupo de gasto que le corresponde a una partida.
 *
 * El clasificador es jerárquico por código: la partida `25200` cuelga del
 * subgrupo `25000` y este del grupo `20000`. O sea que el grupo es el primer
 * dígito de la partida seguido de cuatro ceros, y pedirlo aparte sería pedir
 * un dato que ya está.
 */
export function grupoDePartida(codPartida: string): string {
  const codigo = (codPartida || '').trim();
  if (!/^\d{5}$/.test(codigo)) { return ''; }
  return `${codigo[0]}0000`;
}

export type ProgramacionMensual = Record<string, number | null>;

export function programacionVacia(): ProgramacionMensual {
  return MESES.reduce<ProgramacionMensual>((acc, mes) => {
    acc[mes] = null;
    return acc;
  }, {});
}

export function totalAnual(programacion: ProgramacionMensual): number {
  return MESES.reduce((t, mes) => t + (Number(programacion[mes]) || 0), 0);
}

/** Cabecera heredada de la acción de corto plazo y su categoría programática. */
export interface CabeceraRecursos {
  categoriaProgramatica: string;
  denominacionCategoria: string;
  cargoReacp: string;
  da: string;
  ue: string;
  gestion: number;
  accionPoaId: string | null;
  operacionId: string | null;
  actividadId: string | null;
  codigoAccion: string;
}

export function cabeceraVacia(): CabeceraRecursos {
  return {
    categoriaProgramatica: '',
    denominacionCategoria: '',
    cargoReacp: '',
    da: '',
    ue: '',
    // Sin gestión: la pone el asistente con la del candado (ADR-007). Un
    // literal acá reintroduce el año fijo por la puerta de atrás.
    gestion: 0,
    accionPoaId: null,
    operacionId: null,
    actividadId: null,
    codigoAccion: '',
  };
}

/** Requerimiento: un bien o servicio demandado con su partida y programación. */
export interface RequerimientoForm {
  bienServicio: string;
  codPartida: string;
  descripcionPartida: string;
  grupoGasto: string;
  tipoGasto: string;
  fuenteFinanciamiento: string;
  organismoFinanciador: string;
  fechaRequerimiento: string;
  presupuestoProgramado: number | null;
  programacion: ProgramacionMensual;
  medioVerificacion: string;
}

export function requerimientoVacio(): RequerimientoForm {
  return {
    bienServicio: '',
    codPartida: '',
    descripcionPartida: '',
    grupoGasto: '',
    tipoGasto: '',
    fuenteFinanciamiento: '',
    organismoFinanciador: '',
    fechaRequerimiento: '',
    presupuestoProgramado: null,
    programacion: programacionVacia(),
    medioVerificacion: '',
  };
}

// ---------------------------------------------------------------------------
// Filas de la matriz
// ---------------------------------------------------------------------------

export interface FilaMatrizRecursos extends CabeceraRecursos {
  fuenteFinanciamiento: string;
  organismoFinanciador: string;
  codPartida: string;
  bienServicio: string;
  fechaRequerimiento: string;
  presupuestoProgramado: number | null;
  programacion: ProgramacionMensual;
  totalAnual: number;
  medioVerificacion: string;
}

export function construirFilas(
  cabecera: CabeceraRecursos,
  requerimientos: RequerimientoForm[],
): FilaMatrizRecursos[] {
  return requerimientos.map(r => ({
    ...cabecera,
    fuenteFinanciamiento: r.fuenteFinanciamiento,
    organismoFinanciador: r.organismoFinanciador,
    codPartida: r.codPartida,
    bienServicio: r.bienServicio,
    fechaRequerimiento: r.fechaRequerimiento,
    presupuestoProgramado: r.presupuestoProgramado,
    programacion: r.programacion,
    totalAnual: totalAnual(r.programacion),
    medioVerificacion: r.medioVerificacion,
  }));
}

export function totalGeneral(requerimientos: RequerimientoForm[]): number {
  return requerimientos.reduce((t, r) => t + totalAnual(r.programacion), 0);
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

export function validarMatriz(
  cabecera: CabeceraRecursos,
  requerimientos: RequerimientoForm[],
): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];

  if (!cabecera.actividadId) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación POAU',
      mensaje:
        'Los requerimientos cuelgan de una actividad del POAU: seleccione operación y actividad.',
    });
  }
  if (!cabecera.categoriaProgramatica.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación POAU',
      mensaje: 'Falta la categoría programática que clasifica el gasto.',
    });
  }
  if (!cabecera.da.trim() || !cabecera.ue.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Articulación POAU',
      mensaje: 'Registre la Dirección Administrativa (DA) y la Unidad Ejecutora (UE).',
    });
  }
  if (!cabecera.cargoReacp.trim()) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Articulación POAU',
      mensaje: 'Sin el cargo del REACP no queda claro quién responde por el requerimiento.',
    });
  }

  if (!requerimientos.length) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Requerimientos',
      mensaje: 'Determine al menos un bien o servicio demandado.',
    });
  }

  requerimientos.forEach((r, i) => {
    const etiqueta = `Requerimiento ${i + 1}`;
    if (!r.bienServicio.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Registre el bien o servicio demandado.',
      });
    }
    if (!r.codPartida.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Falta el código de partida de gastos del clasificador.',
      });
    }
    if (!r.fuenteFinanciamiento.trim() || !r.organismoFinanciador.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Registre la fuente de financiamiento (FTE) y el organismo financiador (ORG).',
      });
    }
    if (!r.fechaRequerimiento.trim()) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: 'Indique el mes estimado en que se requiere el pago.',
      });
    }
    const total = totalAnual(r.programacion);
    if (total === 0) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Distribuya el presupuesto en los meses de la gestión.',
      });
    } else if (
      r.presupuestoProgramado !== null &&
      Math.abs(total - Number(r.presupuestoProgramado)) > 0.5
    ) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: `La suma mensual (${total}) no coincide con el presupuesto programado (${r.presupuestoProgramado}).`,
      });
    }
  });

  return hallazgos;
}

export function tieneErrores(hallazgos: Hallazgo[]): boolean {
  return hallazgos.some(h => h.severidad === 'error');
}
