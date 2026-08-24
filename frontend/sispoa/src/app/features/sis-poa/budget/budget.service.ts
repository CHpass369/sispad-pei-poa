import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface FiscalYear {
  id: string;
  anio: number;
  estado: string;
  estado_display: string;
  descripcion: string;
  anio_inicio_plurianual: number | null;
  anio_fin_plurianual: number | null;
  fecha_apertura: string | null;
  fecha_cierre: string | null;
  fecha_inicio?: string | null;
  fecha_cierre_programada?: string | null;
  documento_habilitacion?: string | null;
  fecha_cargado?: string | null;
  encargado_cargado?: string | null;
  activa: boolean;
  gestion_anterior: number | null;
  /** Transiciones válidas resueltas por el backend (fuente única de verdad). */
  puede_habilitar?: boolean;
  puede_reabrir?: boolean;
  puede_cerrar?: boolean;
  puede_eliminar?: boolean;
}

export interface FiscalYearInput {
  anio: number;
  descripcion?: string;
  anio_inicio_plurianual?: number | null;
  anio_fin_plurianual?: number | null;
  fecha_inicio?: string | null;
  fecha_cierre_programada?: string | null;
  documento_habilitacion?: File | null;
  heredar_de?: number | null;
}

export interface DetalleCatalogo {
  id?: string;
  codigo: string;
  denominacion: string;
  /** Variante del endpoint /catalogs/ (GET /catalogs/ devuelve `nombre`). */
  nombre?: string;
}

export interface DetalleUnidad {
  id?: string;
  codigo: string;
  nombre: string;
}

// -- Categorías programáticas (Fase 3) -------------------------------------

export interface CategoriaProgramaticaTecho {
  id: number;
  gestion: number;
  codigo: string;
  denominacion: string;
  nivel: string;
  nivel_display: string;
  parent: number | null;
  estado: string;
  codigo_compuesto: string;
}

export interface ProgrammaticCategoryInput {
  /** UUID de la gestión, o el año. El backend acepta ambos. */
  gestion: string | number;
  codigo: string;
  denominacion: string;
  nivel: string;
  parent?: number | null;
}

export interface CategoriaNodo {
  id: string;
  codigo: string;
  denominacion: string;
  nivel: string;
  estado: string;
  hijos: CategoriaNodo[];
}

export interface CatalogoOpciones {
  fuentes: DetalleCatalogo[];
  organismos: DetalleCatalogo[];
  rubros: DetalleCatalogo[];
  objetos_gasto: DetalleCatalogo[];
  entidades_transferencia: DetalleCatalogo[];
  distritos: DetalleUnidad[];
  direcciones: DetalleUnidad[];
  unidades_ejecutoras: DetalleUnidad[];
  unidades_organizacionales: DetalleUnidad[];
}

// -- Distribución presupuestaria (Fase 4) -----------------------------------

export interface DistribucionVersion {
  id: number;
  gestion: string;
  gestion_anio: number;
  numero: number;
  estado: string;
  estado_display: string;
  hash: string;
  fecha_fijacion: string | null;
  fijado_por: number | null;
  fijado_por_email: string | null;
  observaciones: string;
  inmutable: boolean;
}

export interface AperturaFuente {
  id: number;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  monto: string;
}

export interface AllocationSourceInput {
  fuente: string;
  organismo?: string | null;
  monto: number | string;
}

export interface DetalleDistrito {
  codigo: string;
  nombre: string;
}

export interface DetalleCategoria {
  id: string;
  codigo: string;
  codigo_compuesto: string;
  denominacion: string;
}

export interface Apertura {
  id: number;
  gestion: string;
  gestion_anio: number;
  version: number | null;
  orden: number;
  unidad_organizacional: string | null;
  unidad_detalle: DetalleUnidad | null;
  distrito: string | null;
  distrito_detalle: DetalleDistrito | null;
  da: string | null;
  da_detalle: DetalleUnidad | null;
  ue: string | null;
  ue_detalle: DetalleUnidad | null;
  categoria: number | null;
  categoria_detalle: DetalleCategoria | null;
  proyecto_codigo: string;
  codigo_sisin: string;
  actividad_codigo: string;
  denominacion: string;
  tipo_apertura: string;
  estado: string;
  estado_display: string;
  fuentes: AperturaFuente[];
  total: string;
}

