/**
 * Modelo y reglas puras de la Matriz de Planificación PEI 2026-2030.
 *
 * La matriz territorial oficial tiene 46 columnas agrupadas en ocho secciones
 * (Guía Metodológica PEI §3.7). Una fila de nivel "resultado" abre cada
 * resultado institucional y las filas de nivel "producto" cuelgan de ella.
 */
import { GESTIONES_PEI } from './pei-catalogos';

export type NivelFila = 'resultado' | 'producto';

/** Valor literal que exige la guía en las columnas que no aplican a la fila de resultado. */
export const NO_APLICA = 'NO APLICA';

/** Programación anual indexada por gestión del quinquenio. */
export type ProgramacionAnual = Record<string, number | null>;

export function programacionVacia(): ProgramacionAnual {
  return GESTIONES_PEI.reduce<ProgramacionAnual>((acc, anio) => {
    acc[anio] = null;
    return acc;
  }, {});
}

/** Secciones I a IV más la articulación territorial: contexto común del resultado. */
export interface ArticulacionPei {
  codEjePgdesa: string;
  objetivoImpacto: string;
  codComponentePdesa: string;
  objetivoEfecto: string;
  codOds: string;
  codNdc: string;
  codNdt: string;
  codMeta3030: string;
  codSector: string;
  sector: string;
  codResultadoSectorial: string;
  resultadoSectorial: string;
  codResultadoTerritorial: string;
  resultadoPadId: string | null;
}

/** Sección VI: ficha del indicador y su programación física y financiera. */
export interface IndicadorPei {
  indicador: string;
  tipoIndicador: 'Resultado' | 'Producto';
  unidadMedida: string;
  formula: string;
  lineaBase: number | null;
  meta2030: number | null;
  fisica: ProgramacionAnual;
  inversion: ProgramacionAnual;
  corriente: ProgramacionAnual;
}

export function indicadorVacio(tipo: 'Resultado' | 'Producto'): IndicadorPei {
  return {
    indicador: '',
    tipoIndicador: tipo,
    unidadMedida: '',
    formula: 'N/A',
    lineaBase: null,
    meta2030: null,
    fisica: programacionVacia(),
    inversion: programacionVacia(),
    corriente: programacionVacia(),
  };
}

/** Producto institucional (reemplaza a la AMP en el ciclo 2026-2030). */
export interface ProductoPeiForm {
  codigoProducto: string;
  denominacion: string;
  bienServicio: string;
  condicionEstado: string;
  tipoProducto: string;
  codProgramaPresup: string;
  programaPresup: string;
  indicador: IndicadorPei;
}

export function productoVacio(): ProductoPeiForm {
  return {
    codigoProducto: '',
    denominacion: '',
    bienServicio: '',
    condicionEstado: '',
    tipoProducto: 'TERMINAL',
    codProgramaPresup: '',
    programaPresup: '',
    indicador: indicadorVacio('Producto'),
  };
}

/** Sección V: identificación institucional y resultado del PEI. */
export interface ResultadoPeiForm {
  codEntidad: string;
  entidad: string;
  vigenciaDesde: number;
  vigenciaHasta: number;
  codOei: string;
  objetivoEstrategico: string;
  correlativoResultado: number;
  accionCambio: string;
  variableResultado: string;
  indicador: IndicadorPei;
}

export function resultadoVacio(): ResultadoPeiForm {
  return {
    codEntidad: '',
    entidad: '',
    vigenciaDesde: 2026,
    vigenciaHasta: 2030,
    codOei: 'OE 1.',
    objetivoEstrategico: '',
    correlativoResultado: 1,
    accionCambio: '',
    variableResultado: '',
    indicador: indicadorVacio('Resultado'),
  };
}

