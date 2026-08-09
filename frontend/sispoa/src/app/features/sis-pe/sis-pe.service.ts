import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface InstrumentoV2 {
  id: string;
  tipo: string;
  tipo_nombre: string;
  codigo: string;
  nombre: string;
  institucion_responsable: string;
  periodo_inicio: number;
  periodo_fin: number;
  estado: string;
  versiones_count: number;
}

export interface VersionV2 {
  id: string;
  instrumento: string;
  instrumento_codigo: string;
  numero: number;
  etiqueta: string;
  metodologia: string;
  metodologia_nombre: string;
  estado: string;
  inmutable: boolean;
  checksum: string;
  norma_aprobacion: string;
  nodos_count: number;
  vinculos_count: number;
}

export interface NodoV2 {
  id: string;
  version: string;
  tipo_nodo: string;
  tipo_nodo_denominacion: string;
  padre: string | null;
  padre_codigo: string | null;
  codigo: string;
  nombre: string;
  descripcion: string;
  orden: number;
  hijos?: NodoV2[];
}

export interface MetodologiaV2 {
  id: string;
  codigo: string;
  nombre: string;
  version: string;
  estado: string;
}

interface Paginado<T> {
  count: number;
  results: T[];
}

/**
 * Servicio tipado del SIS-PE V2 (ADR-002): consume exclusivamente /api/v2.
 */
@Injectable({ providedIn: 'root' })
export class SisPeService {
  private base = environment.apiUrlV2 + '/sis-pe';

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

  listarInstrumentos(params?: { tipo?: string }): Observable<Paginado<InstrumentoV2>> {
    return this.http.get<Paginado<InstrumentoV2>>(
      `${this.base}/instrumentos/`, { params: this.params(params) },
    );
  }

  crearInstrumento(data: Partial<InstrumentoV2>): Observable<InstrumentoV2> {
    return this.http.post<InstrumentoV2>(`${this.base}/instrumentos/`, data);
  }

  crearVersion(
    instrumentoId: string,
    metodologia: string,
    etiqueta = '',
  ): Observable<VersionV2> {
    return this.http.post<VersionV2>(
      `${this.base}/instrumentos/${instrumentoId}/crear_version/`,
      { metodologia, etiqueta },
    );
  }

  versionesDeInstrumento(instrumentoId: string): Observable<VersionV2[]> {
    return this.http.get<VersionV2[]>(
      `${this.base}/instrumentos/${instrumentoId}/versiones/`,
    );
  }

  obtenerVersion(id: string): Observable<VersionV2> {
    return this.http.get<VersionV2>(`${this.base}/versiones/${id}/`);
  }

  nodosDeVersion(id: string): Observable<NodoV2[]> {
    return this.http.get<NodoV2[]>(`${this.base}/versiones/${id}/nodos/`);
  }

  aprobarVersion(id: string, norma: string): Observable<VersionV2> {
    return this.http.post<VersionV2>(
      `${this.base}/versiones/${id}/aprobar/`,
      { norma_aprobacion: norma },
    );
  }

  verificarVersion(id: string): Observable<{
    inmutable: boolean;
    checksum_registrado: string;
    checksum_actual: string;
    consistente: boolean;
  }> {
    return this.http.get<{
      inmutable: boolean;
      checksum_registrado: string;
      checksum_actual: string;
      consistente: boolean;
    }>(`${this.base}/versiones/${id}/verificar/`);
  }

  listarMetodologias(): Observable<Paginado<MetodologiaV2>> {
    return this.http.get<Paginado<MetodologiaV2>>(`${this.base}/metodologias/`);
  }
}
