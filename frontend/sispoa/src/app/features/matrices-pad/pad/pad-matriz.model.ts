/**
 * Modelo y reglas puras de las Matrices de Planificación PAD 2026-2030.
 *
 * La Matriz "A" (27 columnas) sintetiza toda la propuesta de desarrollo del
 * territorio; la Matriz "B" (33 columnas) articula esa propuesta con el
 * PGDESA, los acuerdos internacionales y la planificación sectorial
 * (Guía PAD §4.5.1 y §4.5.2).
 */
import { GESTIONES_PAD } from './pad-catalogos';

export type NivelFilaPad = 'resultado' | 'producto';

/** Programación anual indexada por gestión del quinquenio. */
export type ProgramacionAnual = Record<string, number | null>;

export function programacionVacia(): ProgramacionAnual {
  return GESTIONES_PAD.reduce<ProgramacionAnual>((acc, anio) => {
    acc[anio] = null;
    return acc;
  }, {});
}

/** Cabecera de cadena: se repite en cada fila de las matrices. */
export interface CabeceraPad {
  // Planificación nacional (Matriz B)
  codEjePgdesa: string;
  objetivoImpacto: string;
  codComponentePdesa: string;
  objetivoEfecto: string;
  // Acuerdos internacionales (Matriz B)
  codOds: string;
  codNdc: string;
  codNdt: string;
  compromiso3030: string;
  // Planificación sectorial (Matriz B)
  codSector: string;
  sector: string;
  codResultadoSectorial: string;
  resultadoSectorial: string;
  // Planificación territorial (Matriz A y B)
  codGeografico: string;
  eta: string;
  politica: string;
  codLineamiento: string;
  lineamiento: string;
  lineamientoId: string | null;
}

export function cabeceraVacia(): CabeceraPad {
  return {
    codEjePgdesa: '',
    objetivoImpacto: '',
    codComponentePdesa: '',
    objetivoEfecto: '',
    codOds: '',
    codNdc: 'N/A',
    codNdt: 'N/A',
    compromiso3030: 'N/A',
    codSector: '',
    sector: '',
    codResultadoSectorial: '',
    resultadoSectorial: '',
    // Clasificador geográfico presupuestario: Sacaba = 351 (departamento 3,
    // provincia 5, municipio 1). Se escribe corrido, sin puntos, como en el
    // ejemplo del Ministerio (1102); así el código de resultado territorial
    // queda 351.<lineamiento>.<correlativo>. Entidad MEFP 1312 / SCB.
    codGeografico: '351',
    eta: 'GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA',
    politica: '',
    codLineamiento: '',
    lineamiento: '',
    lineamientoId: null,
  };
}

/** Ficha de indicador compartida por resultados y productos (Guía PAD §4.5.2.f). */
export interface IndicadorPad {
  indicador: string;
  formula: string;
  unidadMedida: string;
  lineaBase: number | null;
  anioLineaBase: number | null;
  meta2030: number | null;
}

export function indicadorVacio(): IndicadorPad {
  return {
    indicador: '',
    formula: 'N/A',
    unidadMedida: '',
    lineaBase: null,
    anioLineaBase: 2025,
    meta2030: null,
  };
}

/** Producto territorial: bien, servicio o intervención concreta. */
export interface ProductoPadForm {
  denominacion: string;
  territorializacion: string;
  responsable: string;
  cuentaConFinanciamiento: boolean;
  indicador: IndicadorPad;
  fisica: ProgramacionAnual;
  presupuesto: ProgramacionAnual;
}

export function productoVacio(responsable = ''): ProductoPadForm {
  return {
    denominacion: '',
    territorializacion: '',
    responsable,
    cuentaConFinanciamiento: false,
    indicador: indicadorVacio(),
    fisica: programacionVacia(),
    presupuesto: programacionVacia(),
  };
}

/** Resultado territorial con la colección de productos que lo alcanzan. */
export interface ResultadoPadForm {
  accionCambio: string;
  variableResultado: string;
  territorializacion: string;
  responsable: string;
  cuentaConFinanciamiento: boolean;
  indicador: IndicadorPad;
  fisica: ProgramacionAnual;
  presupuesto: ProgramacionAnual;
  productos: ProductoPadForm[];
}

export function resultadoVacio(): ResultadoPadForm {
  return {
    accionCambio: '',
    variableResultado: '',
    territorializacion: '',
    responsable: '',
    cuentaConFinanciamiento: false,
    indicador: indicadorVacio(),
    fisica: programacionVacia(),
    presupuesto: programacionVacia(),
    productos: [productoVacio()],
  };
}

