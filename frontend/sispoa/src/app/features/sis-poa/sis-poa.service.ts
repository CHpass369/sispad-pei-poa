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

export interface TechoV2 {
  id: string;
  gestion: number;
  monto_total: string;
  fuente: string;
  fuente_codigo: string;
  fuente_nombre: string;
  organismo: string | null;
  concepto: string;
  descripcion: string;
  activo: boolean;
  total_recursos?: string;
  total_gastos_obligatorios?: string;
  monto_distribuido?: string;
  saldo_disponible?: string;
}

export interface RecursoTechoV2 {
  id: string;
  techo: string;
  rubro: string;
  rubro_descripcion: string;
  fuente: string;
  fuente_codigo: string;
  fuente_nombre: string;
  organismo: string | null;
  organismo_codigo: string | null;
  entidad_otorgante: string;
  concepto: string;
  monto: string;
  orden: number;
}

export interface GastoObligatorioV2 {
  id: string;
  techo: string;
  da: string | null;
  ue: string | null;
  programa: string | null;
  programa_codigo: string | null;
  fuente: string;
  fuente_codigo: string;
  fuente_nombre: string;
  organismo: string | null;
  objeto_gasto: string | null;
  denominacion: string;
  base_legal: string;
  monto: string;
  activo: boolean;
  orden: number;
}

export interface ResumenTecho {
  techo_id: string;
  gestion: number;
  monto_total: string;
  total_recursos: string;
  total_gastos_obligatorios: string;
  monto_distribuido: string;
  saldo_disponible: string;
  excede: boolean;
}

export interface ControlDistribucion {
  monto_solicitado: string;
  saldo_disponible: string;
  excede: boolean;
}

export interface ProgramacionFila {
  actividad_id: string;
  actividad_codigo: string;
  actividad_nombre: string;
  anio: number;
  tipo: string;
  programado: string;
  ejecutado: string;
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

  programacionesDePoa(id: string): Observable<{ poa: string; codigo: string; filas: ProgramacionFila[] }> {
    return this.http.get<{ poa: string; codigo: string; filas: ProgramacionFila[] }>(
      `${this.base}/poas/${id}/programaciones/`,
    );
  }

  listarTechos(params?: { gestion?: number; activo?: boolean }): Observable<Paginado<TechoV2>> {
    return this.http.get<Paginado<TechoV2>>(`${this.base}/techos/`, { params: this.params(params) });
  }

  crearTecho(data: Partial<TechoV2>): Observable<TechoV2> {
    return this.http.post<TechoV2>(`${this.base}/techos/`, data);
  }

  actualizarTecho(id: string, data: Partial<TechoV2>): Observable<TechoV2> {
    return this.http.patch<TechoV2>(`${this.base}/techos/${id}/`, data);
  }

  eliminarTecho(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/techos/${id}/`);
  }

  resumenTecho(id: string): Observable<ResumenTecho> {
    return this.http.get<ResumenTecho>(`${this.base}/techos/${id}/resumen/`);
  }

  controlDistribucion(id: string, monto: number): Observable<ControlDistribucion> {
    return this.http.get<ControlDistribucion>(
      `${this.base}/techos/${id}/control_distribucion/`,
      { params: this.params({ monto }) },
    );
  }

  listarRecursos(params?: { techo?: string }): Observable<RecursoTechoV2[]> {
    return this.http.get<RecursoTechoV2[]>(`${this.base}/techo-recursos/`, {
      params: this.params(params),
    });
  }

  crearRecurso(data: Partial<RecursoTechoV2>): Observable<RecursoTechoV2> {
    return this.http.post<RecursoTechoV2>(`${this.base}/techo-recursos/`, data);
  }

  eliminarRecurso(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/techo-recursos/${id}/`);
  }

  listarGastosObligatorios(params?: { techo?: string; activo?: boolean }): Observable<GastoObligatorioV2[]> {
    return this.http.get<GastoObligatorioV2[]>(`${this.base}/techo-gastos-obligatorios/`, {
      params: this.params(params),
    });
  }

  crearGastoObligatorio(data: Partial<GastoObligatorioV2>): Observable<GastoObligatorioV2> {
    return this.http.post<GastoObligatorioV2>(`${this.base}/techo-gastos-obligatorios/`, data);
  }

  eliminarGastoObligatorio(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/techo-gastos-obligatorios/${id}/`);
  }
}
