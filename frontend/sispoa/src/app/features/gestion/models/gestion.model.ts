export interface Gestion {
  id: number;
  anio: number;
  estado: 'planificacion' | 'formulacion' | 'revision' | 'aprobado' | 'ejecucion' | 'cerrado';
  fecha_inicio: string;
  fecha_fin: string;
  ciclos_formulacion: CicloFormulacion[];
  etapas: EtapaGestion[];
}

export interface GestionRequest {
  anio: number;
  fecha_inicio: string;
  fecha_fin: string;
}

export interface CicloFormulacion {
  id: number;
  gestion_id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  activo: boolean;
}

export interface EtapaGestion {
  id: number;
  gestion_id: number;
  nombre: string;
  orden: number;
  completada: boolean;
  fecha_completada?: string;
}

export const ESTADOS_GESTION: Record<string, string> = {
  planificacion: 'Planificación',
  formulacion: 'Formulación',
  revision: 'Revisión',
  aprobado: 'Aprobado',
  ejecucion: 'Ejecución',
  cerrado: 'Cerrado',
};