export function articulacionVacia(): ArticulacionPei {
  return {
    codEjePgdesa: '',
    objetivoImpacto: '',
    codComponentePdesa: '',
    objetivoEfecto: '',
    codOds: '',
    codNdc: 'N/A',
    codNdt: 'N/A',
    codMeta3030: 'N/A',
    codSector: '',
    sector: '',
    codResultadoSectorial: '',
    resultadoSectorial: '',
    codResultadoTerritorial: '',
    resultadoPadId: null,
  };
}

/** Fila desnormalizada tal como se imprime en la matriz oficial. */
export interface FilaMatrizPei extends ArticulacionPei {
  nivel: NivelFila;
  codEntidad: string;
  entidad: string;
  codOei: string;
  codResultadoPei: string;
  resultadoInstitucional: string;
  codProgramaPresup: string;
  programaPresup: string;
  codProducto: string;
  nombreProducto: string;
  indicador: string;
  tipoIndicador: string;
  unidadMedida: string;
  formula: string;
  lineaBase: number | null;
  meta2030: number | null;
  fisica: ProgramacionAnual;
  presupuestoTotal: number;
  inversionTotal: number;
  inversion: ProgramacionAnual;
  corrienteTotal: number;
  corriente: ProgramacionAnual;
}

// ---------------------------------------------------------------------------
// Reglas de codificación (Guía §3.2 y §3.3)
// ---------------------------------------------------------------------------

/** Código de resultado = código de entidad + "." + número de resultado. */
export function codigoResultado(codEntidad: string, correlativo: number): string {
  if (!codEntidad) return '';
  return `${codEntidad}.${correlativo}`;
}

/** Código de producto = código de resultado + "." + correlativo. */
export function codigoProducto(codResultado: string, indice: number): string {
  if (!codResultado) return '';
  return `${codResultado}.${indice + 1}`;
}

/** Resultado institucional = acción de cambio + variable de resultado. */
export function redactarResultado(accion: string, variable: string): string {
  const partes = [accion.trim(), variable.trim()].filter(Boolean);
  if (!partes.length) return '';
  const texto = partes.join(' ');
  return texto.endsWith('.') ? texto : `${texto}.`;
}

/** Producto institucional = bien, servicio o norma + condición de estado. */
export function redactarProducto(bienServicio: string, condicion: string): string {
  const partes = [bienServicio.trim(), condicion.trim()].filter(Boolean);
  return partes.join(' ');
}

// ---------------------------------------------------------------------------
// Totales
// ---------------------------------------------------------------------------

export function sumarProgramacion(programacion: ProgramacionAnual): number {
  return GESTIONES_PEI.reduce(
    (total, anio) => total + (Number(programacion[anio]) || 0),
    0,
  );
}

export function totalIndicador(indicador: IndicadorPei): {
  inversionTotal: number;
  corrienteTotal: number;
  presupuestoTotal: number;
} {
  const inversionTotal = sumarProgramacion(indicador.inversion);
  const corrienteTotal = sumarProgramacion(indicador.corriente);
  return {
    inversionTotal,
    corrienteTotal,
    presupuestoTotal: inversionTotal + corrienteTotal,
  };
}

/**
 * Guía §3.4: el presupuesto del resultado institucional es la sumatoria del
 * presupuesto de los productos que lo componen.
 */
export function consolidarPresupuestoResultado(
  productos: ProductoPeiForm[],
): { inversion: ProgramacionAnual; corriente: ProgramacionAnual } {
  const inversion = programacionVacia();
  const corriente = programacionVacia();
  for (const anio of GESTIONES_PEI) {
    inversion[anio] = productos.reduce(
      (total, p) => total + (Number(p.indicador.inversion[anio]) || 0),
      0,
    );
    corriente[anio] = productos.reduce(
      (total, p) => total + (Number(p.indicador.corriente[anio]) || 0),
      0,
    );
  }
  return { inversion, corriente };
}

// ---------------------------------------------------------------------------
// Construcción de filas
// ---------------------------------------------------------------------------

