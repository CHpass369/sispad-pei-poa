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
}

export interface DetalleUnidad {
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
}
