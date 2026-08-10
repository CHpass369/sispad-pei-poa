import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ProyectoV2 {
  id: string;
  codigo_interno: string;
  codigo_sisin: string;
  nombre: string;
  gestion: number;
  fase: string;
  estado: string;
  costo_total: string;
  ejecucion_acumulada: string;
}

export interface CadenaPaso {
  tipo: string;
  codigo: string;
  nombre: string;
}

export interface CondicionV2 {
  id: string;
  proyecto: string;
  descripcion: string;
  cumplida: boolean;
}

export interface DocumentoV2 {
  id: string;
  proyecto: string;
  tipo: string;
  nombre: string;
  estado: string;
}

export interface CostoV2 {
  id: string;
  proyecto: string;
  concepto: string;
  monto: string;
  anio: number;
}

export interface PresupuestoProyecto {
  costo_total: string;
  ejecucion_acumulada: string;
  saldo: string;
  costos_detalle: string;
}

interface Paginado<T> {
  count: number;
  results: T[];
}

/** Servicio tipado del SIS-PRO V2 (ADR-002): consume exclusivamente /api/v2. */
@Injectable({ providedIn: 'root' })
export class SisProService {
  private base = environment.apiUrlV2 + '/sis-pro';

  constructor(private http: HttpClient) {}

  private params(values?: Record<string, string | number | boolean>): HttpParams {
    let p = new HttpParams();
    if (values) {
      Object.entries(values).forEach(([k, v]) => {
        if (v !== undefined && v !== null) p = p.set(k, String(v));
      });
    }
    return p;
  }

  listarProyectos(params?: { gestion?: number; fase?: string }): Observable<Paginado<ProyectoV2>> {
    return this.http.get<Paginado<ProyectoV2>>(`${this.base}/proyectos/`, { params: this.params(params) });
  }

  crearProyecto(data: Partial<ProyectoV2>): Observable<ProyectoV2> {
    return this.http.post<ProyectoV2>(`${this.base}/proyectos/`, data);
  }

  obtenerProyecto(id: string): Observable<ProyectoV2> {
    return this.http.get<ProyectoV2>(`${this.base}/proyectos/${id}/`);
  }

  cadena(id: string): Observable<CadenaPaso[]> {
    return this.http.get<CadenaPaso[]>(`${this.base}/proyectos/${id}/cadena/`);
  }

  avanzarFase(id: string): Observable<ProyectoV2> {
    return this.http.post<ProyectoV2>(`${this.base}/proyectos/${id}/avanzar_fase/`, {});
  }

  presupuesto(id: string): Observable<PresupuestoProyecto> {
    return this.http.get<PresupuestoProyecto>(`${this.base}/proyectos/${id}/presupuesto/`);
  }

  condiciones(id: string): Observable<CondicionV2[]> {
    return this.http.get<CondicionV2[]>(`${this.base}/proyectos/${id}/condiciones/`);
  }

  documentos(id: string): Observable<DocumentoV2[]> {
    return this.http.get<DocumentoV2[]>(`${this.base}/proyectos/${id}/documentos/`);
  }

  crearCondicion(proyecto: string, descripcion: string): Observable<CondicionV2> {
    return this.http.post<CondicionV2>(`${this.base}/condiciones/`, { proyecto, descripcion });
  }

  crearDocumento(proyecto: string, tipo: string, nombre: string): Observable<DocumentoV2> {
    return this.http.post<DocumentoV2>(`${this.base}/documentos/`, { proyecto, tipo, nombre });
  }
}
