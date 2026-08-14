import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface FiscalYear {
  id: string;
  anio: number;
  estado: string;
  estado_display: string;
  descripcion: string;
  anio_inicio_plurianual: number | null;
  anio_fin_plurianual: number | null;
  fecha_apertura: string | null;
  fecha_cierre: string | null;
  activa: boolean;
  gestion_anterior: number | null;
}

export interface FiscalYearInput {
  anio: number;
  descripcion?: string;
  anio_inicio_plurianual?: number | null;
  anio_fin_plurianual?: number | null;
  heredar_de?: number | null;
}

interface Paginado<T> {
  count: number;
  results: T[];
}

/** Servicio tipado del ciclo presupuestario SIS-POA (ADR-002): V2 puro. */
@Injectable({ providedIn: 'root' })
export class BudgetService {
  private base = environment.apiUrlV2 + '/sis-poa/budget';

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

  listar(params?: { anio?: number; estado?: string }): Observable<Paginado<FiscalYear>> {
    return this.http.get<Paginado<FiscalYear>>(`${this.base}/fiscal-years/`, {
      params: this.params(params),
    });
  }

  crear(data: FiscalYearInput): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/`, data);
  }

  habilitar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/enable/`, {});
  }

  cerrar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/close/`, {});
  }
}
