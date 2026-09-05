/**
 * Techo presupuestario de una unidad organizacional en una categoría
 * programática, tal como lo devuelve
 * `/api/v1/articulacion/saldos-unidad-categoria/`.
 *
 * Reemplaza al arreglo estático `saldos-unidad-categoria.catalogo.ts`, que
 * viajaba dentro del bundle: cambiar un monto exigía compilar y desplegar.
 */
export interface SaldoUnidadCategoria {
  id: string;
  /** Identificador de la unidad. Es lo que se manda al crear o editar. */
  unidad: string;
  unidad_codigo: string;
  unidad_nombre: string;
  gestion: number;
  categoria_programatica: string;
  denominacion: string;
  /** Nulo en las filas heredadas de la planilla, que no declaran fuente. */
  fuente: string | null;
  fuente_codigo: string | null;
  fuente_denominacion: string | null;
  organismo: string | null;
  organismo_codigo: string | null;
  organismo_denominacion: string | null;
  /** Llega como cadena: DRF serializa `DecimalField` en texto para no perder precisión. */
  saldo: string;
  /** Bs. ya programados contra esta categoría, según lo guardado en la base. */
  programado: string;
  /** `saldo` menos `programado`: lo que de verdad queda para programar. */
  disponible: string;
  filas_origen: number;
  observacion: string;
  activo: boolean;
  created_at?: string;
  updated_at?: string;
}

/** Lo que se manda al crear o editar. */
export interface SaldoUnidadCategoriaForm {
  unidad: string;
  categoria_programatica: string;
  denominacion: string;
  fuente: string | null;
  organismo: string | null;
  saldo: string;
  observacion: string;
  activo: boolean;
}

export interface OpcionCatalogo {
  id: string;
  codigo: string;
  denominacion: string;
}

export function formularioVacio(): SaldoUnidadCategoriaForm {
  return {
    unidad: '',
    categoria_programatica: '',
    denominacion: '',
    fuente: null,
    organismo: null,
    saldo: '',
    observacion: '',
    activo: true,
  };
}

export function aFormulario(saldo: SaldoUnidadCategoria): SaldoUnidadCategoriaForm {
  return {
    unidad: saldo.unidad,
    categoria_programatica: saldo.categoria_programatica,
    denominacion: saldo.denominacion,
    fuente: saldo.fuente,
    organismo: saldo.organismo,
    saldo: saldo.saldo,
    observacion: saldo.observacion,
    activo: saldo.activo,
  };
}

/**
 * Los saldos llegan como texto y hay que sumarlos para mostrar el total.
 *
 * `Number` sobre una cadena vacía da 0, que acá sería un techo inventado; por
 * eso lo que no parsea se descarta en vez de contarse como cero.
 */
export function totalDeSaldos(filas: SaldoUnidadCategoria[]): number {
  return filas.reduce((suma, fila) => {
    const valor = Number(fila.saldo);
    return Number.isFinite(valor) ? suma + valor : suma;
  }, 0);
}

/**
 * Valida el formulario antes de mandarlo.
 *
 * El backend valida igual —es la autoridad— pero un mensaje inmediato evita el
 * viaje de ida y vuelta para errores que se ven desde acá.
 */
export function erroresDeFormulario(form: SaldoUnidadCategoriaForm): string[] {
  const errores: string[] = [];
  if (!form.unidad) {
    errores.push('Elija la unidad organizacional.');
  }
  if (!form.categoria_programatica.trim()) {
    errores.push('Escriba la categoría programática.');
  }
  // Se permite el negativo a propósito: la planilla marca saldos negativos y
  // redondearlos a cero inventaría un margen que la unidad no tiene.
  if (form.saldo.trim() === '' || !Number.isFinite(Number(form.saldo))) {
    errores.push('El saldo tiene que ser un número.');
  }
  return errores;
}