// ---------------------------------------------------------------------------
// Redacción y codificación (Guía PAD §4.4 y §4.5.2.d)
// ---------------------------------------------------------------------------

/** Resultado territorial = acción de cambio en pretérito + variable. */
export function redactarResultado(accion: string, variable: string): string {
  const partes = [accion.trim(), variable.trim()].filter(Boolean);
  if (!partes.length) return '';
  const texto = partes.join(' ');
  return texto.endsWith('.') ? texto.slice(0, -1) : texto;
}

/**
 * Código del resultado territorial = código geográfico + código del
 * lineamiento estratégico + correlativo del resultado. Ejemplo: 1102.1.1
 */
export function codigoResultado(
  codGeografico: string,
  codLineamiento: string,
  correlativo: number,
): string {
  if (!codGeografico || !codLineamiento) return '';
  return `${codGeografico}.${codLineamiento}.${correlativo}`;
}

/** Código del producto = código del resultado + correlativo. */
export function codigoProducto(codResultado: string, indice: number): string {
  if (!codResultado) return '';
  return `${codResultado}.${indice + 1}`;
}

// ---------------------------------------------------------------------------
// Totales
// ---------------------------------------------------------------------------

export function sumarProgramacion(programacion: ProgramacionAnual): number {
  return GESTIONES_PAD.reduce(
    (total, anio) => total + (Number(programacion[anio]) || 0),
    0,
  );
}

/** El presupuesto del resultado es la sumatoria del de sus productos. */
export function consolidarPresupuesto(
  productos: ProductoPadForm[],
): ProgramacionAnual {
  const consolidado = programacionVacia();
  for (const anio of GESTIONES_PAD) {
    consolidado[anio] = productos.reduce(
      (total, p) => total + (Number(p.presupuesto[anio]) || 0),
      0,
    );
  }
  return consolidado;
}

// ---------------------------------------------------------------------------
// Filas de la Matriz "A" (27 columnas)
// ---------------------------------------------------------------------------

export interface FilaMatrizA {
  nivel: NivelFilaPad;
  sector: string;
  codGeografico: string;
  politica: string;
  codLineamiento: string;
  lineamiento: string;
  codResultadoTerritorial: string;
  resultadoTerritorial: string;
  codProducto: string;
  producto: string;
  territorializacion: string;
  responsable: string;
  indicador: string;
  formula: string;
  lineaBase: number | null;
  meta2030: number | null;
  fisica: ProgramacionAnual;
  cuentaConFinanciamiento: string;
  presupuestoTotal: number;
  presupuesto: ProgramacionAnual;
}

export function construirMatrizA(
  cabecera: CabeceraPad,
  resultados: ResultadoPadForm[],
  correlativoBase = 1,
): FilaMatrizA[] {
  const filas: FilaMatrizA[] = [];

  resultados.forEach((resultado, indice) => {
    const codResultado = codigoResultado(
      cabecera.codGeografico,
      cabecera.codLineamiento,
      correlativoBase + indice,
    );
    const presupuestoResultado = consolidarPresupuesto(resultado.productos);

    filas.push({
      nivel: 'resultado',
      sector: cabecera.sector,
      codGeografico: cabecera.codGeografico,
      politica: cabecera.politica,
      codLineamiento: cabecera.codLineamiento,
      lineamiento: cabecera.lineamiento,
      codResultadoTerritorial: codResultado,
      resultadoTerritorial: redactarResultado(
        resultado.accionCambio,
        resultado.variableResultado,
      ),
      codProducto: '',
      producto: '',
      territorializacion: resultado.territorializacion,
      responsable: resultado.responsable,
      indicador: resultado.indicador.indicador,
      formula: resultado.indicador.formula,
      lineaBase: resultado.indicador.lineaBase,
      meta2030: resultado.indicador.meta2030,
      fisica: resultado.fisica,
      cuentaConFinanciamiento: resultado.cuentaConFinanciamiento ? 'SÍ' : 'NO',
      presupuestoTotal: sumarProgramacion(presupuestoResultado),
      presupuesto: presupuestoResultado,
    });

    resultado.productos.forEach((producto, j) => {
      filas.push({
        nivel: 'producto',
        sector: cabecera.sector,
        codGeografico: cabecera.codGeografico,
        politica: cabecera.politica,
        codLineamiento: cabecera.codLineamiento,
        lineamiento: cabecera.lineamiento,
        codResultadoTerritorial: '',
        resultadoTerritorial: '',
        codProducto: codigoProducto(codResultado, j),
        producto: producto.denominacion,
        territorializacion: producto.territorializacion,
        responsable: producto.responsable,
        indicador: producto.indicador.indicador,
        formula: producto.indicador.formula,
        lineaBase: producto.indicador.lineaBase,
        meta2030: producto.indicador.meta2030,
        fisica: producto.fisica,
        cuentaConFinanciamiento: producto.cuentaConFinanciamiento ? 'SÍ' : 'NO',
        presupuestoTotal: sumarProgramacion(producto.presupuesto),
        presupuesto: producto.presupuesto,
      });
    });
  });

  return filas;
}

