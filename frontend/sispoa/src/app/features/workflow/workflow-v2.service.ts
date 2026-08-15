import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  WorkflowDefinitionV2,
  WorkflowInstanceV2,
  WorkflowTaskV2,
} from './models/workflow-v2.model';

export interface Paginado<T> {
  count: number;
  results: T[];
}

/** Servicio del motor de workflow V2 (ADR-003): puro contra /api/v2/platform/. */
@Injectable({ providedIn: 'root' })
export class WorkflowV2Service {
  private base = environment.apiUrlV2 + '/platform';

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

  listarTareas(params?: { mias?: boolean; instancia?: string }): Observable<Paginado<WorkflowTaskV2>> {
    return this.http.get<Paginado<WorkflowTaskV2>>(`${this.base}/workflow-tareas/`, {
      params: this.params(params),
    });
  }

  listarInstancias(params?: {
    definicion?: string;
    entidad_tipo?: string;
    entidad_id?: string;
    cerrado?: boolean;
  }): Observable<Paginado<WorkflowInstanceV2>> {
    return this.http.get<Paginado<WorkflowInstanceV2>>(
      `${this.base}/workflow-instancias/`,
      { params: this.params(params) },
    );
  }

  obtenerInstancia(id: string): Observable<WorkflowInstanceV2> {
    return this.http.get<WorkflowInstanceV2>(`${this.base}/workflow-instancias/${id}/`);
  }

  iniciarInstancia(definicion: string, entidadTipo: string, entidadId: string): Observable<WorkflowInstanceV2> {
    return this.http.post<WorkflowInstanceV2>(`${this.base}/workflow-instancias/`, {
      definicion,
      entidad_tipo: entidadTipo,
      entidad_id: entidadId,
    });
  }

  avanzarInstancia(id: string, comentario = ''): Observable<WorkflowInstanceV2> {
    return this.http.post<WorkflowInstanceV2>(
      `${this.base}/workflow-instancias/${id}/avanzar/`, { comentario },
    );
  }

  aprobarInstancia(id: string, comentario = ''): Observable<WorkflowInstanceV2> {
    return this.http.post<WorkflowInstanceV2>(
      `${this.base}/workflow-instancias/${id}/aprobar/`, { comentario },
    );
  }

  observarInstancia(id: string, texto: string, severidad = 'moderada'): Observable<WorkflowInstanceV2> {
    return this.http.post<WorkflowInstanceV2>(
      `${this.base}/workflow-instancias/${id}/observar/`, { texto, severidad },
    );
  }

  delegarInstancia(id: string, delegadoA: string, motivo = ''): Observable<WorkflowInstanceV2> {
    return this.http.post<WorkflowInstanceV2>(
      `${this.base}/workflow-instancias/${id}/delegar/`,
      { delegado_a: delegadoA, motivo },
    );
  }

  listarDefiniciones(): Observable<Paginado<WorkflowDefinitionV2>> {
    return this.http.get<Paginado<WorkflowDefinitionV2>>(
      `${this.base}/workflow-definiciones/`,
    );
  }
}
