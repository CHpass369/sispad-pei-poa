export interface Revision {
  id: number;
  gestion_id: number;
  tipo: 'envio' | 'revision';
  estado: 'pendiente' | 'en_revision' | 'observado' | 'aprobado' | 'rechazado';
  unidad_origen_nombre: string;
  unidad_destino_nombre: string;
  creado_por_nombre: string;
  fecha_creacion: string;
  fecha_revision?: string;
  comentarios?: string;
}

export interface Observacion {
  id: number;
  revision_id: number;
  severidad: 'grave' | 'moderada' | 'leve';
  descripcion: string;
  campo: string;
  creado_por_nombre: string;
  fecha_creacion: string;
  resuelta: boolean;
  fecha_resolucion?: string;
}

export interface Aprobacion {
  id: number;
  gestion_id: number;
  gestion_anio: number;
  tipo: 'formulacion' | 'presupuesto' | 'cierre';
  estado: 'pendiente' | 'aprobado' | 'rechazado';
  aprobado_por_nombre?: string;
  fecha_aprobacion?: string;
  comentarios?: string;
}

export const TIPOS_REVISION: Record<string, string> = {
  envio: 'Envío',
  revision: 'Revisión',
};

export const ESTADOS_REVISION: Record<string, string> = {
  pendiente: 'Pendiente',
  en_revision: 'En Revisión',
  observado: 'Observado',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};

export const SEVERIDADES: Record<string, string> = {
  grave: 'Grave',
  moderada: 'Moderada',
  leve: 'Leve',
};

export const TIPOS_APROBACION: Record<string, string> = {
  formulacion: 'Formulación',
  presupuesto: 'Presupuesto',
  cierre: 'Cierre',
};

export const ESTADOS_APROBACION: Record<string, string> = {
  pendiente: 'Pendiente',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};
