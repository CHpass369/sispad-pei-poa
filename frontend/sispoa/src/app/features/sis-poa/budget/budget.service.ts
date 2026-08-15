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
  activa: boolean;
  gestion_anterior: number | null;
}

export interface FiscalYearInput {
  anio: number;
  descripcion?: string;
  anio_inicio_plurianual?: number | null;
  anio_fin_plurianual?: number | null;
  heredar_de?: number | null;
}

export interface DetalleCatalogo {
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

export interface ProgrammaticCategory {
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
  gestion: number;
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

export interface DistributionVersion {
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

export interface AllocationSource {
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

export interface Allocation {
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
  fuentes: AllocationSource[];
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

export interface Reserve {
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

export interface CeilingResource {
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

export interface MandatoryExpense {
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

export interface DirectiveCeilingVersion {
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
  recursos: CeilingResource[];
  gastos_obligatorios: MandatoryExpense[];
}

export interface DirectiveCeiling {
  id: number;
  gestion: string;
  gestion_anio: number;
  estado: string;
  estado_display: string;
  version_actual: number;
  version: DirectiveCeilingVersion | null;
  composicion: Composition | null;
  created_at: string;
  updated_at: string;
}

export interface DirectiveCeilingInput {
  gestion: string;
}

export interface BudgetDocument {
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

export interface BudgetImport {
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

export interface TerritorialAllocation {
  id: number;
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

export interface TerritorialDistribution {
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
  asignaciones: TerritorialAllocation[];
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
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/`, data);
  }

  habilitar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/enable/`, {});
  }

  cerrar(id: string): Observable<FiscalYear> {
    return this.http.post<FiscalYear>(`${this.base}/fiscal-years/${id}/close/`, {});
  }

  // -- Techo directivo (Fase 2) ----------------------------------------------

  listarTechos(params?: { estado?: string }): Observable<Paginado<DirectiveCeiling>> {
    return this.http.get<Paginado<DirectiveCeiling>>(
      `${this.base}/directive-ceilings/`,
      { params: this.params(params) },
    );
  }

  crearTecho(data: DirectiveCeilingInput): Observable<DirectiveCeiling> {
    return this.http.post<DirectiveCeiling>(`${this.base}/directive-ceilings/`, data);
  }

  obtenerTecho(id: number): Observable<DirectiveCeiling> {
    return this.http.get<DirectiveCeiling>(`${this.base}/directive-ceilings/${id}/`);
  }

  composicionTecho(id: number): Observable<Composition> {
    return this.http.get<Composition>(
      `${this.base}/directive-ceilings/${id}/composition/`,
    );
  }

  enviarRevision(id: number): Observable<DirectiveCeiling> {
    return this.http.post<DirectiveCeiling>(
      `${this.base}/directive-ceilings/${id}/submit/`, {},
    );
  }

  observarTecho(id: number, observaciones: string): Observable<DirectiveCeiling> {
    return this.http.post<DirectiveCeiling>(
      `${this.base}/directive-ceilings/${id}/observe/`, { observaciones },
    );
  }

  aprobarTecho(id: number): Observable<DirectiveCeiling> {
    return this.http.post<DirectiveCeiling>(
      `${this.base}/directive-ceilings/${id}/approve/`, {},
    );
  }

  fijarTecho(id: number, observaciones = ''): Observable<DirectiveCeiling> {
    return this.http.post<DirectiveCeiling>(
      `${this.base}/directive-ceilings/${id}/freeze/`, { observaciones },
    );
  }

  // -- Recursos (Fase 2) -----------------------------------------------------

  listarRecursos(params?: { version?: number; origen?: string }): Observable<Paginado<CeilingResource>> {
    return this.http.get<Paginado<CeilingResource>>(`${this.base}/resources/`, {
      params: this.params(params),
    });
  }

