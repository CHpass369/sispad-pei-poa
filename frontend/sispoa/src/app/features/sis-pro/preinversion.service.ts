import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ProyectoPreinversion {
  id: string;
  codigo_interno: string;
  codigo_sisin: string;
  nombre: string;
  descripcion: string;
  gestion: number;
  fase: string;
  estado: string;
  estado_preinversion: string;
  tipologia_rm115: string;
  responsable: string | null;
  problema: string;
  objetivo_general: string;
  descripcion_localizacion: string;
  distrito: string;
  comunidad: string;
  presupuesto_estimado: string | null;
  presupuesto_aprobado: string | null;
  moneda: string;
  puntaje_madurez: string;
  habilitado_poa: boolean;
  vigencia_viabilidad: string | null;
  geometry_geojson: unknown;
  created_at: string;
  updated_at: string;
}

export interface ITCP {
  id: string;
  proyecto: string;
  version: number;
  estado: string;
  justificacion_iniciativa: string;
  idea_proyecto: string;
  resultado_preliminar: string;
  conclusiones: string;
  recomendaciones: string;
  condiciones: CondicionITCP[];
}

export interface CondicionITCP {
  id: string;
  proyecto: string;
  itcp: string;
  categoria: string;
  titulo: string;
  estado: string;
  hallazgo: string;
  plan_accion: string;
  justificacion_no_aplica: string;
  fecha_limite: string | null;
  critica: boolean;
  orden: number;
}

export interface TDR {
  id: string;
  proyecto: string;
  version: number;
  estado: string;
  justificacion: string;
  objetivos: string;
  alcance: string;
  actores_responsabilidades: string;
  metodologia: string;
  duracion_dias: number | null;
  presupuesto_referencial: string | null;
  actividades: TDRActividad[];
  productos: TDRProducto[];
  personal: TDRPersonal[];
  items_presupuesto: TDRItemPresupuesto[];
}

export interface TDRActividad {
  id: string;
  tdr: string;
  codigo: string;
  descripcion: string;
  duracion_dias: number;
  orden: number;
}

export interface TDRProducto {
  id: string;
  tdr: string;
  codigo: string;
  nombre: string;
  criterios_aceptacion: string;
  dia_entrega: number;
}

export interface TDRPersonal {
  id: string;
  tdr: string;
  rol: string;
  cantidad: number;
  meses: string;
  dedicacion_porcentaje: string;
  tarifa_mensual: string;
  requisitos: string;
  subtotal: string;
}

export interface TDRItemPresupuesto {
  id: string;
  tdr: string;
  categoria: string;
  descripcion: string;
  cantidad: string;
  unidad: string;
  costo_unitario: string;
  memoria_calculo: string;
  subtotal: string;
}

export interface SeccionEDTP {
  id: string;
  edtp: string;
  codigo: string;
  titulo: string;
  orden: number;
  requerida: boolean;
  aplicable: boolean;
  justificacion_no_aplica: string;
  contenido: string;
  estado: string;
  porcentaje_avance: number;
}

export interface EstudioTecnico {
  id: string;
  edtp: string;
  tipo_estudio: string;
  titulo: string;
  requerido: boolean;
  estado: string;
  profesional: string;
  registro_profesional: string;
  fecha_estudio: string | null;
  version: number;
  conclusiones: string;
}

export interface ItemCostoEDTP {
  id: string;
  edtp: string;
  componente: string | null;
  categoria: string;
  codigo: string;
  descripcion: string;
  unidad: string;
  cantidad: string;
  precio_unitario: string;
  subtotal: string;
}

export interface FuenteFinanciamientoEDTP {
  id: string;
  edtp: string;
  codigo_fuente: string;
  nombre_fuente: string;
  monto: string;
  confirmada: boolean;
}

export interface ItemCronograma {
  id: string;
  edtp: string;
  componente: string | null;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  monto_planificado: string;
  peso_fisico: string;
}

export interface PlanOperacionMantenimiento {
  id: string;
  edtp: string;
  operador: string;
  actividades: string;
  costo_operacion_anual: string;
  costo_mantenimiento_anual: string;
  mecanismo_financiamiento: string;
  justificacion_costo_cero: string;
}

export interface IndicadorEvaluacionEDTP {
  id: string;
  edtp: string;
  tipo_indicador: string;
  nombre: string;
  valor: string;
  unidad: string;
  interpretacion: string;
}

export interface EDTP {
  id: string;
  proyecto: string;
  version: number;
  estado: string;
  resumen_ejecutivo: string;
  metodo_evaluacion: string;
  resultado_viabilidad: string;
  conclusiones: string;
  recomendaciones: string;
  secciones: SeccionEDTP[];
  estudios_tecnicos: EstudioTecnico[];
  items_costo: ItemCostoEDTP[];
  fuentes_financiamiento: FuenteFinanciamientoEDTP[];
  indicadores_evaluacion: IndicadorEvaluacionEDTP[];
  plan_om: PlanOperacionMantenimiento | null;
}

