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

export interface RegistrationRequest {
  first_name: string;
  last_name: string;
  email: string;
  cargo: string;
  unidad_organizacional_id: string;
  password: string;
  password_confirm: string;
}

export interface RegistrationResponse {
  detail: string;
}

export interface PublicOrganizationalUnit {
  id: string;
  codigo: string;
  nombre: string;
  sigla: string;
  padre: string | null;
}
