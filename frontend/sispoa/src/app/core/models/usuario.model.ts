export interface Usuario {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  cargo: string;
  telefono: string;
  roles: string[];
  roles_detalle: Rol[];
  activo: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  debe_cambiar_password: boolean;
  last_login: string;
  date_joined: string;
}

export interface Rol {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  activo: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}
