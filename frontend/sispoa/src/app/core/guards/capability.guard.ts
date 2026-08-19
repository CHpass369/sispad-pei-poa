import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, UrlTree } from '@angular/router';
import { Observable, catchError, filter, map, of, take } from 'rxjs';
import { CapabilitiesService } from '../services/capabilities.service';
import { PermissionsService } from '../services/permissions.service';

/**
 * Guard de rutas V2 por capacidad (ADR-003).
 * Uso: { path: '...', canActivate: [CapabilityGuard],
 *        data: { capacidades: ['sis_pe.instrumento.read'] } }
 */
@Injectable({ providedIn: 'root' })
export class CapabilityGuard implements CanActivate {
  constructor(
    private permissions: PermissionsService,
    private capabilities: CapabilitiesService,
    private router: Router,
  ) {}

  canActivate(route: ActivatedRouteSnapshot): boolean | Observable<boolean | UrlTree> {
    const requeridas = route.data?.['capacidades'] as string[] | undefined;
    if (!requeridas?.length) {
      return true;
    }

    return this.capabilities.cargadas$.pipe(
      filter(cargadas => cargadas),
      take(1),
      map(() => this.permissions.hasAnyCapability(requeridas)
        ? true
        : this.router.parseUrl('/dashboard')),
      catchError(() => of(this.router.parseUrl('/dashboard'))),
    );
  }
}
