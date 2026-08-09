import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router } from '@angular/router';
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
    private router: Router,
  ) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {
    const requeridas = route.data?.['capacidades'] as string[] | undefined;
    if (!requeridas?.length) {
      return true;
    }
    if (this.permissions.hasAnyCapability(requeridas)) {
      return true;
    }
    this.router.navigate(['/dashboard']);
    return false;
  }
}
