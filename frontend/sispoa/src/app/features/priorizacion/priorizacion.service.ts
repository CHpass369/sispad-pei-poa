import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ProyectoCatalogo {
  id: string;
  nombre: string;
  sisin: string;
  categoria_programatica: string;
  denominacion_categoria: string;
  origen: string;
  veces_priorizado: number;
}

export interface ProyectoPriorizado {
  id?: string;
  orden?: number;
  nombre: string;
  catalogo?: string | null;
  sisin: string;
  categoria_programatica: string;
  denominacion_categoria?: string;
  monto: number | null;
  fuente?: string | null;
  organismo?: string | null;
  par_financiamiento?: string;
}

/** Fila del padrón maestro de organizaciones sociales territoriales. */
export interface OrganizacionTerritorial {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  tipo_display: string;
  distrito: string;
  distrito_codigo: string;
  dirigente: string;
  cargo: string;
  telefono: string;
}

export interface ActaPriorizacion {
  id?: string;
  gestion: number;
  numero?: number | null;
  distrito: string;
  distrito_nombre?: string;
  otb: string;
  unidad_territorial?: string | null;
  presidente: string;
  responsable_registro: string;
  fecha: string | null;
  es_pavimento?: boolean;
  fecha_hora_registro?: string;
  estado?: string;
  estado_display?: string;
  observacion?: string;
  monto_total?: number;
  esta_completa?: boolean;
  proyectos: ProyectoPriorizado[];
}

@Injectable({ providedIn: 'root' })
export class PriorizacionService {
  private base = `${environment.apiUrl}/priorizacion`;

  constructor(private http: HttpClient) {}

  /** Buscador incremental del nombre de proyecto: cada palabra acota más. */
  buscarProyectos(q: string, limite = 12): Observable<any> {
    return this.http.get(`${this.base}/catalogo-proyectos/`, {
      params: new HttpParams().set('q', q).set('limite', limite),
    });
  }

  listarActas(filtros: Record<string, any> = {}): Observable<any> {
    let params = new HttpParams();
    for (const [k, v] of Object.entries(filtros)) {
      if (v !== '' && v !== null && v !== undefined) { params = params.set(k, v); }
    }
    return this.http.get(`${this.base}/actas/`, { params });
  }

  obtenerActa(id: string): Observable<ActaPriorizacion> {
    return this.http.get<ActaPriorizacion>(`${this.base}/actas/${id}/`);
  }

  crearActa(acta: ActaPriorizacion): Observable<ActaPriorizacion> {
    return this.http.post<ActaPriorizacion>(`${this.base}/actas/`, acta);
  }

  actualizarActa(id: string, acta: ActaPriorizacion): Observable<ActaPriorizacion> {
    return this.http.put<ActaPriorizacion>(`${this.base}/actas/${id}/`, acta);
  }

  eliminarActa(id: string): Observable<any> {
    return this.http.delete(`${this.base}/actas/${id}/`);
  }

  revisar(id: string, accion: string, cuerpo: any = {}): Observable<any> {
    return this.http.post(`${this.base}/actas/${id}/${accion}/`, cuerpo);
  }

  actaOficial(id: string): Observable<any> {
    return this.http.get(`${this.base}/actas/${id}/acta-oficial/`);
  }

  /** El PDF lo arma el servidor con la medida oficio clavada. */
  actaPdf(id: string): Observable<Blob> {
    return this.http.get(`${this.base}/actas/${id}/pdf/`, {
      responseType: 'blob',
    });
  }

  /**
   * Reporte de proyectos programados del recorte que se está viendo.
   *
   * Viajan los mismos filtros que el listado y NO la página: el reporte es de
   * todo lo filtrado, no de los renglones que entraron en pantalla.
   */
  reporteProyectos(filtros: Record<string, any>, formato: 'xlsx' | 'pdf'):
      Observable<Blob> {
    let params = new HttpParams().set('formato', formato);
    for (const [k, v] of Object.entries(filtros)) {
      if (v !== '' && v !== null && v !== undefined) { params = params.set(k, v); }
    }
    return this.http.get(`${this.base}/actas/reporte/`, {
      params, responseType: 'blob',
    });
  }

  /** Sube el acta escaneada. El servidor la guarda cifrada. */
  adjuntar(id: string, archivo: File): Observable<any> {
    const cuerpo = new FormData();
    cuerpo.append('archivo', archivo);
    return this.http.post(`${this.base}/actas/${id}/adjuntar/`, cuerpo);
  }

  documentosDelActa(id: string): Observable<any> {
    return this.http.get(`${this.base}/actas/${id}/documentos/`);
  }

  descargarDocumento(documentoId: string): Observable<Blob> {
    return this.http.get(`${environment.apiUrl}/documentos/${documentoId}/descargar/`,
                         { responseType: 'blob' });
  }

  /** Matrices acumulativas de la gestión habilitada (la resuelve el backend). */
  matrices(): Observable<any> {
    return this.http.get(`${this.base}/matrices/`);
  }

  /** Categorías programáticas nivel ACTIVIDAD, para elegir a mano en el acta. */
  categorias(): Observable<any> {
    return this.http.get(`${this.base}/categorias-programaticas/`);
  }

  /** Techo, lo usado y lo que queda por par FF/OF. */
  saldos(excluirActa = ''): Observable<any> {
    let params = new HttpParams();
    if (excluirActa) { params = params.set('excluir_acta', excluirActa); }
    return this.http.get(`${this.base}/saldos/`, { params });
  }

  distritos(): Observable<any> {
    return this.http.get(`${environment.apiUrl}/distritos/`);
  }

  /**
   * Padrón de organizaciones con su dirigente vigente. Es el dominio que llena
   * «OTB / Junta vecinal» y «Presidente» en el acta. Sin distrito trae el
   * padrón entero: el formulario lo filtra en memoria, así que no hay una
   * consulta por tecla.
   */
  organizaciones(distritoId = ''): Observable<any> {
    let params = new HttpParams();
    if (distritoId) { params = params.set('distrito', distritoId); }
    return this.http.get(`${environment.apiUrl}/unidades-territoriales/dominio/`,
                         { params });
  }
}
