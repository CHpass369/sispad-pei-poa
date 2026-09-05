import { Injectable } from '@angular/core';
import { Observable, concatMap, map, of } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import {
  OpcionCatalogo,
  SaldoUnidadCategoria,
  SaldoUnidadCategoriaForm,
} from './poau-saldos.model';

const RUTA = '/articulacion/saldos-unidad-categoria/';

/**
 * Acceso a los techos por unidad y categoría programática.
 *
 * Antes vivían en un arreglo estático del bundle: consultarlos era una llamada
 * a función y cambiarlos costaba un despliegue. Ahora salen de la base, así que
 * toda lectura es asíncrona.
 */
@Injectable({ providedIn: 'root' })
export class PoauSaldosService {
  constructor(private api: ApiService) {}

  /**
   * Todas las páginas de una ruta paginada, concatenadas.
   *
   * DRF pagina por defecto: quedarse con la primera página mostraría un
   * subconjunto del catálogo sin avisar, que es peor que fallar.
   */
  private todasLasPaginas<T>(ruta: string, pagina = 1, acumulado: T[] = []): Observable<T[]> {
    const separador = ruta.includes('?') ? '&' : '?';
    return this.api.get<any>(`${ruta}${separador}page=${pagina}`).pipe(
      concatMap(respuesta => {
        if (Array.isArray(respuesta)) {
          return of([...acumulado, ...respuesta] as T[]);
        }
        const actual = Array.isArray(respuesta?.results) ? respuesta.results : [];
        const todos = [...acumulado, ...actual] as T[];
        return respuesta?.next
          ? this.todasLasPaginas<T>(ruta, pagina + 1, todos)
          : of(todos);
      }),
    );
  }

  listar(codigoUnidad?: string): Observable<SaldoUnidadCategoria[]> {
    const ruta = codigoUnidad
      ? `${RUTA}?unidad=${encodeURIComponent(codigoUnidad)}`
      : RUTA;
    return this.todasLasPaginas<SaldoUnidadCategoria>(ruta);
  }

  crear(datos: SaldoUnidadCategoriaForm): Observable<SaldoUnidadCategoria> {
    return this.api.post<SaldoUnidadCategoria>(RUTA, datos);
  }

  editar(id: string, datos: SaldoUnidadCategoriaForm): Observable<SaldoUnidadCategoria> {
    return this.api.patch<SaldoUnidadCategoria>(`${RUTA}${id}/`, datos);
  }

  borrar(id: string): Observable<void> {
    return this.api.delete<void>(`${RUTA}${id}/`);
  }

  fuentes(): Observable<OpcionCatalogo[]> {
    return this.todasLasPaginas<OpcionCatalogo>('/fuentes/');
  }

  organismos(): Observable<OpcionCatalogo[]> {
    return this.todasLasPaginas<OpcionCatalogo>('/organismos/');
  }

  /** Catálogo de unidades ya recortado al alcance del usuario (ADR-003). */
  unidades(): Observable<{ codigo: string; nombre: string; id: string }[]> {
    return this.api
      .get<any>('/articulacion/matriz-poau/?incluir_unidades=1')
      .pipe(map(respuesta => respuesta?.unidades ?? []));
  }
}
