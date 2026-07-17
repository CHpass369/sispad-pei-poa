import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface Evaluacion {
  id?: number;
  tipo?: string;
  periodo?: string;
  responsable?: string;
  responsable_nombre?: string;
  estado?: string;
  fecha_creacion?: string;
  fecha_cierre?: string;
  observaciones?: string;
}

export interface ResultadoEvaluacion {
  id?: number;
  evaluacion?: number;
  poau?: string;
  unidad?: string;
  criterio?: string;
  puntaje?: number;
  max_puntaje?: number;
  observaciones?: string;
}

@Injectable()
export class EvaluacionService {
  constructor(private api: ApiService) {}

  listar(params?: Record<string, string | number | boolean>): Observable<Evaluacion[]> {
    return this.api.get<Evaluacion[]>('/evaluaciones/', params);
  }

  obtener(id: number): Observable<Evaluacion> {
    return this.api.get<Evaluacion>(`/evaluaciones/${id}/`);
  }

  crear(data: Partial<Evaluacion>): Observable<Evaluacion> {
    return this.api.post<Evaluacion>('/evaluaciones/', data);
  }

  resultados(id: number): Observable<ResultadoEvaluacion[]> {
    return this.api.get<ResultadoEvaluacion[]>(`/evaluaciones/${id}/resultados/`);
  }

  generar(data?: Record<string, string | number | boolean>): Observable<Evaluacion> {
    return this.api.post<Evaluacion>('/evaluaciones/generar/', data);
  }
}
