import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../core/services/api.service';

export interface Usuario {
  id?: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  roles?: number[];
  rol_nombre?: string[];
  date_joined?: string;
}

export interface Rol {
  id: number;
  name: string;
  description?: string;
}

@Injectable()
export class AdminUsuariosService {
  constructor(private api: ApiService) {}

  listarUsuarios(params?: { search?: string; is_active?: boolean }): Observable<Usuario[]> {
    return this.api.get<Usuario[]>('/auth/usuarios/', params as Record<string, string | number | boolean>);
  }

  obtenerUsuario(id: number): Observable<Usuario> {
    return this.api.get<Usuario>(`/auth/usuarios/${id}/`);
  }

  crearUsuario(data: Partial<Usuario>): Observable<Usuario> {
    return this.api.post<Usuario>('/auth/usuarios/', data);
  }

  actualizarUsuario(id: number, data: Partial<Usuario>): Observable<Usuario> {
    return this.api.put<Usuario>(`/auth/usuarios/${id}/`, data);
  }

  eliminarUsuario(id: number): Observable<void> {
    return this.api.delete<void>(`/auth/usuarios/${id}/`);
  }

  listarRoles(): Observable<Rol[]> {
    return this.api.get<Rol[]>('/auth/roles/');
  }

  crearRol(data: Partial<Rol>): Observable<Rol> {
    return this.api.post<Rol>('/auth/roles/', data);
  }
}
