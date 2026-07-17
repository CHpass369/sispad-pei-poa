import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface PdeSa {
  id?: number;
  nombre?: string;
  descripcion?: string;
  gestion?: number;
  estado?: string;
}

export interface Ptdi {
  id?: number;
  pde_sa?: number;
  pde_sa_nombre?: string;
  nombre?: string;
  descripcion?: string;
  gestion?: number;
}

export interface Pei {
  id?: number;
  ptdi?: number;
  ptdi_nombre?: string;
  unidad_ejecutora?: number;
  unidad_ejecutora_nombre?: string;
  gestion?: number;
  estado?: string;
  avance_porcentual?: number;
}

export interface ResultadoPad {
  id?: number;
  pei?: number;
  pei_descripcion?: string;
  unidad_ejecutora?: number;
  unidad_ejecutora_nombre?: string;
  programa?: string;
  monto_total?: number;
  monto_formulado?: number;
  avance_porcentual?: number;
  estado?: string;
}

export interface Poau {
  id?: number;
  resultado_pad?: number;
  resultado_pad_descripcion?: string;
  unidad_ejecutora?: number;
  unidad_ejecutora_nombre?: string;
  gestion?: number;
  monto_total?: number;
  monto_ejecutado?: number;
  avance_porcentual?: number;
  estado?: string;
}

export interface ConsolidacionUE {
  ue_id: number;
  ue_nombre: string;
  pei_porcentaje: number;
  pad_porcentaje: number;
  poa_porcentaje: number;
  poau_porcentaje: number;
  estado_general: string;
}

@Injectable()
export class ConsolidacionService {
  constructor(private api: ApiService) {}

  listarPdeSa(params?: Record<string, string | number | boolean>): Observable<PdeSa[]> {
    return this.api.get<PdeSa[]>('/planificacion/pde-sa/', params);
  }

  listarPtdi(params?: Record<string, string | number | boolean>): Observable<Ptdi[]> {
    return this.api.get<Ptdi[]>('/planificacion/ptdi/', params);
  }

  listarPei(params?: Record<string, string | number | boolean>): Observable<Pei[]> {
    return this.api.get<Pei[]>('/planificacion/pei/', params);
  }

  listarResultadosPad(params?: Record<string, string | number | boolean>): Observable<ResultadoPad[]> {
    return this.api.get<ResultadoPad[]>('/pad/resultados/', params);
  }

  listarPoau(params?: Record<string, string | number | boolean>): Observable<Poau[]> {
    return this.api.get<Poau[]>('/poau/', params);
  }
}