  crearRecurso(data: CeilingResourceInput): Observable<CeilingResource> {
    return this.http.post<CeilingResource>(`${this.base}/resources/`, data);
  }

  eliminarRecurso(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/resources/${id}/`);
  }

  // -- Gastos obligatorios (Fase 2) ------------------------------------------

  listarGastos(params?: { version?: number }): Observable<Paginado<MandatoryExpense>> {
    return this.http.get<Paginado<MandatoryExpense>>(
      `${this.base}/mandatory-expenses/`,
      { params: this.params(params) },
    );
  }

  crearGasto(data: MandatoryExpenseInput): Observable<MandatoryExpense> {
    return this.http.post<MandatoryExpense>(`${this.base}/mandatory-expenses/`, data);
  }

  eliminarGasto(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/mandatory-expenses/${id}/`);
  }

  // -- Documentos (Fase 2) ---------------------------------------------------

  listarDocumentos(gestion: string): Observable<Paginado<BudgetDocument>> {
    return this.http.get<Paginado<BudgetDocument>>(`${this.base}/documents/`, {
      params: this.params({ gestion }),
    });
  }

  subirDocumento(formData: FormData): Observable<BudgetDocument> {
    return this.http.post<BudgetDocument>(`${this.base}/documents/`, formData);
  }

  // -- Categorías programáticas y catálogos (Fase 3) -------------------------

  listarCategorias(params?: { gestion?: number; nivel?: string }): Observable<Paginado<ProgrammaticCategory>> {
    return this.http.get<Paginado<ProgrammaticCategory>>(
      `${this.base}/programmatic-categories/`,
      { params: this.params(params) },
    );
  }

  crearCategoria(data: ProgrammaticCategoryInput): Observable<ProgrammaticCategory> {
    return this.http.post<ProgrammaticCategory>(`${this.base}/programmatic-categories/`, data);
  }

  arbolCategorias(gestion: number): Observable<CategoriaNodo[]> {
    return this.http.get<CategoriaNodo[]>(`${this.base}/programmatic-categories/tree/`, {
      params: this.params({ gestion }),
    });
  }

