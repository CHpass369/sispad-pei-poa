/** Modelos del motor de workflow V2 (API /api/v2/platform/workflow-*). */

/** Estados de una tarea según `EstadosTarea` del backend (models_v2.py). */
export type EstadoTarea =
  | 'pendiente'
  | 'en_curso'
  | 'completada'
  | 'rechazada';

/** Tarea del workflow V2 (GET /platform/workflow-tareas/). */
export interface WorkflowTaskV2 {
  id: string;
  instancia: string;
  /** Código de la definición del workflow. */
  definicion: string;
  paso_nombre: string;
  paso: string;
  asignado_a: string | null;
  estado: EstadoTarea;
  creado_en: string;
  completado_en: string | null;
}

/** Instancia del workflow V2 (GET /platform/workflow-instancias/). */
export interface WorkflowInstanceV2 {
  id: string;
  definicion: string;
  definicion_codigo: string;
  entidad_tipo: string;
  entidad_id: string;
  estado_actual: string;
  cerrado: boolean;
  iniciado_en: string;
  tarea_actual: {
    id: string;
    paso: string;
    estado: EstadoTarea;
    asignado_a: string | null;
  } | null;
}

/** Definición del workflow V2 (GET /platform/workflow-definiciones/). */
export interface WorkflowDefinitionV2 {
  id: string;
  codigo: string;
  nombre: string;
  tipo_entidad: string;
  descripcion: string;
  activo: boolean;
  pasos: {
    id: string;
    orden: number;
    nombre: string;
    estado: string;
    es_inicial: boolean;
    es_final: boolean;
  }[];
  transiciones: {
    id: string;
    nombre: string;
    desde: string;
    hacia: string;
    requiere_aprobacion: boolean;
  }[];
}
