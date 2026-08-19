import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, finalize, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AlcanceOrganizacional {
  tipo: 'organizacional';
  unidad_id: string;
  unidad_nombre: string;
  sigla?: string;
  vigente_desde?: string | null;
  vigente_hasta?: string | null;
}

export interface CapabilitiesResponse {
  usuario: { id: string; email: string };
  roles: string[];
  capabilities: string[];
  alcances: AlcanceOrganizacional[];
}

/**
 * Consume /api/v2/me/capabilities (ADR-003).
 * El menú y las acciones del frontend se derivan de estas capacidades;
 * los roles no se codifican en componentes.
 */
@Injectable({ providedIn: 'root' })
export class CapabilitiesService {
  private base = environment.apiUrlV2;
  private capabilities: string[] = [];
  private alcances: AlcanceOrganizacional[] = [];
  /** Señal de que las capacidades ya fueron cargadas (menú dinámico). */
  cargadas$ = new BehaviorSubject<boolean>(false);

  constructor(private http: HttpClient) {}

  cargar(): Observable<CapabilitiesResponse> {
    return this.http.get<CapabilitiesResponse>(`${this.base}/me/capabilities/`).pipe(
      tap(data => {
        this.capabilities = data.capabilities ?? [];
        this.alcances = data.alcances ?? [];
      }),
      // La navegación debe continuar también cuando la petición falla.
      finalize(() => this.cargadas$.next(true)),
    );
  }

  tiene(codigo: string): boolean {
    return this.capabilities.includes(codigo);
  }

  tieneAlguna(codigos: string[]): boolean {
    return codigos.some(codigo => this.tiene(codigo));
  }

  listar(): string[] {
    return [...this.capabilities];
  }

  listarAlcances(): AlcanceOrganizacional[] {
    return [...this.alcances];
  }
}