// ---------------------------------------------------------------------------
// Filas de la Matriz "B" (33 columnas, nivel resultado)
// ---------------------------------------------------------------------------

export interface FilaMatrizB extends CabeceraPad {
  codResultadoTerritorial: string;
  resultadoTerritorial: string;
  indicador: string;
  formula: string;
  lineaBase: number | null;
  meta2030: number | null;
  fisica: ProgramacionAnual;
  presupuestoReferencial: number;
  presupuesto: ProgramacionAnual;
}

/**
 * La Matriz "B" copia el contenido de la "A" a nivel de resultado y le
 * antepone la articulación nacional, internacional y sectorial.
 */
export function construirMatrizB(
  cabecera: CabeceraPad,
  resultados: ResultadoPadForm[],
  correlativoBase = 1,
): FilaMatrizB[] {
  return resultados.map((resultado, indice) => {
    const presupuesto = consolidarPresupuesto(resultado.productos);
    return {
      ...cabecera,
      codResultadoTerritorial: codigoResultado(
        cabecera.codGeografico,
        cabecera.codLineamiento,
        correlativoBase + indice,
      ),
      resultadoTerritorial: redactarResultado(
        resultado.accionCambio,
        resultado.variableResultado,
      ),
      indicador: resultado.indicador.indicador,
      formula: resultado.indicador.formula,
      lineaBase: resultado.indicador.lineaBase,
      meta2030: resultado.indicador.meta2030,
      fisica: resultado.fisica,
      presupuestoReferencial: sumarProgramacion(presupuesto),
      presupuesto,
    };
  });
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

/** Guía PAD §4.5.2.f: el indicador nunca se formula sobre la ejecución presupuestaria. */
const INDICADOR_PRESUPUESTARIO = /(presupuest|ejecuci[oó]n financiera|bolivianos|\bbs\.?\b)/i;
const PRETERITO_COMPUESTO = /^se\s+ha\b/i;

function esProgresiva(programacion: ProgramacionAnual): boolean {
  let anterior: number | null = null;
  for (const anio of GESTIONES_PAD) {
    const valor = programacion[anio];
    if (valor === null || valor === undefined || (valor as unknown) === '') continue;
    const actual = Number(valor);
    if (anterior !== null && actual < anterior) return false;
    anterior = actual;
  }
  return true;
}

function tieneDecimales(programacion: ProgramacionAnual): boolean {
  return GESTIONES_PAD.some(anio => {
    const valor = Number(programacion[anio]);
    return Number.isFinite(valor) && !Number.isInteger(valor);
  });
}

function validarIndicador(
  indicador: IndicadorPad,
  seccion: string,
  hallazgos: Hallazgo[],
): void {
  if (!indicador.indicador.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion,
      mensaje: 'Registre el indicador: es la variable de medición del avance.',
    });
    return;
  }
  if (INDICADOR_PRESUPUESTARIO.test(indicador.indicador)) {
    hallazgos.push({
      severidad: 'aviso',
      seccion,
      mensaje:
        'El indicador no debe formularse en función de la ejecución presupuestaria, sino de la programación física (Guía PAD §4.5.2.f).',
    });
  }
  if (indicador.meta2030 === null) {
    hallazgos.push({
      severidad: 'error',
      seccion,
      mensaje: 'Falta la meta 2030 del indicador.',
    });
  }
  if (indicador.anioLineaBase !== null && indicador.anioLineaBase < 2025) {
    hallazgos.push({
      severidad: 'aviso',
      seccion,
      mensaje: 'El año base de la línea base no debe ser anterior a la gestión 2025.',
    });
  }
}

/**
 * Contrasta el borrador contra las reglas verificables de la Guía PAD.
 * Los "error" bloquean el registro; los "aviso" solo advierten.
 */
