import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface PoaV2 {
  id: string;
  gestion: number;
  codigo: string;
  nombre: string;
  version_pei: string | null;
  estado: string;
}

export interface AccionPoaV2 {
  id: string;
  poa: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  nodo_pei: string | null;
  nodo_pei_codigo: string | null;
  estado: string;
}

export interface ResumenPresupuesto {
  poa: string;
  codigo: string;
  gestion: number;
  fisica: { programado: string; ejecutado: string };
  financiera: { programado: string; ejecutado: string };
  actividades: number;
}

export interface ValidacionTecho {
  excede: boolean;
  techo: string;
  formulado: string;
  mensaje: string;
}

interface Paginado<T> {
  count: number;
  results: T[];
}

/** Servicio tipado del SIS-POA V2 (ADR-002): consume exclusivamente /api/v2. */
@Injectable({ providedIn: 'root' })
export class SisPoaService {
  private base = environment.apiUrlV2 + '/sis-poa';

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

  listarPoas(params?: { gestion?: number; estado?: string }): Observable<Paginado<PoaV2>> {
    return this.http.get<Paginado<PoaV2>>(`${this.base}/poas/`, { params: this.params(params) });
  }

  crearPoa(data: Partial<PoaV2>): Observable<PoaV2> {
    return this.http.post<PoaV2>(`${this.base}/poas/`, data);
  }

  obtenerPoa(id: string): Observable<PoaV2> {
    return this.http.get<PoaV2>(`${this.base}/poas/${id}/`);
  }

  accionesDePoa(id: string): Observable<AccionPoaV2[]> {
    return this.http.get<AccionPoaV2[]>(`${this.base}/poas/${id}/acciones/`);
  }

  resumenPresupuesto(id: string): Observable<ResumenPresupuesto> {
    return this.http.get<ResumenPresupuesto>(`${this.base}/poas/${id}/resumen_presupuesto/`);
  }

  validarTecho(id: string): Observable<ValidacionTecho> {
    return this.http.get<ValidacionTecho>(`${this.base}/poas/${id}/validar_techo/`);
  }

  crearAccion(poa: string, codigo: string, nombre: string): Observable<AccionPoaV2> {
    return this.http.post<AccionPoaV2>(`${this.base}/acciones/`, { poa, codigo, nombre });
  }
}
