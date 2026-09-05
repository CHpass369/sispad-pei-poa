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

/**
 * Lo que edita el formulario.
 *
 * `saldo` NO es `string`: el campo se pinta con `<input type="number">` y el
 * `NumberValueAccessor` de Angular escribe en el modelo `parseFloat(valor)` —o
 * `null` si se vacía—, nunca la cadena que se tipeó. Declararlo `string` hacía
 * que `saldo.trim()` reventara con `TypeError` en cuanto alguien escribía un
 * monto, y como la excepción sale del handler del click, el botón Guardar no
 * hacía absolutamente nada: ni petición, ni mensaje.
 */
export interface SaldoUnidadCategoriaForm {
  unidad: string;
  categoria_programatica: string;
  denominacion: string;
  fuente: string | null;
  organismo: string | null;
  saldo: string | number | null;
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
  if (!(form.categoria_programatica ?? '').trim()) {
    errores.push('Escriba la categoría programática.');
  }
  // Se permite el negativo a propósito: la planilla marca saldos negativos y
  // redondearlos a cero inventaría un margen que la unidad no tiene.
  if (montoDelFormulario(form.saldo) === null) {
    errores.push('El saldo tiene que ser un número.');
  }
  return errores;
}

/**
 * El monto del formulario como número, o `null` si no hay un monto utilizable.
 *
 * El campo llega como número cuando el usuario tipeó, como `null` cuando lo
 * vació, y como cadena cuando lo escribió el backend al abrir la edición. Los
 * tres casos pasan por acá para que nadie vuelva a suponer un `string`.
 */
export function montoDelFormulario(valor: string | number | null): number | null {
  if (valor === null || valor === undefined) { return null; }
  if (typeof valor === 'number') {
    return Number.isFinite(valor) ? valor : null;
  }
  const texto = valor.trim();
  if (texto === '') { return null; }
  const numero = Number(texto);
  return Number.isFinite(numero) ? numero : null;
}

/**
 * El formulario listo para viajar en el JSON.
 *
 * El monto sale como cadena de dos decimales a propósito. `<input
 * type="number">` entrega un float del navegador y el `DecimalField` de DRF
 * valida la precisión ANTES de redondear: un `1489783.005` mandado crudo muere
 * en un 400 por «no más de 2 decimales» en vez de guardarse. Fijar la cola acá
 * es lo mismo que hace el resto de los montos del POAU.
 */
export function aPayload(form: SaldoUnidadCategoriaForm): SaldoUnidadCategoriaForm {
  const monto = montoDelFormulario(form.saldo);
  return {
    ...form,
    saldo: monto === null ? '' : monto.toFixed(2),
  };
}