export interface AllocationInput {
  gestion: string;
  denominacion: string;
  categoria?: number | null;
  distrito?: string | null;
  da?: string | null;
  ue?: string | null;
  unidad_organizacional?: string | null;
  proyecto_codigo?: string;
  codigo_sisin?: string;
  actividad_codigo?: string;
  orden?: number;
  fuentes?: AllocationSourceInput[];
}

export interface Reserva {
  id: number;
  gestion: string;
  gestion_anio: number;
  version: number | null;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  tipo: string;
  tipo_display: string;
  monto: string;
  motivo: string;
  estado: string;
  estado_display: string;
}

export interface ReserveInput {
  gestion: string;
  fuente: string;
  organismo?: string | null;
  tipo?: string;
  monto: number | string;
  motivo?: string;
}

export interface DistribucionPorFuente {
  fuente_id: string;
  denominacion: string;
  techo: string;
  distribuido: string;
  reservado: string;
  disponible: string;
  porcentaje: number;
}

export interface DistributionSummary {
  gestion: number;
  techo_distribuible: string;
  distribuido: string;
  reservado: string;
  disponible: string;
  porcentaje: number;
  aperturas_count: number;
  por_fuente: DistribucionPorFuente[];
}

/** Fila de la validación de fijación (Fase 7): diferencia por fuente. */
export interface DiferenciaFuente {
  fuente_id: string;
  denominacion: string;
  techo: string;
  distribuido: string;
  reservado: string;
  diferencia: string;
}

/** Resultado de validar_distribucion_completa (Fase 7, §49-52). */
export interface ValidacionDistribucion {
  valida: boolean;
  diferencias: DiferenciaFuente[];
}

// -- Objetos del gasto (Fase 9) ---------------------------------------------

/** Programación de un objeto del gasto en una apertura (Fase 9, §90-91). */
export interface ExpenseObject {
  id: number;
  allocation: number;
  objeto_gasto: string;
  objeto_gasto_detalle: DetalleCatalogo | null;
  monto: string;
  created_at: string;
  updated_at: string;
}

export interface ExpenseObjectInput {
  allocation: number | string;
  objeto_gasto: string;
  monto: string | number;
}

/** Saldos de una apertura para la programación (§90): techo/programado/disponible. */
export interface ResumenApertura {
  valido: boolean;
  errores: string[];
  techo: string;
  programado: string;
  disponible: string;
}

/** Error de la API V2: {error: {detail}, code?, details?}. */
export interface ApiErrorResponse {
  error?: { detail?: string | string[] } | Record<string, unknown>;
  code?: string;
  details?: { requested?: string; available?: string; difference?: string };
}

// -- Reformulaciones (Fase 10, §92-97) --------------------------------------

export type TipoReform =
  | 'TRASPASO'
  | 'INCREMENTO'
  | 'DISMINUCION'
  | 'NUEVA_APERTURA'
  | 'CIERRE_APERTURA'
  | 'CAMBIO_FUENTE'
  | 'AJUSTE_DISTRIBUCION';

export type EstadoReform =
  | 'BORRADOR'
  | 'EN_REVISION'
  | 'OBSERVADA'
  | 'APROBADA'
  | 'APLICADA'
  | 'RECHAZADA';

export interface DetalleAperturaReform {
  id: string;
  denominacion: string;
  codigo_sisin: string;
}

export interface ReformaMovimiento {
  id: number;
  tipo: string;
  tipo_display: string;
  apertura_origen: number | null;
  apertura_origen_detalle: DetalleAperturaReform | null;
  apertura_destino: number | null;
  apertura_destino_detalle: DetalleAperturaReform | null;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  monto: string;
  saldo_antes: string | null;
  saldo_despues: string | null;
  motivo: string;
}

export interface ReformMovementInput {
  tipo: string;
  apertura_origen?: number | null;
  apertura_destino?: number | null;
  fuente?: string | null;
  organismo?: string | null;
  monto: string | number;
  motivo?: string;
}

export interface Reforma {
  id: number;
  gestion: string;
  gestion_anio: number;
  tipo: string;
  tipo_display: string;
  estado: string;
  estado_display: string;
  motivo: string;
  resolucion: string;
  documento: number | null;
  version_origen: number | null;
  version_origen_numero: number | null;
  version_resultante: number | null;
  solicitada_por: string;
  solicitada_por_email: string;
  aprobada_por: string | null;
  aprobada_por_email: string | null;
  fecha_aplicacion: string | null;
  movimientos: ReformaMovimiento[];
  created_at: string;
}