export interface ComponenteProyecto {
  id: string;
  proyecto: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  meta_fisica: string | null;
  unidad: string;
  presupuesto: string;
  orden: number;
}

export interface GrupoBeneficiario {
  id: string;
  proyecto: string;
  tipo: string;
  descripcion: string;
  cantidad: number;
  unidad: string;
  metodologia: string;
}

export interface DocumentoGenerado {
  id: string;
  proyecto: string;
  tipo_documento: string;
  estado: string;
  plantilla: string;
  archivo_docx: string | null;
  archivo_pdf: string | null;
  mensaje_error: string;
  contexto: unknown;
  created_at: string;
  updated_at: string;
}

export interface ResultadoAccion {
  itcp_id?: string;
  edtp_id?: string;
  condiciones?: number;
  secciones?: number;
  tipologia_sugerida?: string;
  puntaje_madurez?: string;
  habilitado_poa?: boolean;
  estado_preinversion?: string;
  aprobable?: boolean;
  errores?: string[];
  documento_generado_id?: string;
  estado?: string;
}

export interface ValidacionResultado {
  aprobable: boolean;
  errores: string[];
  estado_preinversion: string;
}

export interface PaqueteTransferencia {
  schema_version: string;
  project_id: string;
  project_code: string;
  official_name: string;
  management_year: number;
  status: string;
  rm115_typology: string;
  district_code: string;
  community_name: string;
  geometry: unknown;
  approved_budget: string;
  currency: string;
  readiness_score: string;
  components: unknown[];
  beneficiaries: unknown[];
  documents: unknown[];
}

interface Paginado<T> {
  count: number;
  results: T[];
}

const ESTADOS_EXPEDIENTE = [
  'registrada', 'en_admisibilidad', 'admitida',
  'itcp_elaboracion', 'itcp_revision', 'itcp_aprobado',
  'edtp_elaboracion', 'edtp_revision', 'edtp_aprobado',
  'viable', 'habilitado_poa', 'enviado_poa',
  'no_viable', 'archivado',
];

const TIPOLOGIAS_RM115: Record<string, string> = {
  I: 'Desarrollo Empresarial Productivo',
  II: 'Apoyo al Desarrollo Productivo',
  III: 'Desarrollo Social',
  IV: 'Fortalecimiento Institucional',
  V: 'Investigación y Desarrollo Tecnológico',
};

const ESTADOS_CONDICION = [
  'pendiente', 'en_elaboracion', 'observada', 'subsanada',
  'cumple', 'no_aplica', 'aprobada',
];

const ESTADOS_DOCUMENTO = ['borrador', 'en_revision', 'observado', 'aprobado', 'rechazado'];

const CATEGORIAS_CONDICION: Record<string, string> = {
  justificacion: 'Justificación y alineamiento',
  idea: 'Idea del proyecto',
  compromiso_social: 'Compromiso social',
  derecho_propietario: 'Derecho propietario',
  terceros: 'Derechos de vía y terceros',
  ambiente: 'Impactos ambientales',
  riesgo: 'Riesgos y cambio climático',
  otros: 'Otros aspectos',
  conclusiones: 'Conclusiones y recomendaciones',
};

/** Servicio tipado de preinversión SIS-PRO V2 (SISPRE / RM 115). */
@Injectable({ providedIn: 'root' })
export class PreinversionService {
  private base = environment.apiUrlV2 + '/sis-pro';

  constructor(private http: HttpClient) {}

  private params(values?: Record<string, string | number | boolean>): HttpParams {
    let p = new HttpParams();
    if (values) {
      Object.entries(values).forEach(([k, v]) => {
        if (v !== undefined && v !== null) p = p.set(k, String(v));
      });
    }
    return p;
  }

  // -------------------------------------------------------------------------
  // Proyecto / expediente
  // -------------------------------------------------------------------------
  listarProyectos(params?: {
    gestion?: number;
    estado_preinversion?: string;
    tipologia_rm115?: string;
    habilitado_poa?: boolean;
  }): Observable<Paginado<ProyectoPreinversion>> {
    return this.http.get<Paginado<ProyectoPreinversion>>(
      `${this.base}/proyectos-preinversion/`, { params: this.params(params) },
    );
  }

  obtenerProyecto(id: string): Observable<ProyectoPreinversion> {
    return this.http.get<ProyectoPreinversion>(`${this.base}/proyectos-preinversion/${id}/`);
  }

