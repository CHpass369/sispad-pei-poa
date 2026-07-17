import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface SolicitudModificacion {
  id?: number;
  tipo?: string;
  entidad?: string;
  entidad_id?: number;
  motivo?: string;
  informe_tecnico?: string;
  estado?: string;
  solicitado_por?: string;
  solicitado_por_nombre?: string;
  aprobado_por?: string;
  aprobado_por_nombre?: string;
  fecha_solicitud?: string;
  fecha_resolucion?: string;
  observaciones?: string;
}

@Injectable()
export class ModificacionesService {
  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>): Observable<SolicitudModificacion[]> {
    return this.api.get<SolicitudModificacion[]>('/solicitudes-modificacion/', params);
  }

  obtener(id: number): Observable<SolicitudModificacion> {
    return this.api.get<SolicitudModificacion>(`/solicitudes-modificacion/${id}/`);
  }

  crear(data: Partial<SolicitudModificacion>): Observable<SolicitudModificacion> {
    return this.api.post<SolicitudModificacion>('/solicitudes-modificacion/', data);
  }

  aprobar(id: number, data?: { observaciones?: string }): Observable<void> {
    return this.api.post<void>(`/solicitudes-modificacion/${id}/aprobar/`, data);
  }

  rechazar(id: number, data?: { observaciones?: string }): Observable<void> {
    return this.api.post<void>(`/solicitudes-modificacion/${id}/rechazar/`, data);
  }
}