export interface ReformInput {
  gestion: string;
  tipo: string;
  motivo?: string;
  resolucion?: string;
  documento?: number | null;
  movimientos: ReformMovementInput[];
}

// -- Auditoría de trazabilidad (Fase 11) ------------------------------------

/** Evento de auditoría del ciclo (GET /budget/audit/, EventoAuditoria). */
export interface AuditEvent {
  id: string;
  usuario: string | null;
  usuario_email: string | null;
  usuario_nombre: string;
  accion: string;
  accion_display: string;
  entidad: string;
  entidad_display: string;
  entidad_id: string;
  version: number | null;
  resumen: string;
  datos_previos: Record<string, unknown> | null;
  datos_posteriores: Record<string, unknown> | null;
  direccion_ip: string | null;
  gestion: number | null;
  creado_en: string;
}

/** Slugs de entidad del ciclo aceptados por ?entidad= en /budget/audit/. */
export const ENTIDADES_AUDITORIA: { valor: string; etiqueta: string }[] = [
  { valor: 'allocation', etiqueta: 'Apertura programática' },
  { valor: 'reserve', etiqueta: 'Reserva' },
  { valor: 'directive-ceiling', etiqueta: 'Techo directivo' },
  { valor: 'distribution', etiqueta: 'Distribución' },
  { valor: 'expense-object', etiqueta: 'Objeto del gasto' },
  { valor: 'reform', etiqueta: 'Reformulación' },
  { valor: 'import', etiqueta: 'Importación' },
  { valor: 'territorial', etiqueta: 'Distribución territorial' },
  { valor: 'fiscal-year', etiqueta: 'Gestión fiscal' },
];

/** Acciones del catálogo EventoAuditoria.Accion (código → etiqueta). */
export const ACCIONES_AUDITORIA: { valor: string; etiqueta: string }[] = [
  { valor: 'crear', etiqueta: 'Creación' },
  { valor: 'modificar', etiqueta: 'Modificación' },
  { valor: 'anular', etiqueta: 'Anulación' },
  { valor: 'enviar', etiqueta: 'Envío' },
  { valor: 'devolver', etiqueta: 'Devolución' },
  { valor: 'aprobar', etiqueta: 'Aprobación / fijación' },
  { valor: 'importar', etiqueta: 'Importación' },
  { valor: 'cerrar', etiqueta: 'Cierre' },
  { valor: 'restaurar', etiqueta: 'Restauración' },
  { valor: 'consolidar', etiqueta: 'Consolidación' },
];

export interface AuditFilter {
  gestion?: string;
  entidad?: string;
  registro_id?: string;
  usuario?: string;
  accion?: string;
  desde?: string;
  hasta?: string;
  page?: number;
}


/** Composición del techo directivo (§22). Montos en string (convención API). */
export interface Composition {
  gestion: number;
  version: number | null;
  estado: string | null;
  sigep: string;
  municipales: string;
  saldos: string;
  otros: string;
  gastos_obligatorios: string;
  reservas: string;
  techo_bruto: string;
  techo_distribuible: string;
  por_fuente: { fuente: string; denominacion: string; monto: string }[];
}

export interface RecursoTecho {
  id: number;
  version: number;
  origen: string;
  origen_display: string;
  rubro: string | null;
  rubro_detalle: DetalleCatalogo | null;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  entidad_otorgante: string | null;
  entidad_detalle: DetalleCatalogo | null;
  concepto: string;
  monto: string;
  documento: number | null;
  documento_nombre: string | null;
}

export interface CeilingResourceInput {
  version: number;
  origen: string;
  rubro?: string | null;
  fuente?: string | null;
  organismo?: string | null;
  concepto?: string;
  monto: string | number;
}

export interface GastoObligatorio {
  id: number;
  version: number;
  da: string | null;
  da_detalle: DetalleUnidad | null;
  ue: string | null;
  ue_detalle: DetalleUnidad | null;
  programa: string;
  actividad: string;
  denominacion: string;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  objeto_gasto: string | null;
  objeto_gasto_detalle: DetalleCatalogo | null;
  entidad_transferencia: string;
  monto: string;
  documento: number | null;
  documento_nombre: string | null;
}

