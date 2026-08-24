import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { Observable, catchError, filter, map, of, take } from 'rxjs';
import { GestionHabilitadaService } from '../services/gestion-habilitada.service';

/** A dónde se manda al usuario cuando no hay gestión habilitada. */
export const RUTA_HABILITACION = '/sis-poa/budget/gestion-fiscal';

/**
 * Candado duro de SIS-POA (ADR-007): sin gestión habilitada no se entra.
 *
 * Uso: `{ path: '...', canActivate: [GestionHabilitadaGuard] }`.
 *
 * Sin esto las pantallas se abrían igual y pedían datos de un año fantasma:
 * el resultado era una tabla vacía que se lee como "no hay nada cargado" en
 * lugar de "no hay gestión habilitada". La pantalla de habilitación queda
 * fuera del guard, porque es justamente donde se resuelve el problema.
 */
@Injectable({ providedIn: 'root' })
export class GestionHabilitadaGuard implements CanActivate {
  constructor(
    private gestion: GestionHabilitadaService,
    private router: Router,
  ) {}

  canActivate(): boolean | Observable<boolean | UrlTree> {
    return this.gestion.cargada$.pipe(
      filter(cargada => cargada),
      take(1),
      map(() => this.gestion.hayGestion()
        ? true
        : this.router.parseUrl(RUTA_HABILITACION)),
      catchError(() => of(this.router.parseUrl(RUTA_HABILITACION))),
    );
  }
}
