import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { EMPTY, Observable } from 'rxjs';
import { expand, map, reduce } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export type TipoAcuerdo = 'ODS' | 'NDC' | 'NDT' | 'COMPROMISO_3030';
export type TipoRelacion =
  | 'OFICIAL_EXPLICITA'
  | 'DERIVADA_DOCUMENTAL'
  | 'SUGERENCIA_SEMANTICA';
export type EstadoCompatibilidad = 'VALIDADA' | 'CANDIDATA' | 'RECHAZADA';
export type ConfianzaCompatibilidad = 'ALTA' | 'MEDIA' | 'BAJA';

export interface AcuerdoInternacionalOption {
  id: string;
  tipo_acuerdo: TipoAcuerdo;
  tipo_acuerdo_display?: string;
  codigo: string;
  denominacion: string;
  rango_valido?: string;
  es_codigo_oficial?: boolean;
  activo?: boolean;
}

export interface CompatibilidadAcuerdo {
  id: string;
  origen: AcuerdoInternacionalOption;
  destino: AcuerdoInternacionalOption;
  tipo_relacion: TipoRelacion;
  tipo_relacion_display: string;
  estado: EstadoCompatibilidad;
  estado_display: string;
  confianza: ConfianzaCompatibilidad;
  confianza_display: string;
  fuente_url: string;
  fuente_titulo: string;
  fuente_version: string;
  localizador: string;
  evidencia: string;
  justificacion: string;
  activo: boolean;
}

export interface CompatibilidadesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: CompatibilidadAcuerdo[];
}

export interface CompatibilidadesQuery {
  origenId?: string;
  origenIds?: string[];
  destinoTipo?: TipoAcuerdo;
  estado?: EstadoCompatibilidad;
  incluirSugerencias?: boolean;
}

@Injectable({ providedIn: 'root' })
export class CompatibilidadesAcuerdosService {
  private readonly base = `${environment.apiUrlV2}/integracion/compatibilidades/`;

  constructor(private http: HttpClient) {}

  listar(query: CompatibilidadesQuery = {}): Observable<CompatibilidadesResponse> {
    let params = new HttpParams();
    if (query.origenId) params = params.set('origen_id', query.origenId);
    if (query.origenIds?.length) {
      params = params.set('origen_ids', query.origenIds.join(','));
    }
    if (query.destinoTipo) params = params.set('destino_tipo', query.destinoTipo);
    if (query.estado) params = params.set('estado', query.estado);
    if (query.incluirSugerencias !== undefined) {
      params = params.set('incluir_sugerencias', String(query.incluirSugerencias));
    }
    return this.http.get<CompatibilidadesResponse>(this.base, { params }).pipe(
      expand(page => page.next
        ? this.http.get<CompatibilidadesResponse>(page.next)
        : EMPTY),
      reduce(
        (acumulado, page) => ({
          count: page.count,
          next: null,
          previous: null,
          results: [...acumulado.results, ...page.results],
        }),
        { count: 0, next: null, previous: null, results: [] },
      ),
      map(response => ({ ...response, count: response.results.length })),
    );
  }
}