export interface MandatoryExpenseInput {
  version: number;
  programa?: string;
  actividad?: string;
  denominacion?: string;
  fuente?: string | null;
  organismo?: string | null;
  objeto_gasto?: string | null;
  monto: string | number;
}

export interface TechoVersion {
  id: number;
  numero: number;
  estado: string;
  estado_display: string;
  hash: string;
  fecha_fijacion: string | null;
  fijado_por: number | null;
  fijado_por_email: string | null;
  observaciones: string;
  inmutable: boolean;
  recursos: RecursoTecho[];
  gastos_obligatorios: GastoObligatorio[];
}

export interface TechoDirectivo {
  id: number;
  gestion: string;
  gestion_anio: number;
  estado: string;
  estado_display: string;
  version_actual: number;
  version: TechoVersion | null;
  composicion: Composition | null;
  created_at: string;
  updated_at: string;
}

export interface DirectiveCeilingInput {
  gestion: string;
}

export interface DocumentoPresupuestario {
  id: number;
  gestion: string;
  gestion_anio: number;
  tipo: string;
  tipo_display: string;
  nombre: string;
  mime_type: string;
  size: number;
  sha256: string;
  fecha_documento: string | null;
  storage_path: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

interface Paginado<T> {
  count: number;
  results: T[];
}

// -- Importaciones Excel (Fase 5) -------------------------------------------

export interface ImportMapeo {
  hoja?: string;
  columnas?: Record<string, string>;
  fuentes?: Record<string, string>;
}

export interface Importacion {
  id: number;
  gestion: string;
  gestion_anio: number;
  perfil: string;
  perfil_display: string;
  filename: string;
  mime_type: string;
  size: number;
  sha256: string;
  hoja_seleccionada: string;
  mapeo_json: ImportMapeo;
  estado: string;
  estado_display: string;
  tipo_importacion: string;
  storage_path: string;
  conteos: Record<string, number>;
  created_at: string;
}

export interface ImportMapeoBody {
  hoja: string;
  mapeo?: { columnas?: Record<string, string | null>; fuentes?: Record<string, string> };
}

export interface ImportErrorItem {
  id: number;
  detalle: number | null;
  fila: number;
  campo: string;
  valor_original: string;
  valor_normalizado: string;
  severidad: string;
  severidad_display: string;
  mensaje: string;
  accion: string;
  accion_display: string;
  resuelto: boolean;
}

export interface ImportResultado {
  aperturas_creadas: number;
  total_importado: string;
}

// -- Distribución territorial (Fase 6) --------------------------------------

export interface AsignacionTerritorial {  id: number;
  distrito: string;
  distrito_detalle: DetalleDistrito;
  poblacion: number | null;
  porcentaje: string | null;
  monto_calculado: string;
  ajuste: string;
  monto_final: string;
}

export interface TerritorialRow {
  distrito: string;
  poblacion?: number | null;
  porcentaje?: string | number | null;
  monto?: string | number | null;
}

export interface DistribucionTerritorial {
  id: number;
  gestion: string;
  gestion_anio: number;
  version: number | null;
  fuente: string | null;
  fuente_detalle: DetalleCatalogo | null;
  organismo: string | null;
  organismo_detalle: DetalleCatalogo | null;
  metodo: string;
  metodo_display: string;
  bolsa_total: string;
  estado: string;
  estado_display: string;
  observaciones: string;
  asignaciones: AsignacionTerritorial[];
  total_asignado: string;
}

export interface TerritorialDistributionInput {
  gestion: string;
  fuente: string;
  organismo?: string | null;
  metodo: string;
  bolsa_total: string | number;
  observaciones?: string;
  distritos?: TerritorialRow[];
}

/** Campos destino del mapeo columna -> campo (con etiqueta en español). */
export const CAMPOS_IMPORTACION: { valor: string; etiqueta: string }[] = [
  { valor: 'unidad', etiqueta: 'Unidad ejecutiva' },
  { valor: 'distrito', etiqueta: 'Distrito' },
  { valor: 'da', etiqueta: 'Dirección administrativa' },
  { valor: 'ue', etiqueta: 'Unidad ejecutora' },
  { valor: 'tipo', etiqueta: 'Tipo (V: P/SP/TS/T)' },
  { valor: 'programa', etiqueta: 'Programa' },
  { valor: 'subprograma', etiqueta: 'Subprograma' },
  { valor: 'sisin', etiqueta: 'Código SISIN' },
  { valor: 'actividad', etiqueta: 'Actividad' },
  { valor: 'denominacion', etiqueta: 'Denominación del proyecto' },
  { valor: 'saldo', etiqueta: 'Saldo gestión anterior' },
  { valor: 'ct', etiqueta: 'CT (monto)' },
  { valor: 're', etiqueta: 'RE (monto)' },
  { valor: 'ore', etiqueta: 'ORE (monto)' },
  { valor: 'idh', etiqueta: 'IDH (monto)' },
  { valor: 'tgn', etiqueta: 'TGN (monto)' },
  { valor: 'total', etiqueta: 'Total presupuesto' },
];

/** Fila del Presupuesto General de Recursos, tal como sale del reporte oficial. */
export interface FilaRecurso {
  id: number;
  concepto: string;
  origen: string;
  fuente: string;
  organismo: string;
  ff_of: string;
  monto: string;
  /** Nulo cuando el divisor es cero: la planilla mostraba #DIV/0!. */
  porcentaje: string | null;
  monto_corriente: string | null;
  porcentaje_corriente: string | null;
  monto_inversion: string | null;
  porcentaje_inversion: string | null;
  orden: number;
  componentes?: FilaRecurso[];
}

/** Un par FF/OF con su monto acumulado; lo calcula el backend. */
export interface ResumenFuente {
  ff_of: string;
  fuente: string;
  organismo: string;
  monto: string;
  porcentaje: string | null;
}

export interface PresupuestoRecursos {
  gestion: number;
  estado: string;
  editable: boolean;
  version_id: number | null;
  por_fuente: ResumenFuente[];
  rubros: FilaRecurso[];
  total: {
    monto: string;
    porcentaje: string | null;
    monto_corriente: string;
    porcentaje_corriente: string | null;
    monto_inversion: string;
    porcentaje_inversion: string | null;
  };
}

/** Servicio tipado del ciclo presupuestario SIS-POA (ADR-002): V2 puro. */
@Injectable({ providedIn: 'root' })

export class BudgetService {
  private base = environment.apiUrlV2 + '/sis-poa/budget';

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

