import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { EMPTY, Observable, expand, map, reduce } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Paginado } from '../../core/models/paginado.model';

export type AdminUserState = 'PENDIENTE' | 'ACTIVO' | 'INACTIVO';
export type AdminSystem = 'sis_pe' | 'sis_poa';
export type AdminRoleSystem = AdminSystem | 'accounts';
export type AdminAssignmentScope = 'SELF' | 'DESCENDANTS' | 'GLOBAL';

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
  scope_type: AdminAssignmentScope;
  fiscal_year: string | null;
}

export interface AdminUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  cargo: string;
  telefono: string;
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

export interface AdminUserPersonalPatch {
  first_name?: string;
  last_name?: string;
  cargo?: string;
  telefono?: string;
}

export interface AdminRoleCapability {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  sistema: AdminRoleSystem;
  activo: boolean;
  orden: number;
}

export interface AdminRole {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  activo: boolean;
  es_sistema: boolean;
  deprecated: boolean;
  orden: number;
  sistemas: AdminRoleSystem[];
  capacidades: AdminRoleCapability[];
}

export interface AdminAssignmentInput {
  role_code: string;
  organizational_unit_id: string;
  scope_type: AdminAssignmentScope;
  fiscal_year_id: string | null;
}

export interface AdminAssignmentsPayload {
  assignments: AdminAssignmentInput[];
}

@Injectable()
export class AdminUsuariosService {
  private readonly baseUrl = `${environment.apiUrlV2}/admin/users`;
  private readonly rolesUrl = `${environment.apiUrlV2}/admin/roles/`;

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

  patchUser(id: string, data: AdminUserPersonalPatch): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`${this.baseUrl}/${id}/`, data);
  }

  getAssignments(id: string): Observable<AdminUser> {
    return this.http.get<AdminUser>(`${this.baseUrl}/${id}/assignments/`);
  }

  putAssignments(id: string, data: AdminAssignmentsPayload): Observable<AdminUser> {
    return this.http.put<AdminUser>(`${this.baseUrl}/${id}/assignments/`, data);
  }

  listRoles(): Observable<AdminRole[]> {
    return this.http.get<Paginado<AdminRole>>(this.rolesUrl, {
      params: new HttpParams().set('active', 'true'),
    }).pipe(
      expand(page => page.next
        ? this.http.get<Paginado<AdminRole>>(page.next)
        : EMPTY),
      reduce(
        (roles, page) => [...roles, ...page.results],
        [] as AdminRole[],
      ),
    );
  }

  activate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/activate/`, {});
  }

  deactivate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/deactivate/`, {});
  }
}
