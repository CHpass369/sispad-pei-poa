import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface ReporteSeguimiento {
  id?: number;
  actividad?: number;
  actividad_descripcion?: string;
  avance_fisico?: number;
  avance_financiero?: number;
  monto_ejecutado?: number;
  monto_programado?: number;
  observaciones?: string;
  fecha_registro?: string;
  registro_por?: string;
}

export interface Semaforo {
  actividad_id: string;
  actividad_descripcion?: string;
  estado_semaforo: 'verde' | 'amarillo' | 'rojo';
  avance_fisico?: number;
  avance_financiero?: number;
}

export interface DashboardData {
  gestion: number;
  total_actividades?: number;
  semaforo?: { verde: number; amarillo: number; rojo: number };
  promedio_avance_fisico?: number;
  promedio_avance_financiero?: number;
}

export interface SemaforoResponse {
  gestion: number;
  resumen: { verde: number; amarillo: number; rojo: number; total: number };
  detalle: Record<'verde' | 'amarillo' | 'rojo', Array<{
    id: string;
    actividad_codigo: string;
    actividad_nombre: string;
    avance_fisico: number;
    avance_financiero: number;
  }>>;
}

export interface Alerta {
  id?: number;
  tipo?: string;
  severidad?: string;
  mensaje?: string;
  actividad?: number;
  actividad_descripcion?: string;
  leida?: boolean;
  fecha_creacion?: string;
}

@Injectable()
export class SeguimientoService {
  constructor(private api: ApiService) {}

  listarReportes(params?: Record<string, string | number | boolean>): Observable<ReporteSeguimiento[]> {
    return this.api.get<ReporteSeguimiento[]>('/reportes-seguimiento/', params);
  }

  crearReporte(data: Partial<ReporteSeguimiento>): Observable<ReporteSeguimiento> {
    return this.api.post<ReporteSeguimiento>('/reportes-seguimiento/', data);
  }

  /** Semáforo de la gestión habilitada (la resuelve el backend, ADR-007). */
  obtenerSemaforo(): Observable<SemaforoResponse> {
    return this.api.get<SemaforoResponse>('/entradas/semaforo/');
  }

  obtenerDashboard(): Observable<DashboardData> {
    return this.api.get<DashboardData>('/entradas/dashboard/');
  }

  listarAlertasActivas(): Observable<Alerta[]> {
    return this.api.get<Alerta[]>('/alertas/activas/');
  }

  resolverAlerta(alertaId: number, data?: { resolucion?: string }): Observable<void> {
    return this.api.post<void>(`/alertas/${alertaId}/resolver/`, data);
  }
}
