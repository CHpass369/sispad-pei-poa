import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface Notificacion {
  id?: number;
  titulo?: string;
  mensaje?: string;
  tipo?: string;
  leida?: boolean;
  fecha_creacion?: string;
  enlace?: string;
}

export interface ResumenNotificaciones {
  total?: number;
  no_leidas?: number;
}

export interface PreferenciaNotificacion {
  id?: number;
  evento?: string;
  email_habilitado?: boolean;
  in_app_habilitado?: boolean;
  push_habilitado?: boolean;
}

@Injectable()
export class NotificacionesService {
  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>): Observable<Notificacion[]> {
    return this.api.get<Notificacion[]>('/notificaciones/', params);
  }

  marcarLeida(id: number): Observable<void> {
    return this.api.post<void>(`/notificaciones/${id}/marcar-leida/`);
  }

  marcarTodasLeidas(): Observable<void> {
    return this.api.post<void>('/notificaciones/marcar-todas-leidas/');
  }

  obtenerResumen(): Observable<ResumenNotificaciones> {
    return this.api.get<ResumenNotificaciones>('/notificaciones/resumen/');
  }

  obtenerPreferencias(): Observable<PreferenciaNotificacion[]> {
    return this.api.get<PreferenciaNotificacion[]>('/notificaciones/preferencias/');
  }

  actualizarPreferencia(id: number, data: Partial<PreferenciaNotificacion>): Observable<PreferenciaNotificacion> {
    return this.api.put<PreferenciaNotificacion>(`/notificaciones/preferencias/${id}/`, data);
  }
}
