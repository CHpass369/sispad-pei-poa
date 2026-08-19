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
}

export interface ActaPriorizacion {
  id?: string;
  gestion: number;
  numero?: number | null;
  distrito: string;
  distrito_nombre?: string;
  otb: string;
  presidente: string;
  responsable_registro: string;
  fecha: string | null;
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

  matrices(gestion: number): Observable<any> {
    return this.http.get(`${this.base}/matrices/`, {
      params: new HttpParams().set('gestion', gestion),
    });
  }

  /** Categorías programáticas nivel ACTIVIDAD, para elegir a mano en el acta. */
  categorias(gestion = 2027): Observable<any> {
    return this.http.get(`${this.base}/categorias-programaticas/`, {
      params: new HttpParams().set('gestion', gestion),
    });
  }

  distritos(): Observable<any> {
    return this.http.get(`${environment.apiUrl}/distritos/`);
  }
}
