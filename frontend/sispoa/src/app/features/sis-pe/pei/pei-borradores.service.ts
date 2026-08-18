import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

export interface PermisosRevision {
  es_autor: boolean;
  es_aprobador: boolean;
  editar: boolean;
  validar: boolean;
  aprobar: boolean;
  observar: boolean;
  borrar: boolean;
}

export interface BorradorMatrizPEI {
  id: string;
  gestion: number;
  estado: 'BORRADOR' | 'COMPLETO';
  datos: Record<string, any>;
  id_resultado_pei: string | null;
  estado_revision?: 'PENDIENTE' | 'VALIDADO' | 'OBSERVADO' | 'APROBADO';
  estado_revision_display?: string;
  observacion?: string;
  validado_por_nombre?: string;
  aprobado_por_nombre?: string;
  observado_por_nombre?: string;
  permisos?: PermisosRevision;
  created_at?: string;
  updated_at?: string;
}

/**
 * Borradores de la Matriz PEI: guardado incremental por sección,
 * materialización y circuito de revisión. Espejo de MatricesPadService.
 */
@Injectable({ providedIn: 'root' })
export class PeiBorradoresService {
  private base = '/articulacion/borradores-matriz-pei';

  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>):
    Observable<{ count: number; results: BorradorMatrizPEI[] }> {
    return this.api.get<{ count: number; results: BorradorMatrizPEI[] }>(
      `${this.base}/`, params,
    );
  }

  crear(datos?: Record<string, unknown>): Observable<BorradorMatrizPEI> {
    return this.api.post<BorradorMatrizPEI>(`${this.base}/`, datos || {});
  }

  obtener(id: string): Observable<BorradorMatrizPEI> {
    return this.api.get<BorradorMatrizPEI>(`${this.base}/${id}/`);
  }

  guardarSeccion(id: string, seccion: string, valores: unknown): Observable<BorradorMatrizPEI> {
    return this.api.patch<BorradorMatrizPEI>(`${this.base}/${id}/`, { seccion, valores });
  }

  materializar(id: string): Observable<any> {
    return this.api.post<any>(`${this.base}/${id}/materializar/`, {});
  }

  /** Filas de la matriz PEI (46 columnas) de este borrador. */
  matriz(id: string): Observable<any[]> {
    return this.api.get<any[]>(`${this.base}/${id}/matriz/`);
  }

  validar(id: string): Observable<BorradorMatrizPEI> {
    return this.api.post<BorradorMatrizPEI>(`${this.base}/${id}/validar/`, {});
  }

  aprobar(id: string): Observable<BorradorMatrizPEI> {
    return this.api.post<BorradorMatrizPEI>(`${this.base}/${id}/aprobar/`, {});
  }

  observar(id: string, observacion: string): Observable<BorradorMatrizPEI> {
    return this.api.post<BorradorMatrizPEI>(`${this.base}/${id}/observar/`, { observacion });
  }

  eliminar(id: string): Observable<unknown> {
    return this.api.delete(`${this.base}/${id}/`);
  }
}
