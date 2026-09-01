import {
  Observable,
  OperatorFunction,
  catchError,
  distinctUntilChanged,
  map,
  of,
  pipe,
  switchMap,
  timer
} from 'rxjs';

/**
 * Política global para búsquedas incrementales de PIP.
 *
 * Todos los autocompletados que consulten una API deberían utilizar
 * esta configuración.
 */
export const AUTOCOMPLETE_CONFIG = {
  debounceMs: 500,
  minChars: 3,
  limit: 12
} as const;

export interface AutocompleteOptions {
  debounceMs?: number;
  minChars?: number;
}

/**
 * Normaliza el texto escrito por el usuario.
 */
function normalizarConsulta(valor: string | null | undefined): string {
  return (valor ?? '')
    .trim()
    .replace(/\s+/g, ' ');
}

/**
 * Operador estándar para autocompletados remotos de PIP.
 *
 * Características:
 * - normaliza la consulta;
 * - evita búsquedas repetidas;
 * - cancela inmediatamente la búsqueda anterior;
 * - espera antes de lanzar una nueva petición;
 * - exige un mínimo de caracteres;
 * - captura errores sin destruir el stream.
 *
 * Ejemplo:
 *
 * this.busqueda$.pipe(
 *   autocompleteSearch(
 *     q => this.api.buscar(q, AUTOCOMPLETE_CONFIG.limit),
 *     []
 *   )
 * )
 */
export function autocompleteSearch<T>(
  buscar: (consulta: string) => Observable<T>,
  resultadoVacio: T,
  opciones: AutocompleteOptions = {}
): OperatorFunction<string, T> {

  const debounceMs =
    opciones.debounceMs ?? AUTOCOMPLETE_CONFIG.debounceMs;

  const minChars =
    opciones.minChars ?? AUTOCOMPLETE_CONFIG.minChars;

  return pipe(
    map(valor => normalizarConsulta(valor)),

    distinctUntilChanged(),

    /*
     * switchMap está deliberadamente antes del temporizador.
     *
     * De esta forma una nueva tecla cancela inmediatamente
     * cualquier búsqueda HTTP anterior.
     */
    switchMap(consulta => {

      if (consulta.length < minChars) {
        return of(resultadoVacio);
      }

      return timer(debounceMs).pipe(
        switchMap(() =>
          buscar(consulta).pipe(
            catchError(error => {
              console.error(
                '[PIP autocomplete] Error de búsqueda:',
                error
              );

              return of(resultadoVacio);
            })
          )
        )
      );
    })
  );
}