export function validarMatrices(
  cabecera: CabeceraPad,
  resultados: ResultadoPadForm[],
): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];

  if (!cabecera.codEjePgdesa) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Matriz B — Nacional',
      mensaje: 'Seleccione el eje del PGDESA y su componente PDESA.',
    });
  }
  if (!cabecera.codSector) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Matriz B — Sectorial',
      mensaje: 'Registre el código de sector del clasificador presupuestario.',
    });
  }
  if (cabecera.codSector && !cabecera.codResultadoSectorial) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Matriz B — Sectorial',
      mensaje:
        'Si el PDS no define un resultado correspondiente, consigne el código del sector seguido de "0".',
    });
  }
  if (!cabecera.codGeografico) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Matriz A — Territorial',
      mensaje: 'El código geográfico es el prefijo del código de resultado territorial.',
    });
  }
  if (!cabecera.politica.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Matriz A — Política',
      mensaje: 'La política organiza la propuesta y articula PAD-PGDESA-PDESA-PDS (§4.2).',
    });
  } else if (cabecera.politica.trim().split(/\s+/).length > 12) {
    hallazgos.push({
      severidad: 'aviso',
      seccion: 'Matriz A — Política',
      mensaje: 'La política es un texto corto que define ámbitos o temas de intervención.',
    });
  }
  if (!cabecera.codLineamiento || !cabecera.lineamiento.trim()) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Matriz A — Lineamiento',
      mensaje:
        'El lineamiento estratégico es el primer elemento de la matriz: sin él no se codifican los resultados (§4.3).',
    });
  }

  if (!resultados.length) {
    hallazgos.push({
      severidad: 'error',
      seccion: 'Resultados',
      mensaje: 'El PAD necesita al menos un resultado territorial.',
    });
  }

  resultados.forEach((resultado, indice) => {
    const etiqueta = `Resultado ${indice + 1}`;
    const redactado = redactarResultado(
      resultado.accionCambio,
      resultado.variableResultado,
    );
    if (!redactado) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'Redacte el resultado: acción de cambio + variable.',
      });
    } else if (!PRETERITO_COMPUESTO.test(redactado)) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje: 'El resultado se redacta en tiempo pretérito (§4.4).',
      });
    }
    validarIndicador(resultado.indicador, etiqueta, hallazgos);
    if (!esProgresiva(resultado.fisica)) {
      hallazgos.push({
        severidad: 'aviso',
        seccion: etiqueta,
        mensaje:
          'La programación física refleja el progreso gradual hacia la meta: no debería decrecer (§4.5.2.g).',
      });
    }
    if (!resultado.productos.length) {
      hallazgos.push({
        severidad: 'error',
        seccion: etiqueta,
        mensaje: 'El resultado se alcanza mediante productos territoriales.',
      });
    }

    resultado.productos.forEach((producto, j) => {
      const etiquetaProducto = `${etiqueta} · Producto ${j + 1}`;
      if (!producto.denominacion.trim()) {
        hallazgos.push({
          severidad: 'error',
          seccion: etiquetaProducto,
          mensaje: 'Registre el bien, servicio o intervención concreta.',
        });
      }
      if (!producto.territorializacion.trim()) {
        hallazgos.push({
          severidad: 'aviso',
          seccion: etiquetaProducto,
          mensaje: 'Falta la territorialización: dónde se implementa el producto.',
        });
      }
      if (!producto.responsable.trim()) {
        hallazgos.push({
          severidad: 'error',
          seccion: etiquetaProducto,
          mensaje: 'Identifique la entidad responsable de la ejecución.',
        });
      }
      validarIndicador(producto.indicador, etiquetaProducto, hallazgos);
      if (tieneDecimales(producto.presupuesto)) {
        hallazgos.push({
          severidad: 'aviso',
          seccion: etiquetaProducto,
          mensaje: 'El presupuesto se expresa en bolivianos sin decimales.',
        });
      }
      if (
        producto.cuentaConFinanciamiento &&
        sumarProgramacion(producto.presupuesto) === 0
      ) {
        hallazgos.push({
          severidad: 'aviso',
          seccion: etiquetaProducto,
          mensaje:
            'Marcado con financiamiento pero sin presupuesto quinquenal asignado.',
        });
      }
    });
  });

  return hallazgos;
}

export function tieneErrores(hallazgos: Hallazgo[]): boolean {
  return hallazgos.some(h => h.severidad === 'error');
}