  actualizarProyecto(id: string, data: Partial<ProyectoPreinversion>): Observable<ProyectoPreinversion> {
    return this.http.patch<ProyectoPreinversion>(
      `${this.base}/proyectos-preinversion/${id}/`, data,
    );
  }

  clasificar(id: string, aceptar = true): Observable<ResultadoAccion> {
    return this.http.post<ResultadoAccion>(
      `${this.base}/proyectos-preinversion/${id}/clasificar/`, { aceptar },
    );
  }

  inicializarItcp(id: string): Observable<ResultadoAccion> {
    return this.http.post<ResultadoAccion>(
      `${this.base}/proyectos-preinversion/${id}/inicializar_itcp/`, {},
    );
  }

  inicializarEdtp(id: string): Observable<ResultadoAccion> {
    return this.http.post<ResultadoAccion>(
      `${this.base}/proyectos-preinversion/${id}/inicializar_edtp/`, {},
    );
  }

  calcularMadurez(id: string): Observable<ResultadoAccion> {
    return this.http.post<ResultadoAccion>(
      `${this.base}/proyectos-preinversion/${id}/calcular_madurez/`, {},
    );
  }

  validarAprobacion(id: string, documento: 'ITCP' | 'EDTP'): Observable<ValidacionResultado> {
    return this.http.post<ValidacionResultado>(
      `${this.base}/proyectos-preinversion/${id}/validar_aprobacion/`,
      { documento },
    );
  }

  generarDocumento(id: string, tipoDocumento: 'ITCP' | 'EDTP'): Observable<ResultadoAccion> {
    return this.http.post<ResultadoAccion>(
      `${this.base}/proyectos-preinversion/${id}/generar_documento/`,
      { tipo_documento: tipoDocumento },
    );
  }

  paqueteTransferencia(id: string): Observable<PaqueteTransferencia> {
    return this.http.get<PaqueteTransferencia>(
      `${this.base}/proyectos-preinversion/${id}/paquete_transferencia/`,
    );
  }

  cambiarEstado(id: string, estadoPreinversion: string): Observable<ProyectoPreinversion> {
    return this.http.post<ProyectoPreinversion>(
      `${this.base}/proyectos-preinversion/${id}/cambiar_estado/`,
      { estado_preinversion: estadoPreinversion },
    );
  }

  elegiblesPoa(): Observable<ProyectoPreinversion[]> {
    return this.http.get<ProyectoPreinversion[]>(
      `${this.base}/proyectos-preinversion/elegibles_poa/`,
    );
  }

  // -------------------------------------------------------------------------
  // ITCP
  // -------------------------------------------------------------------------
  listarItcps(params?: { proyecto?: string }): Observable<Paginado<ITCP>> {
    return this.http.get<Paginado<ITCP>>(`${this.base}/itcps/`, { params: this.params(params) });
  }

  obtenerItcp(id: string): Observable<ITCP> {
    return this.http.get<ITCP>(`${this.base}/itcps/${id}/`);
  }

  actualizarItcp(id: string, data: Partial<ITCP>): Observable<ITCP> {
    return this.http.patch<ITCP>(`${this.base}/itcps/${id}/`, data);
  }

  listarCondiciones(params?: { itcp?: string; proyecto?: string }): Observable<CondicionITCP[]> {
    return this.http.get<CondicionITCP[]>(`${this.base}/itcp-condiciones/`, {
      params: this.params(params),
    });
  }

  actualizarCondicion(id: string, data: Partial<CondicionITCP>): Observable<CondicionITCP> {
    return this.http.patch<CondicionITCP>(`${this.base}/itcp-condiciones/${id}/`, data);
  }

  // -------------------------------------------------------------------------
  // TDR
  // -------------------------------------------------------------------------
  listarTdrs(params?: { proyecto?: string }): Observable<Paginado<TDR>> {
    return this.http.get<Paginado<TDR>>(`${this.base}/tdrs/`, { params: this.params(params) });
  }

  obtenerTdr(id: string): Observable<TDR> {
    return this.http.get<TDR>(`${this.base}/tdrs/${id}/`);
  }

  actualizarTdr(id: string, data: Partial<TDR>): Observable<TDR> {
    return this.http.patch<TDR>(`${this.base}/tdrs/${id}/`, data);
  }

  crearActividadTdr(data: Partial<TDRActividad>): Observable<TDRActividad> {
    return this.http.post<TDRActividad>(`${this.base}/tdr-actividades/`, data);
  }

  crearProductoTdr(data: Partial<TDRProducto>): Observable<TDRProducto> {
    return this.http.post<TDRProducto>(`${this.base}/tdr-productos/`, data);
  }

  crearPersonalTdr(data: Partial<TDRPersonal>): Observable<TDRPersonal> {
    return this.http.post<TDRPersonal>(`${this.base}/tdr-personal/`, data);
  }

