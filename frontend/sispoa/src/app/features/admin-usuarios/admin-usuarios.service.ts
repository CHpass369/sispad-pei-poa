import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Paginado } from '../../core/models/paginado.model';

export type AdminUserState = 'PENDIENTE' | 'ACTIVO' | 'INACTIVO';
export type AdminSystem = 'sis_pe' | 'sis_poa';

export interface AdminUserRole {
  codigo: string;
  nombre: string;
  sistemas: AdminSystem[];
}

export interface AdminOrganizationalUnit {
  id: string;
  codigo: string;
  nombre: string;
}

export interface AdminUserScope {
  rol: string | null;
  unidad: AdminOrganizationalUnit;
  scope_type: 'SELF' | 'DESCENDANTS' | 'GLOBAL';
  fiscal_year: string | null;
}

export interface AdminUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  cargo: string;
  estado: AdminUserState;
  activo: boolean;
  is_active: boolean;
  last_login: string | null;
  roles: AdminUserRole[];
  alcances: AdminUserScope[];
  sistemas: AdminSystem[];
}

export interface AdminUserFilters {
  search?: string;
  organizational_unit?: string;
  role?: string;
  system?: AdminSystem;
  state?: AdminUserState;
}

@Injectable()
export class AdminUsuariosService {
  private readonly baseUrl = `${environment.apiUrlV2}/admin/users`;

  constructor(private readonly http: HttpClient) {}

  listUsers(filters: AdminUserFilters = {}, page = 1): Observable<Paginado<AdminUser>> {
    let params = new HttpParams().set('page', page.toString());
    const values: Record<keyof AdminUserFilters, string | undefined> = {
      search: filters.search?.trim(),
      organizational_unit: filters.organizational_unit,
      role: filters.role?.trim(),
      system: filters.system,
      state: filters.state,
    };

    for (const [key, value] of Object.entries(values)) {
      if (value) {
        params = params.set(key, value);
      }
    }

    return this.http.get<Paginado<AdminUser>>(`${this.baseUrl}/`, { params }).pipe(
      map(response => ({
        count: response.count,
        next: response.next,
        previous: response.previous,
        results: response.results,
      })),
    );
  }

  getUser(id: string): Observable<AdminUser> {
    return this.http.get<AdminUser>(`${this.baseUrl}/${id}/`);
  }

  activate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/activate/`, {});
  }

  deactivate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/deactivate/`, {});
  }
}
