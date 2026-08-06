import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

export interface NodoArbol {
  id: string;
  codigo_completo: string;
  codigo: string;
  nombre: string;
  nivel: string;
  tipo_plan: string;
  plan_nombre: string;
  hijos?: NodoArbol[];
  articulaciones?: any[];
}

export interface MatrizResponse {
  data: NodoArbol[];
  stats: {
    total: number;
    por_nivel: Record<string, number>;
  };
}

@Injectable({ providedIn: 'root' })
export class MatrizCompletaService {
  constructor(private api: ApiService) {}

  getArbol(
    gestion: number,
    nivel?: string,
    padreId?: string,
  ): Observable<MatrizResponse> {
    const params: Record<string, string | number> = { gestion };
    if (nivel) params['nivel'] = nivel;
    if (padreId) params['padre_id'] = padreId;
    return this.api.get<MatrizResponse>('/planificacion/matriz-completa/', params);
  }

  updateBridgePAD(resultadoPadId: string, nodoPdesaId: string): Observable<any> {
    return this.api.patch(`/articulacion/resultados-pad/${resultadoPadId}/`, {
      nodo_pdesa: nodoPdesaId,
    });
  }

  exportXLSX(gestion: number): void {
    const url = `${environment.apiUrl}/reportes/matriz_completa_xlsx/?gestion=${gestion}`;
    window.open(url, '_blank');
  }

  getResultadosPAD(gestion: number): Observable<any> {
    return this.api.get<any>('/articulacion/resultados-pad/', { gestion });
  }
}
