import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import {
  buildReportUrl,
  MatrizResponse,
} from './matrices-contracts';

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
    window.open(buildReportUrl('/reportes/matriz_completa_xlsx/', gestion), '_blank');
  }

  getResultadosPAD(gestion: number): Observable<any> {
    return this.api.get<any>('/articulacion/resultados-pad/', { gestion });
  }
}
