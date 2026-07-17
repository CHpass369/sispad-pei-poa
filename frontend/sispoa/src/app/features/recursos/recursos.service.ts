import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface Recurso {
  id?: number;
  tipo: string;
  nombre: string;
  cantidad?: number;
  unidad?: string;
  disponibilidad?: string;
  asignado_a?: string;
  asignado_nombre?: string;
  costo_estimado?: number;
  periodo?: string;
  responsable?: string;
  responsable_nombre?: string;
  descripcion?: string;
  fecha_creacion?: string;
}

@Injectable()
export class RecursosService {
  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>): Observable<Recurso[]> {
    return this.api.get<Recurso[]>('/recursos/', params);
  }

  obtener(id: number): Observable<Recurso> {
    return this.api.get<Recurso>(`/recursos/${id}/`);
  }

  crear(data: Partial<Recurso>): Observable<Recurso> {
    return this.api.post<Recurso>('/recursos/', data);
  }
}
