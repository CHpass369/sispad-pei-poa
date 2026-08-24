import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, finalize, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

/** La gestión fiscal habilitada, tal como la publica el backend. */
export interface GestionHabilitada {
  id: string;
  anio: number;
  estado: string;
  estado_display: string;
  fecha_apertura: string | null;
  fecha_cierre: string | null;
}

export interface RespuestaGestionHabilitada {
  habilitada: boolean;
  gestion: GestionHabilitada | null;
}

/**
 * El candado de gestión fiscal de SIS-POA (ADR-007).
 *
 * Una sola gestión está habilitada a la vez y TODOS los módulos de SIS-POA
 * operan sobre ella. Ningún componente elige el año ni lo escribe a mano: lo
 * lee de acá. Antes cada pantalla tenía el suyo clavado —unas en 2027 y otras
 * en 2026, que ya estaba cerrada— y la plataforma mostraba dos gestiones
 * distintas al mismo tiempo.
 *
 * NO aplica a SIS-PE (PAD/PEI): esa planificación es quinquenal 2026-2030 y
 * sus años son horizontes de plan, no gestiones fiscales operativas.
 *
 * Sigue el mismo idioma que `CapabilitiesService`: se carga una vez al
 * arranque y publica un latch para que el guard sepa cuándo ya se sabe.
 */
@Injectable({ providedIn: 'root' })
export class GestionHabilitadaService {
  private base = environment.apiUrlV2;
  private gestionActual: GestionHabilitada | null = null;
  /** Emite cuando la consulta terminó, con o sin gestión habilitada. */
  cargada$ = new BehaviorSubject<boolean>(false);

  constructor(private http: HttpClient) {}

  cargar(): Observable<RespuestaGestionHabilitada> {
    return this.http
      .get<RespuestaGestionHabilitada>(`${this.base}/sis-poa/budget/fiscal-years/activa/`)
      .pipe(
        tap(data => {
          this.gestionActual = data?.gestion ?? null;
        }),
        // La navegación debe continuar también cuando la petición falla: el
        // guard tratará "no se sabe" igual que "no hay gestión".
        finalize(() => this.cargada$.next(true)),
      );
  }

  /** La gestión habilitada, o `null` si no hay ninguna. */
  gestion(): GestionHabilitada | null {
    return this.gestionActual;
  }

  /**
   * El año sobre el que trabaja SIS-POA.
   *
   * Devuelve `null` —nunca el año del reloj— cuando no hay gestión habilitada:
   * inventar `getFullYear()` acá reintroduciría por la ventana el mismo
   * hardcode que este servicio vino a sacar (ADR-007 §3).
   */
  anio(): number | null {
    return this.gestionActual?.anio ?? null;
  }

  hayGestion(): boolean {
    return this.gestionActual !== null;
  }

  /** Refresca el candado tras habilitar o cerrar una gestión. */
  refrescar(): Observable<RespuestaGestionHabilitada> {
    return this.cargar();
  }
}
