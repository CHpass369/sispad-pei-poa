import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface PdeSaPublico {
  id?: number;
  nombre?: string;
  descripcion?: string;
  gestion?: number;
  estado?: string;
}

export interface ResultadoPadPublico {
  id?: number;
  pei_descripcion?: string;
  unidad_ejecutora_nombre?: string;
  programa?: string;
  monto_total?: number;
  monto_formulado?: number;
  avance_porcentual?: number;
  estado?: string;
}

export interface IndicadorPublico {
  id?: number;
  nombre?: string;
  descripcion?: string;
  tipo?: string;
  meta?: number;
  valor_actual?: number;
  unidad_medida?: string;
  fuente?: string;
  avance_porcentual?: number;
}

export interface ResumenEjecucion {
  total_presupuesto?: number;
  total_ejecutado?: number;
  porcentaje_ejecucion?: number;
  total_programas?: number;
  total_acciones?: number;
  por_tipo?: any[];
  por_sector?: any[];
  por_mes?: any[];
}

export interface EstadisticasResumen {
  total_planes?: number;
  total_presupuesto?: number;
  total_ejecutado?: number;
  total_indicadores?: number;
  indicadores_cumplidos?: number;
}

@Injectable()
export class PortalPublicoService {
  constructor(private api: ApiService) {}

  listarPdeSa(params?: Record<string, string | number | boolean>): Observable<PdeSaPublico[]> {
    return this.api.get<PdeSaPublico[]>('/planificacion/pde-sa/', params);
  }

  listarResultadosPad(params?: Record<string, string | number | boolean>): Observable<ResultadoPadPublico[]> {
    return this.api.get<ResultadoPadPublico[]>('/pad/resultados/', params);
  }

  listarIndicadores(params?: Record<string, string | number | boolean>): Observable<IndicadorPublico[]> {
    return this.api.get<IndicadorPublico[]>('/indicadores/', params);
  }

  obtenerResumenEjecucion(params?: Record<string, string | number | boolean>): Observable<ResumenEjecucion> {
    return this.api.get<ResumenEjecucion>('/reportes/resumen-ejecucion/', params);
  }
}
