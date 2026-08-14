import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface BorradorMatrizPAD {
  id: string;
  gestion: number;
  estado: 'BORRADOR' | 'COMPLETO';
  datos: Record<string, unknown>;
  id_resultado_pad: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface MatrizGestionResponse {
  gestion: number;
  fecha: string;
  total_filas: number;
  filas: any[];
}

/**
 * Servicio del módulo Matrices PAD (wizard 11 pasos, guardado incremental).
 *
 * Contrato del PATCH por sección:
 *   guardarSeccion(id, seccion, valores) → PATCH {"seccion": ..., "valores": ...}
 * Los visualizadores Matriz A/B leen en vivo:
 *   GET /borradores-matriz-pad/{id}/matriz_a|b/
 */
@Injectable({ providedIn: 'root' })
export class MatricesPadService {
  private base = '/articulacion/borradores-matriz-pad';

  constructor(private api: ApiService) {}

  listar(
    params?: Record<string, string | number | boolean>,
  ): Observable<{ count: number; results: BorradorMatrizPAD[] }> {
    return this.api.get<{ count: number; results: BorradorMatrizPAD[] }>(
      `${this.base}/`,
      params,
    );
  }

  crear(datos?: Record<string, unknown>): Observable<BorradorMatrizPAD> {
    return this.api.post<BorradorMatrizPAD>(`${this.base}/`, datos || {});
  }

  obtener(id: string): Observable<BorradorMatrizPAD> {
    return this.api.get<BorradorMatrizPAD>(`${this.base}/${id}/`);
  }

  guardarSeccion(
    id: string,
    seccion: string,
    valores: unknown,
  ): Observable<BorradorMatrizPAD> {
    return this.api.patch<BorradorMatrizPAD>(`${this.base}/${id}/`, {
      seccion,
      valores,
    });
  }

  actualizarDatos(id: string, datos: unknown): Observable<BorradorMatrizPAD> {
    return this.api.patch<BorradorMatrizPAD>(`${this.base}/${id}/`, { datos });
  }

  materializar(id: string): Observable<any> {
    return this.api.post<any>(`${this.base}/${id}/materializar/`, {});
  }

  matrizA(id: string): Observable<any[]> {
    return this.api.get<any[]>(`${this.base}/${id}/matriz_a/`);
  }

  matrizB(id: string): Observable<any[]> {
    return this.api.get<any[]>(`${this.base}/${id}/matriz_b/`);
  }

  /** Matriz A (27 columnas) ACUMULADA de la gestión completa (todos los
   *  resultados materializados de la gestión en una sola matriz). */
  matrizAGestion(gestion: number): Observable<MatrizGestionResponse> {
    return this.api.get<MatrizGestionResponse>(
      '/articulacion/matrices/matriz_a_gestion/',
      { gestion },
    );
  }

  /** Matriz B (34 columnas) ACUMULADA de la gestión completa. */
  matrizBGestion(gestion: number): Observable<MatrizGestionResponse> {
    return this.api.get<MatrizGestionResponse>(
      '/articulacion/matrices/matriz_b_gestion/',
      { gestion },
    );
  }

  eliminar(id: string): Observable<unknown> {
    return this.api.delete(`${this.base}/${id}/`);
  }
}
