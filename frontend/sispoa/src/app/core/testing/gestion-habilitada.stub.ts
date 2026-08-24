import { BehaviorSubject, Observable, of } from 'rxjs';
import {
  GestionHabilitada,
  RespuestaGestionHabilitada,
} from '../services/gestion-habilitada.service';

/**
 * Doble de `GestionHabilitadaService` para specs.
 *
 * El candado se carga una vez al arranque de la aplicación (ADR-007), no por
 * pantalla. En un spec no hay arranque, así que sin este doble cada
 * componente de SIS-POA dispararía una petición extra a `fiscal-years/activa/`
 * que el `HttpTestingController` tendría que atender.
 */
export function gestionHabilitadaStub(
  anio = 2027,
  id = 'gestion-habilitada-stub',
) {
  const gestion: GestionHabilitada = {
    id,
    anio,
    estado: 'HABILITADA',
    estado_display: 'Habilitada',
    fecha_apertura: `${anio - 1}-08-01T00:00:00Z`,
    fecha_cierre: null,
  };
  return {
    cargada$: new BehaviorSubject<boolean>(true),
    gestion: () => gestion,
    anio: () => anio,
    hayGestion: () => true,
    cargar: (): Observable<RespuestaGestionHabilitada> =>
      of({ habilitada: true, gestion }),
    refrescar: (): Observable<RespuestaGestionHabilitada> =>
      of({ habilitada: true, gestion }),
  };
}

/** Doble para el caso "no hay ninguna gestión habilitada". */
export function sinGestionHabilitadaStub() {
  const vacio: RespuestaGestionHabilitada = { habilitada: false, gestion: null };
  return {
    cargada$: new BehaviorSubject<boolean>(true),
    gestion: () => null,
    anio: () => null,
    hayGestion: () => false,
    cargar: (): Observable<RespuestaGestionHabilitada> => of(vacio),
    refrescar: (): Observable<RespuestaGestionHabilitada> => of(vacio),
  };
}
