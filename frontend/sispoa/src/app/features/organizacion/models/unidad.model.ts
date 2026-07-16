export interface UnidadOrganizacional {
  id: number;
  codigo: string;
  sigla: string;
  nombre: string;
  nivel: string;
  padre_id: number | null;
  hijos: UnidadOrganizacional[];
  tipo: 'DA' | 'UE' | 'OTRO';
  responsable?: string;
  activo: boolean;
}

export interface DireccionAdministrativa {
  id: number;
  codigo: string;
  nombre: string;
  sigla: string;
  responsable: string;
  activo: boolean;
}

export interface DireccionAdministrativaRequest {
  codigo: string;
  nombre: string;
  sigla: string;
  responsable: string;
}

export interface UnidadEjecutora {
  id: number;
  codigo: string;
  nombre: string;
  sigla: string;
  responsable: string;
  activo: boolean;
}

export interface UnidadEjecutoraRequest {
  codigo: string;
  nombre: string;
  sigla: string;
  responsable: string;
}
