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

export interface AdminCapability {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  sistema: string;
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
  sistemas: string[];
  capacidades: AdminCapability[];
}

export interface AdminCatalogFilters {
  search?: string;
  system?: AdminRoleSystem;
  active?: boolean;
}

export interface AdminRoleCreate {
  codigo: string;
  nombre: string;
  descripcion?: string;
  activo?: boolean;
}

export interface AdminRolePatch {
  nombre?: string;
  descripcion?: string;
  activo?: boolean;
  orden?: number;
}

export interface AdminRoleCapabilitiesPayload {
  capability_codes: string[];
}

export interface AdminRegistrationRequest {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  cargo: string;
  date_joined: string | null;
  unidad_solicitada: {
    id: string;
    nombre: string;
  } | null;
  /** What the applicant declared at registration. Grants nothing on its own. */
  solicita_encargado_unidad: boolean;
  /** Role the backend suggests for that declaration; the admin still confirms. */
  rol_sugerido: string;
  estado?: AdminUserState;
}

export interface AdminApprovalPayload {
  unidad_organizacional_id: string;
  rol_codigo: string;
  scope_type: AdminAssignmentScope;
  sistema: AdminSystem;
  fiscal_year_id: string | null;
}

export interface AdminApprovalResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  estado: 'ACTIVO';
  activo: boolean;
  roles: string[];
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

export interface AdminPreviewAccessRequest {
  user_id: string;
  assignments?: AdminAssignmentInput[];
}

export interface AdminPreviewCapability {
  codigo: string;
  nombre: string;
  sistema: AdminSystem;
  modulo: string;
}

export interface AdminPreviewOrganizationalUnit {
  id: string;
  codigo: string;
  nombre: string;
}

export interface AdminPreviewModule {
  codigo: string;
  sistema: AdminSystem;
  visible: boolean;
}

export interface AdminAccessPreviewResponse {
  capabilities: AdminPreviewCapability[];
  effective_uos: AdminPreviewOrganizationalUnit[];
  modules: AdminPreviewModule[];
}

@Injectable()
export class AdminUsuariosService {
  private readonly baseUrl = `${environment.apiUrlV2}/admin/users`;
  private readonly rolesUrl = `${environment.apiUrlV2}/admin/roles/`;
  private readonly capabilitiesUrl = `${environment.apiUrlV2}/admin/capabilities/`;
  private readonly requestsUrl = `${environment.apiUrlV2}/admin/solicitudes/`;
  private readonly previewAccessUrl = `${environment.apiUrlV2}/admin/preview-access/`;

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

  previewAccess(
    request: AdminPreviewAccessRequest,
  ): Observable<AdminAccessPreviewResponse> {
    let params = new HttpParams().set('user_id', request.user_id);
    if (request.assignments !== undefined) {
      params = params.set('assignments', JSON.stringify(request.assignments));
    }
    return this.http.get<AdminAccessPreviewResponse>(this.previewAccessUrl, { params });
  }

  listRoles(): Observable<AdminRole[]> {
    return this.listRolesPage({ active: true }).pipe(
      expand(page => page.next
        ? this.http.get<Paginado<AdminRole>>(page.next)
        : EMPTY),
      reduce(
        (roles, page) => [...roles, ...page.results],
        [] as AdminRole[],
      ),
    );
  }

  listRolesPage(
    filters: AdminCatalogFilters = {},
    page = 1,
  ): Observable<Paginado<AdminRole>> {
    return this.http.get<Paginado<AdminRole>>(this.rolesUrl, {
      params: this.catalogParams(filters, page),
    });
  }

  getRole(id: string): Observable<AdminRole> {
    return this.http.get<AdminRole>(`${this.rolesUrl}${id}/`);
  }

  createRole(data: AdminRoleCreate): Observable<AdminRole> {
    return this.http.post<AdminRole>(this.rolesUrl, data);
  }

  patchRole(id: string, data: AdminRolePatch): Observable<AdminRole> {
    return this.http.patch<AdminRole>(`${this.rolesUrl}${id}/`, data);
  }

  deleteRole(id: string): Observable<void> {
    return this.http.delete<void>(`${this.rolesUrl}${id}/`);
  }

  replaceRoleCapabilities(
    id: string,
    data: AdminRoleCapabilitiesPayload,
  ): Observable<AdminRole> {
    return this.http.put<AdminRole>(`${this.rolesUrl}${id}/capabilities/`, data);
  }

  listCapabilities(
    filters: AdminCatalogFilters = {},
    page = 1,
  ): Observable<Paginado<AdminCapability>> {
    return this.http.get<Paginado<AdminCapability>>(this.capabilitiesUrl, {
      params: this.catalogParams(filters, page),
    });
  }

  listAllCapabilities(): Observable<AdminCapability[]> {
    return this.listCapabilities().pipe(
      expand(page => page.next
        ? this.http.get<Paginado<AdminCapability>>(page.next)
        : EMPTY),
      reduce(
        (capabilities, page) => [...capabilities, ...page.results],
        [] as AdminCapability[],
      ),
    );
  }

  listRequests(page = 1): Observable<Paginado<AdminRegistrationRequest>> {
    return this.http.get<Paginado<AdminRegistrationRequest>>(this.requestsUrl, {
      params: new HttpParams().set('page', page.toString()),
    });
  }

  approveRequest(
    id: string,
    data: AdminApprovalPayload,
  ): Observable<AdminApprovalResponse> {
    return this.http.post<AdminApprovalResponse>(
      `${this.baseUrl}/${id}/approve/`,
      data,
    );
  }

  activate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/activate/`, {});
  }

  deactivate(id: string): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.baseUrl}/${id}/deactivate/`, {});
  }

  private catalogParams(filters: AdminCatalogFilters, page: number): HttpParams {
    let params = new HttpParams().set('page', page.toString());
    const search = filters.search?.trim();
    if (search) {
      params = params.set('search', search);
    }
    if (filters.system) {
      params = params.set('system', filters.system);
    }
    if (filters.active !== undefined) {
      params = params.set('active', filters.active.toString());
    }
    return params;
  }
}