function filaBase(
  articulacion: ArticulacionPei,
  resultado: ResultadoPeiForm,
  codResultadoPei: string,
): Pick<
  FilaMatrizPei,
  keyof ArticulacionPei | 'codEntidad' | 'entidad' | 'codOei' | 'codResultadoPei' | 'resultadoInstitucional'
> {
  return {
    ...articulacion,
    codEntidad: resultado.codEntidad,
    entidad: resultado.entidad,
    codOei: resultado.codOei,
    codResultadoPei,
    resultadoInstitucional: redactarResultado(
      resultado.accionCambio,
      resultado.variableResultado,
    ),
  };
}

function filaIndicador(indicador: IndicadorPei): Pick<
  FilaMatrizPei,
  | 'indicador'
  | 'tipoIndicador'
  | 'unidadMedida'
  | 'formula'
  | 'lineaBase'
  | 'meta2030'
  | 'fisica'
  | 'presupuestoTotal'
  | 'inversionTotal'
  | 'inversion'
  | 'corrienteTotal'
  | 'corriente'
> {
  const totales = totalIndicador(indicador);
  return {
    indicador: indicador.indicador,
    tipoIndicador: indicador.tipoIndicador,
    unidadMedida: indicador.unidadMedida,
    formula: indicador.formula,
    lineaBase: indicador.lineaBase,
    meta2030: indicador.meta2030,
    fisica: indicador.fisica,
    presupuestoTotal: totales.presupuestoTotal,
    inversionTotal: totales.inversionTotal,
    inversion: indicador.inversion,
    corrienteTotal: totales.corrienteTotal,
    corriente: indicador.corriente,
  };
}

/**
 * Arma las filas de la matriz: una de nivel resultado seguida de una por cada
 * producto institucional. La fila de resultado consolida el presupuesto de sus
 * productos y marca programa y producto como NO APLICA.
 */
export function construirFilas(
  articulacion: ArticulacionPei,
  resultado: ResultadoPeiForm,
  productos: ProductoPeiForm[],
): FilaMatrizPei[] {
  const codResultadoPei = codigoResultado(
    resultado.codEntidad,
    resultado.correlativoResultado,
  );
  const consolidado = consolidarPresupuestoResultado(productos);
  const indicadorResultado: IndicadorPei = {
    ...resultado.indicador,
    inversion: consolidado.inversion,
    corriente: consolidado.corriente,
  };

  const filas: FilaMatrizPei[] = [
    {
      nivel: 'resultado',
      ...filaBase(articulacion, resultado, codResultadoPei),
      codProgramaPresup: NO_APLICA,
      programaPresup: NO_APLICA,
      codProducto: NO_APLICA,
      nombreProducto: NO_APLICA,
      ...filaIndicador(indicadorResultado),
    },
  ];

  productos.forEach((producto, indice) => {
    filas.push({
      nivel: 'producto',
      ...filaBase(articulacion, resultado, codResultadoPei),
      codProgramaPresup: producto.codProgramaPresup,
      programaPresup: producto.programaPresup,
      codProducto:
        producto.codigoProducto || codigoProducto(codResultadoPei, indice),
      nombreProducto: redactarProducto(
        producto.bienServicio,
        producto.condicionEstado,
      ) || producto.denominacion,
      ...filaIndicador(producto.indicador),
    });
  });

  return filas;
}

// ---------------------------------------------------------------------------
// Validaciones metodológicas
// ---------------------------------------------------------------------------

export type SeveridadHallazgo = 'error' | 'aviso';

export interface Hallazgo {
  severidad: SeveridadHallazgo;
  seccion: string;
  mensaje: string;
}

const VERBO_INFINITIVO = /^[a-záéíóúñ]+(ar|er|ir)\b/i;
const CIFRA_O_PORCENTAJE = /(\d|%)/;

/**
 * Contrasta el borrador contra las reglas de la Guía Metodológica.
 * Los "error" bloquean el guardado; los "aviso" solo advierten.
 */