  duplicarCategoria(id: number, gestionDestino: number): Observable<unknown> {
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

  listarVersionesDistribucion(gestion: string): Observable<DistributionVersion[]> {
    return this.http.get<DistributionVersion[]>(
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
  }): Observable<Paginado<Allocation>> {
    return this.http.get<Paginado<Allocation>>(`${this.base}/allocations/`, {
      params: this.params(params),
    });
  }

  crearApertura(data: AllocationInput): Observable<Allocation> {
    return this.http.post<Allocation>(`${this.base}/allocations/`, data);
  }

  actualizarApertura(id: number, data: Partial<AllocationInput>): Observable<Allocation> {
    return this.http.patch<Allocation>(`${this.base}/allocations/${id}/`, data);
  }

  eliminarApertura(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/allocations/${id}/`);
  }

  cerrarApertura(id: number): Observable<Allocation> {
    return this.http.post<Allocation>(`${this.base}/allocations/${id}/cerrar/`, {});
  }

  listarReservas(params?: { gestion?: string; estado?: string }): Observable<Paginado<Reserve>> {
    return this.http.get<Paginado<Reserve>>(`${this.base}/reserves/`, {
      params: this.params(params),
    });
  }

  crearReserva(data: ReserveInput): Observable<Reserve> {
    return this.http.post<Reserve>(`${this.base}/reserves/`, data);
  }

  liberarReserva(id: number): Observable<Reserve> {
    return this.http.post<Reserve>(`${this.base}/reserves/${id}/liberar/`, {});
  }

  // -- Fijación de la distribución (Fase 7) ---------------------------------

  validarDistribucion(id: number): Observable<ValidacionDistribucion> {
    return this.http.get<ValidacionDistribucion>(
      `${this.base}/distributions/${id}/validate/`,
    );
  }

  submitDistribucion(id: number): Observable<DistributionVersion> {
    return this.http.post<DistributionVersion>(
      `${this.base}/distributions/${id}/submit/`, {},
    );
  }

  observarDistribucion(id: number, observaciones: string): Observable<DistributionVersion> {
    return this.http.post<DistributionVersion>(
      `${this.base}/distributions/${id}/observe/`, { observaciones },
    );
  }

  aprobarDistribucion(id: number): Observable<DistributionVersion> {
    return this.http.post<DistributionVersion>(
      `${this.base}/distributions/${id}/approve/`, {},
    );
  }

  fijarDistribucion(id: number, observaciones = ''): Observable<DistributionVersion> {
    return this.http.post<DistributionVersion>(
      `${this.base}/distributions/${id}/freeze/`, { observaciones },
    );
  }

  ajusteDistribucion(id: number): Observable<DistributionVersion> {
    return this.http.post<DistributionVersion>(
      `${this.base}/distributions/${id}/ajuste/`, {},
    );
  }

  // -- Importaciones Excel (Fase 5) -----------------------------------------

  subirImportacion(formData: FormData): Observable<BudgetImport> {
    return this.http.post<BudgetImport>(`${this.base}/imports/`, formData);
  }

  listarImportaciones(params?: { gestion?: string; estado?: string }): Observable<Paginado<BudgetImport>> {
    return this.http.get<Paginado<BudgetImport>>(`${this.base}/imports/`, {
      params: this.params(params),
    });
  }

  detalleImportacion(id: number): Observable<BudgetImport> {
    return this.http.get<BudgetImport>(`${this.base}/imports/${id}/`);
  }

  hojasImportacion(id: number): Observable<{ hojas: string[] }> {
    return this.http.get<{ hojas: string[] }>(`${this.base}/imports/${id}/hojas/`);
  }

  mapearImportacion(id: number, body: ImportMapeoBody): Observable<BudgetImport> {
    return this.http.post<BudgetImport>(`${this.base}/imports/${id}/map/`, body);
  }

  validarImportacion(id: number): Observable<BudgetImport> {
    return this.http.post<BudgetImport>(`${this.base}/imports/${id}/validate/`, {});
  }

  erroresImportacion(id: number, params?: { severidad?: string }): Observable<ImportErrorItem[]> {
    return this.http.get<ImportErrorItem[]>(`${this.base}/imports/${id}/errors/`, {
      params: this.params(params),
    });
  }

  aplicarImportacion(id: number): Observable<BudgetImport & { resultado?: ImportResultado }> {
    return this.http.post<BudgetImport & { resultado?: ImportResultado }>(
      `${this.base}/imports/${id}/apply/`, {},
    );
  }

  // -- Distribución territorial (Fase 6) -------------------------------------

  listarTerritoriales(params?: { gestion?: string; estado?: string }): Observable<Paginado<TerritorialDistribution>> {
    return this.http.get<Paginado<TerritorialDistribution>>(
      `${this.base}/territorial-distributions/`,
      { params: this.params(params) },
    );
  }

  crearTerritorial(data: TerritorialDistributionInput): Observable<TerritorialDistribution> {
    return this.http.post<TerritorialDistribution>(
      `${this.base}/territorial-distributions/`, data,
    );
  }

  calcularTerritorial(id: number, distritos?: TerritorialRow[]): Observable<TerritorialDistribution> {
    return this.http.post<TerritorialDistribution>(
      `${this.base}/territorial-distributions/${id}/calcular/`,
      distritos ? { distritos } : {},
    );
  }

  aplicarTerritorial(id: number): Observable<TerritorialDistribution> {
    return this.http.post<TerritorialDistribution>(
      `${this.base}/territorial-distributions/${id}/aplicar/`, {},
    );
  }

  liberarTerritorial(id: number): Observable<TerritorialDistribution> {
    return this.http.post<TerritorialDistribution>(
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
}
