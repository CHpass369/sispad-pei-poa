import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

export interface Documento {
  id?: number;
  nombre: string;
  tipo: string;
  entidad_tipo?: string;
  entidad_id?: number;
  entidad_descripcion?: string;
  tamano?: number;
  descripcion?: string;
  tags?: string;
  fecha_subida?: string;
  subido_por?: string;
  archivo?: string;
  archivo_url?: string;
}

@Injectable()
export class DocumentosService {
  constructor(private api: ApiService, private http: HttpClient) {}

  listar(params?: Record<string, string | number | boolean>): Observable<Documento[]> {
    return this.api.get<Documento[]>('/documentos/', params);
  }

  obtener(id: number): Observable<Documento> {
    return this.api.get<Documento>(`/documentos/${id}/`);
  }

  subir(formData: FormData): Observable<Documento> {
    return this.http.post<Documento>(`${environment.apiUrl}/documentos/`, formData);
  }

  eliminar(id: number): Observable<void> {
    return this.api.delete<void>(`/documentos/${id}/`);
  }
}