  crearItemPresupuestoTdr(data: Partial<TDRItemPresupuesto>): Observable<TDRItemPresupuesto> {
    return this.http.post<TDRItemPresupuesto>(`${this.base}/tdr-items-presupuesto/`, data);
  }

  // -------------------------------------------------------------------------
  // EDTP
  // -------------------------------------------------------------------------
  listarEdtps(params?: { proyecto?: string }): Observable<Paginado<EDTP>> {
    return this.http.get<Paginado<EDTP>>(`${this.base}/edtps/`, { params: this.params(params) });
  }

  obtenerEdtp(id: string): Observable<EDTP> {
    return this.http.get<EDTP>(`${this.base}/edtps/${id}/`);
  }

  actualizarEdtp(id: string, data: Partial<EDTP>): Observable<EDTP> {
    return this.http.patch<EDTP>(`${this.base}/edtps/${id}/`, data);
  }

  actualizarSeccion(id: string, data: Partial<SeccionEDTP>): Observable<SeccionEDTP> {
    return this.http.patch<SeccionEDTP>(`${this.base}/edtp-secciones/${id}/`, data);
  }

  crearEstudioTecnico(data: Partial<EstudioTecnico>): Observable<EstudioTecnico> {
    return this.http.post<EstudioTecnico>(`${this.base}/estudios-tecnicos/`, data);
  }

  actualizarEstudioTecnico(id: string, data: Partial<EstudioTecnico>): Observable<EstudioTecnico> {
    return this.http.patch<EstudioTecnico>(`${this.base}/estudios-tecnicos/${id}/`, data);
  }

  crearItemCosto(data: Partial<ItemCostoEDTP>): Observable<ItemCostoEDTP> {
    return this.http.post<ItemCostoEDTP>(`${this.base}/edtp-items-costo/`, data);
  }

  crearFinanciamiento(data: Partial<FuenteFinanciamientoEDTP>): Observable<FuenteFinanciamientoEDTP> {
    return this.http.post<FuenteFinanciamientoEDTP>(`${this.base}/edtp-financiamiento/`, data);
  }

  // -------------------------------------------------------------------------
  // Documentos generados (inventario documental)
  // -------------------------------------------------------------------------
  listarDocumentosGenerados(params?: {
    proyecto?: string;
    tipo_documento?: string;
    estado?: string;
  }): Observable<Paginado<DocumentoGenerado>> {
    return this.http.get<Paginado<DocumentoGenerado>>(`${this.base}/documentos-generados/`, {
      params: this.params(params),
    });
  }

  urlArchivo(archivo: string | null): string {
    if (!archivo) return '';
    if (archivo.startsWith('http')) return archivo;
    return `${window.location.origin}${archivo}`;
  }

  // -------------------------------------------------------------------------
  // Componentes / beneficiarios
  // -------------------------------------------------------------------------
  listarComponentes(proyecto: string): Observable<ComponenteProyecto[]> {
    return this.http.get<ComponenteProyecto[]>(`${this.base}/componentes/`, {
      params: this.params({ proyecto }),
    });
  }

  crearComponente(data: Partial<ComponenteProyecto>): Observable<ComponenteProyecto> {
    return this.http.post<ComponenteProyecto>(`${this.base}/componentes/`, data);
  }

  // -------------------------------------------------------------------------
  // Helpers de catálogo
  // -------------------------------------------------------------------------
  get estadosExpediente(): string[] {
    return ESTADOS_EXPEDIENTE;
  }

  get estadosCondicion(): string[] {
    return ESTADOS_CONDICION;
  }

  get estadosDocumento(): string[] {
    return ESTADOS_DOCUMENTO;
  }

  tipologiaNombre(codigo: string): string {
    return TIPOLOGIAS_RM115[codigo] ?? (codigo || 'Sin tipología');
  }
  condicionCategoria(codigo: string): string {
    return CATEGORIAS_CONDICION[codigo] ?? codigo;
  }

  etiquetaEstadoExpediente(estado: string): string {
    const mapa: Record<string, string> = {
      registrada: 'Registrada', en_admisibilidad: 'En admisibilidad',
      admitida: 'Admitida', itcp_elaboracion: 'ITCP en elaboración',
      itcp_revision: 'ITCP en revisión', itcp_aprobado: 'ITCP aprobado',
      edtp_elaboracion: 'EDTP en elaboración', edtp_revision: 'EDTP en revisión',
      edtp_aprobado: 'EDTP aprobado', viable: 'Viable',
      habilitado_poa: 'Habilitado para POA', enviado_poa: 'Enviado a SIS-POA',
      no_viable: 'No viable', archivado: 'Archivado',
    };
    return mapa[estado] ?? estado;
  }
}
