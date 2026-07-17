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
  actividad_id: number;
  actividad_descripcion?: string;
  estado_semaforo: 'verde' | 'amarillo' | 'rojo';
  avance_fisico?: number;
  avance_financiero?: number;
}

export interface DashboardData {
  total_actividades?: number;
  en_tiempo?: number;
  con_riesgo?: number;
  retrasadas?: number;
  avance_fisico_promedio?: number;
  avance_financiero_promedio?: number;
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
    return this.api.get<ReporteSeguimiento[]>('/seguimiento/reportes/', params);
  }

  crearReporte(data: Partial<ReporteSeguimiento>): Observable<ReporteSeguimiento> {
    return this.api.post<ReporteSeguimiento>('/seguimiento/reportes/', data);
  }

  obtenerSemaforo(): Observable<Semaforo[]> {
    return this.api.get<Semaforo[]>('/seguimiento/entradas/semforo/');
  }

  obtenerDashboard(): Observable<DashboardData> {
    return this.api.get<DashboardData>('/seguimiento/entradas/dashboard/');
  }

  listarAlertasActivas(): Observable<Alerta[]> {
    return this.api.get<Alerta[]>('/seguimiento/alertas/activas/');
  }

  resolverAlerta(alertaId: number, data?: { resolucion?: string }): Observable<void> {
    return this.api.post<void>(`/seguimiento/alertas/${alertaId}/resolver/`, data);
  }
}