  // -- Gestión fiscal (Fase 1) ----------------------------------------------

  listar(params?: { anio?: number; estado?: string }): Observable<Paginado<FiscalYear>> {
    return this.http.get<Paginado<FiscalYear>>(`${this.base}/fiscal-years/`, {
      params: this.params(params),
    });
  }

  crear(data: FiscalYearInput): Observable<FiscalYear> {
    const { documento_habilitacion, ...jsonData } = data;
    if (!documento_habilitacion) {
      return this.http.post<FiscalYear>(`${this.base}/fiscal-years/`, jsonData);
    }

    const formData = new FormData();
    Object.entries(jsonData).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });
    formData.append('documento_habilitacion', documento_habilitacion);
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/`, formData);
  }

  habilitar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/enable/`, {});
  }

  cerrar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/close/`, {});
  }

  /** CERRADA → HABILITADA. El motivo es obligatorio y queda en auditoría. */
  reabrir(id: string, motivo: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(
      `${this.base}/fiscal-years/${id}/reopen/`,
      { motivo },
    );
  }

  eliminar(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/fiscal-years/${id}/`);
  }

  // -- Techo directivo (Fase 2) ----------------------------------------------

  listarTechos(params?: { estado?: string }): Observable<Paginado<TechoDirectivo>> {
    return this.http.get<Paginado<TechoDirectivo>>(
      `${this.base}/directive-ceilings/`,
      { params: this.params(params) },
    );
  }

  crearTecho(data: DirectiveCeilingInput): Observable<TechoDirectivo> {
    return this.http.post<TechoDirectivo>(`${this.base}/directive-ceilings/`, data);
  }

  obtenerTecho(id: number): Observable<TechoDirectivo> {
    return this.http.get<TechoDirectivo>(`${this.base}/directive-ceilings/${id}/`);
  }

  eliminarTecho(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/directive-ceilings/${id}/`);
  }

  composicionTecho(id: number): Observable<Composition> {
    return this.http.get<Composition>(
      `${this.base}/directive-ceilings/${id}/composition/`,
    );
  }

  enviarRevision(id: number): Observable<TechoDirectivo> {
    return this.http.post<TechoDirectivo>(
      `${this.base}/directive-ceilings/${id}/submit/`, {},
    );
  }

  observarTecho(id: number, observaciones: string): Observable<TechoDirectivo> {
    return this.http.post<TechoDirectivo>(
      `${this.base}/directive-ceilings/${id}/observe/`, { observaciones },
    );
  }

  aprobarTecho(id: number): Observable<TechoDirectivo> {
    return this.http.post<TechoDirectivo>(
      `${this.base}/directive-ceilings/${id}/approve/`, {},
    );
  }

  fijarTecho(id: number, observaciones = ''): Observable<TechoDirectivo> {
    return this.http.post<TechoDirectivo>(
      `${this.base}/directive-ceilings/${id}/freeze/`, { observaciones },
    );
  }

  // -- Recursos (Fase 2) -----------------------------------------------------

  listarRecursos(params?: { version?: number; origen?: string }): Observable<Paginado<RecursoTecho>> {
    return this.http.get<Paginado<RecursoTecho>>(`${this.base}/resources/`, {
      params: this.params(params),
    });
  }

  crearRecurso(data: CeilingResourceInput): Observable<RecursoTecho> {
    return this.http.post<RecursoTecho>(`${this.base}/resources/`, data);
  }

  eliminarRecurso(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/resources/${id}/`);
  }

  // -- Gastos obligatorios (Fase 2) ------------------------------------------

  listarGastos(params?: { version?: number }): Observable<Paginado<GastoObligatorio>> {
    return this.http.get<Paginado<GastoObligatorio>>(
      `${this.base}/mandatory-expenses/`,
      { params: this.params(params) },
    );
  }

  crearGasto(data: MandatoryExpenseInput): Observable<GastoObligatorio> {
    return this.http.post<GastoObligatorio>(`${this.base}/mandatory-expenses/`, data);
  }

  eliminarGasto(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/mandatory-expenses/${id}/`);
  }

  // -- Documentos (Fase 2) ---------------------------------------------------

  listarDocumentos(gestion: string): Observable<Paginado<DocumentoPresupuestario>> {
    return this.http.get<Paginado<DocumentoPresupuestario>>(`${this.base}/documents/`, {
      params: this.params({ gestion }),
    });
  }

  subirDocumento(formData: FormData): Observable<DocumentoPresupuestario> {
    return this.http.post<DocumentoPresupuestario>(`${this.base}/documents/`, formData);
  }

  // -- Categorías programáticas y catálogos (Fase 3) -------------------------

  listarCategorias(params?: { gestion?: string | number; nivel?: string }): Observable<Paginado<CategoriaProgramaticaTecho>> {
    return this.http.get<Paginado<CategoriaProgramaticaTecho>>(
      `${this.base}/programmatic-categories/`,
      { params: this.params(params) },
    );
  }

  crearCategoria(data: ProgrammaticCategoryInput): Observable<CategoriaProgramaticaTecho> {
    return this.http.post<CategoriaProgramaticaTecho>(`${this.base}/programmatic-categories/`, data);
  }

  arbolCategorias(gestion: number): Observable<CategoriaNodo[]> {
    return this.http.get<CategoriaNodo[]>(`${this.base}/programmatic-categories/tree/`, {
      params: this.params({ gestion }),
    });
  }

  duplicarCategoria(id: number, gestionDestino: string | number): Observable<unknown> {
    return this.http.post(`${this.base}/programmatic-categories/${id}/duplicar_a_gestion/`, {
      gestion_destino: gestionDestino,
    });
  }

  opcionesCatalogo(params?: { gestion?: number }): Observable<CatalogoOpciones> {
    return this.http.get<CatalogoOpciones>(`${this.base}/catalogs/`, {
      params: this.params(params),
    });
  }

  // -- Distribución presupuestaria (Fase 4) ---------------------------------

  resumenDistribucion(gestion: string): Observable<DistributionSummary> {
    return this.http.get<DistributionSummary>(
      `${this.base}/distributions/dashboard/`,
      { params: this.params({ gestion }) },
    );
  }

  listarVersionesDistribucion(gestion: string): Observable<DistribucionVersion[]> {
    return this.http.get<DistribucionVersion[]>(
      `${this.base}/distributions/versions/`,
      { params: this.params({ gestion }) },
    );
  }

  listarAperturas(params?: {
    gestion?: string;
    version?: number;
    distrito?: string;
    categoria?: number;
    estado?: string;
    search?: string;
  }): Observable<Paginado<Apertura>> {
    return this.http.get<Paginado<Apertura>>(`${this.base}/allocations/`, {
      params: this.params(params),
    });
  }

  crearApertura(data: AllocationInput): Observable<Apertura> {
    return this.http.post<Apertura>(`${this.base}/allocations/`, data);
  }

  actualizarApertura(id: number, data: Partial<AllocationInput>): Observable<Apertura> {
    return this.http.patch<Apertura>(`${this.base}/allocations/${id}/`, data);
  }

  eliminarApertura(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/allocations/${id}/`);
  }

  cerrarApertura(id: number): Observable<Apertura> {
    return this.http.post<Apertura>(`${this.base}/allocations/${id}/cerrar/`, {});
  }

  listarReservas(params?: { gestion?: string; estado?: string }): Observable<Paginado<Reserva>> {
    return this.http.get<Paginado<Reserva>>(`${this.base}/reserves/`, {
      params: this.params(params),
    });
  }

  crearReserva(data: ReserveInput): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.base}/reserves/`, data);
  }

  liberarReserva(id: number): Observable<Reserva> {
    return this.http.post<Reserva>(`${this.base}/reserves/${id}/liberar/`, {});
  }

  // -- Fijación de la distribución (Fase 7) ---------------------------------

  validarDistribucion(id: number): Observable<ValidacionDistribucion> {
    return this.http.get<ValidacionDistribucion>(
      `${this.base}/distributions/${id}/validate/`,
    );
  }

  submitDistribucion(id: number): Observable<DistribucionVersion> {
    return this.http.post<DistribucionVersion>(
      `${this.base}/distributions/${id}/submit/`, {},
    );
  }

  observarDistribucion(id: number, observaciones: string): Observable<DistribucionVersion> {
    return this.http.post<DistribucionVersion>(
      `${this.base}/distributions/${id}/observe/`, { observaciones },
    );
  }

  aprobarDistribucion(id: number): Observable<DistribucionVersion> {
    return this.http.post<DistribucionVersion>(
      `${this.base}/distributions/${id}/approve/`, {},
    );
  }

  fijarDistribucion(id: number, observaciones = ''): Observable<DistribucionVersion> {
    return this.http.post<DistribucionVersion>(
      `${this.base}/distributions/${id}/freeze/`, { observaciones },
    );
  }

  ajusteDistribucion(id: number): Observable<DistribucionVersion> {
    return this.http.post<DistribucionVersion>(
      `${this.base}/distributions/${id}/ajuste/`, {},
    );
  }

  // -- Importaciones Excel (Fase 5) -----------------------------------------

  subirImportacion(formData: FormData): Observable<Importacion> {
    return this.http.post<Importacion>(`${this.base}/imports/`, formData);
  }

  listarImportaciones(params?: { gestion?: string; estado?: string }): Observable<Paginado<Importacion>> {
    return this.http.get<Paginado<Importacion>>(`${this.base}/imports/`, {
      params: this.params(params),
    });
  }

  detalleImportacion(id: number): Observable<Importacion> {
    return this.http.get<Importacion>(`${this.base}/imports/${id}/`);
  }

  hojasImportacion(id: number): Observable<{ hojas: string[] }> {
    return this.http.get<{ hojas: string[] }>(`${this.base}/imports/${id}/hojas/`);
  }

  mapearImportacion(id: number, body: ImportMapeoBody): Observable<Importacion> {
    return this.http.post<Importacion>(`${this.base}/imports/${id}/map/`, body);
  }

  validarImportacion(id: number): Observable<Importacion> {
    return this.http.post<Importacion>(`${this.base}/imports/${id}/validate/`, {});
  }

  erroresImportacion(id: number, params?: { severidad?: string }): Observable<ImportErrorItem[]> {
    return this.http.get<ImportErrorItem[]>(`${this.base}/imports/${id}/errors/`, {
      params: this.params(params),
    });
  }

  aplicarImportacion(id: number): Observable<Importacion & { resultado?: ImportResultado }> {
    return this.http.post<Importacion & { resultado?: ImportResultado }>(
      `${this.base}/imports/${id}/apply/`, {},
    );
  }

  // -- Distribución territorial (Fase 6) -------------------------------------

  listarTerritoriales(params?: { gestion?: string; estado?: string }): Observable<Paginado<DistribucionTerritorial>> {
    return this.http.get<Paginado<DistribucionTerritorial>>(
      `${this.base}/territorial-distributions/`,
      { params: this.params(params) },
    );
  }

  crearTerritorial(data: TerritorialDistributionInput): Observable<DistribucionTerritorial> {
    return this.http.post<DistribucionTerritorial>(
      `${this.base}/territorial-distributions/`, data,
    );
  }

  calcularTerritorial(id: number, distritos?: TerritorialRow[]): Observable<DistribucionTerritorial> {
    return this.http.post<DistribucionTerritorial>(
      `${this.base}/territorial-distributions/${id}/calcular/`,
      distritos ? { distritos } : {},
    );
  }

  aplicarTerritorial(id: number): Observable<DistribucionTerritorial> {
    return this.http.post<DistribucionTerritorial>(
      `${this.base}/territorial-distributions/${id}/aplicar/`, {},
    );
  }

  liberarTerritorial(id: number): Observable<DistribucionTerritorial> {
    return this.http.post<DistribucionTerritorial>(
      `${this.base}/territorial-distributions/${id}/liberar/`, {},
    );
  }

  // -- Objetos del gasto (Fase 9) -------------------------------------------

  listarObjetosGasto(params?: {
    allocation?: number | string;
  }): Observable<Paginado<ExpenseObject>> {
    return this.http.get<Paginado<ExpenseObject>>(
      `${this.base}/expense-objects/`,
      { params: this.params(params) },
    );
  }

  programarObjetoGasto(data: ExpenseObjectInput): Observable<ExpenseObject> {
    return this.http.post<ExpenseObject>(
      `${this.base}/expense-objects/`, data,
    );
  }

  actualizarObjetoGasto(id: number, monto: string | number): Observable<ExpenseObject> {
    return this.http.patch<ExpenseObject>(
      `${this.base}/expense-objects/${id}/`, { monto },
    );
  }

  eliminarObjetoGasto(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/expense-objects/${id}/`);
  }

  resumenApertura(allocationId: number | string): Observable<ResumenApertura> {
    return this.http.post<ResumenApertura>(
      `${this.base}/control/validate/`,
      { tipo: 'allocation', allocation: allocationId },
    );
  }

  // -- Reformulaciones (Fase 10) ---------------------------------------------

  listarReforms(params?: { gestion?: string; estado?: string; tipo?: string }):
    Observable<Paginado<Reforma>> {
    return this.http.get<Paginado<Reforma>>(`${this.base}/reforms/`, {
      params: this.params(params),
    });
  }

  crearReform(data: ReformInput): Observable<Reforma> {
    return this.http.post<Reforma>(`${this.base}/reforms/`, data);
  }

  detalleReform(id: number): Observable<Reforma> {
    return this.http.get<Reforma>(`${this.base}/reforms/${id}/`);
  }

  submitReform(id: number): Observable<Reforma> {
    return this.http.post<Reforma>(`${this.base}/reforms/${id}/submit/`, {});
  }

  observarReform(id: number, motivo: string): Observable<Reforma> {
    return this.http.post<Reforma>(
      `${this.base}/reforms/${id}/observe/`, { observaciones: motivo },
    );
  }

  aprobarReform(id: number): Observable<Reforma> {
    return this.http.post<Reforma>(`${this.base}/reforms/${id}/approve/`, {});
  }

  rechazarReform(id: number, motivo: string): Observable<Reforma> {
    return this.http.post<Reforma>(
      `${this.base}/reforms/${id}/reject/`, { motivo },
    );
  }

  aplicarReform(id: number): Observable<Reforma> {
    return this.http.post<Reforma>(`${this.base}/reforms/${id}/apply/`, {});
  }

  // -- Auditoría de trazabilidad (Fase 11) ----------------------------------

  listarAuditoria(params?: AuditFilter): Observable<Paginado<AuditEvent>> {
    return this.http.get<Paginado<AuditEvent>>(`${this.base}/audit/`, {
      params: this.params(params as Record<string, string | number | boolean>),
    });
  }

  /** Presupuesto General de Recursos de un techo, agrupado y con totales. */
  presupuestoRecursos(id: number) {
    return this.http.get<PresupuestoRecursos>(
      `${this.base}/directive-ceilings/${id}/presupuesto-recursos/`,
    );
  }

  actualizarRecurso(id: number, datos: Record<string, unknown>) {
    return this.http.patch(`${this.base}/resources/${id}/`, datos);
  }
}
