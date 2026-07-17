import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface Normativa {
  id?: number;
  titulo: string;
  tipo?: string;
  estado?: string;
  version?: string;
  fecha_vigencia?: string;
  contenido?: string;
  descripcion?: string;
  fecha_creacion?: string;
}

export interface ReglaNormativa {
  id?: number;
  normativa?: number;
  normativa_titulo?: string;
  regla?: string;
  descripcion?: string;
  orden?: number;
}

@Injectable()
export class NormativaService {
  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>): Observable<Normativa[]> {
    return this.api.get<Normativa[]>('/normativa/', params);
  }

  obtener(id: number): Observable<Normativa> {
    return this.api.get<Normativa>(`/normativa/${id}/`);
  }

  listarReglas(normativaId: number): Observable<ReglaNormativa[]> {
    return this.api.get<ReglaNormativa[]>(`/normativa/${normativaId}/reglas/`);
  }
}
