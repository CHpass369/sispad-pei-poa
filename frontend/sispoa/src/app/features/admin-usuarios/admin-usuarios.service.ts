import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface AdminUsuario {
  id?: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  roles?: number[];
  rol_nombre?: string[];
  date_joined?: string;
}

export interface AdminRol {
  id: number;
  name: string;
  description?: string;
}

@Injectable()
export class AdminUsuariosService {
  constructor(private api: ApiService) {}

  listarUsuarios(params?: { search?: string; is_active?: boolean }): Observable<AdminUsuario[]> {
    return this.api.get<AdminUsuario[]>('/auth/usuarios/', params as Record<string, string | number | boolean>);
  }

  obtenerUsuario(id: number): Observable<AdminUsuario> {
    return this.api.get<AdminUsuario>(`/auth/usuarios/${id}/`);
  }

  crearUsuario(data: Partial<AdminUsuario>): Observable<AdminUsuario> {
    return this.api.post<AdminUsuario>('/auth/usuarios/', data);
  }

  actualizarUsuario(id: number, data: Partial<AdminUsuario>): Observable<AdminUsuario> {
    return this.api.put<AdminUsuario>(`/auth/usuarios/${id}/`, data);
  }

  eliminarUsuario(id: number): Observable<void> {
    return this.api.delete<void>(`/auth/usuarios/${id}/`);
  }

  listarRoles(): Observable<AdminRol[]> {
    return this.api.get<AdminRol[]>('/auth/roles/');
  }

  crearRol(data: Partial<AdminRol>): Observable<AdminRol> {
    return this.api.post<AdminRol>('/auth/roles/', data);
  }
}