export function validarMatriz(
  articulacion: ArticulacionPei,
  resultado: ResultadoPeiForm,
  productos: ProductoPeiForm[],
): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];

  if (!articulacion.codEjePgdesa) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección I',
      mensaje: 'Seleccione el eje del PGDESA y su componente PDESA.',
    });
  }
  if (!articulacion.codSector) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección III',
      mensaje: 'Registre el código de sector del clasificador presupuestario.',
    });
  }
  if (!articulacion.codResultadoTerritorial) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Articulación territorial',
      mensaje:
        'Sin código de resultado territorial el PEI no podrá articularse con el PAD.',
    });
  }

  if (!resultado.codEntidad) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección V',
      mensaje: 'El código de entidad define la codificación del resultado PEI.',
    });
  }
  if (!resultado.entidad.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección V',
      mensaje:
        'Registre la denominación de la entidad según el clasificador presupuestario.',
    });
  }
  if (!resultado.objetivoEstrategico.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección V',
      mensaje: 'Redacte el objetivo estratégico institucional.',
    });
  } else {
    if (!VERBO_INFINITIVO.test(resultado.objetivoEstrategico.trim())) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: 'Sección V',
        mensaje:
          'El objetivo estratégico debería iniciar con un verbo en infinitivo (Guía §3.1).',
      });
    }
    if (CIFRA_O_PORCENTAJE.test(resultado.objetivoEstrategico)) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: 'Sección V',
        mensaje:
          'El objetivo estratégico no debe incluir metas, porcentajes ni plazos (Guía §3.1).',
      });
    }
  }
  if (!resultado.accionCambio || !resultado.variableResultado.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección V',
      mensaje:
        'El resultado institucional se compone de acción de cambio + variable de resultado.',
    });
  }

  if (!resultado.indicador.indicador.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección VI',
      mensaje: 'El resultado institucional requiere un indicador verificable.',
    });
  }
  if (!resultado.indicador.unidadMedida.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección VI',
      mensaje: 'La unidad de medida expresa el indicador (%, número de personas, km, Bs).',
    });
  }
  if (resultado.indicador.meta2030 === null) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección VI',
      mensaje: 'Registre la meta 2030 del indicador de resultado.',
    });
  }
  if (!esNoDecreciente(resultado.indicador.fisica)) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Sección VII',
      mensaje:
        'Las metas de resultado se plantean de manera acumulativa: no deberían decrecer (Guía §3.2.2).',
    });
  }

  if (!productos.length) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Sección V',
      mensaje:
        'Todo resultado institucional se alcanza mediante productos institucionales (Guía §3.3).',
    });
  }

  productos.forEach((producto, indice) => {
    const etiqueta = `Producto ${indice + 1}`;
    if (!producto.bienServicio.trim() || !producto.condicionEstado.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Producto = bien, servicio o norma + condición de estado.',
      });
    }
    if (!producto.codProgramaPresup.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Cada producto se articula con un programa presupuestario.',
      });
    }
    if (!producto.indicador.indicador.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Registre el indicador de seguimiento del producto.',
      });
    }
    if (!producto.indicador.unidadMedida.trim()) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Falta la unidad de medida del indicador del producto.',
      });
    }
    if (totalIndicador(producto.indicador).presupuestoTotal === 0) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje:
          'El producto no tiene presupuesto quinquenal asignado (inversión ni corriente).',
      });
    }
  });

  return hallazgos;
}

function esNoDecreciente(programacion: ProgramacionAnual): boolean {
  let anterior: number | null = null;
  for (const anio of GESTIONES_PEI) {
    const valor = programacion[anio];
    if (valor === null || valor === undefined || valor === ('' as unknown)) continue;
    const actual = Number(valor);
    if (anterior !== null && actual < anterior) return false;
    anterior = actual;
  }
  return true;
}

export function tieneErrores(hallazgos: Hallazgo[]): boolean {
  return hallazgos.some(h => h.severidad === 'error');
}
