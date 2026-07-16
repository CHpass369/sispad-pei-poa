import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface CatalogoItem {
  id?: number;
  codigo?: string;
  nombre?: string;
  descripcion?: string;
  activo?: boolean;
  gestion?: number;
  [key: string]: unknown;
}

@Injectable()
export class CatalogosService {
  constructor(private api: ApiService) {}

  /** Obtiene la lista de ítems de un tipo de catálogo */
  listar(tipo: string, params?: { gestion?: number; search?: string }): Observable<CatalogoItem[]> {
    return this.api.get<CatalogoItem[]>(`/catalogos/${tipo}/`, params as Record<string, string | number | boolean>);
  }

  /** Importa un archivo XLSX/CSV para un tipo de catálogo */
  importar(tipo: string, formData: FormData): Observable<{ mensaje: string; cantidad: number }> {
    return this.api.post<{ mensaje: string; cantidad: number }>(`/catalogos/${tipo}/importar/`, formData);
  }
}
