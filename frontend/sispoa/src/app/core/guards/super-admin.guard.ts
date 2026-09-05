import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { Observable, filter, map, take } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { PermissionsService } from '../services/permissions.service';

/**
 * Guard de rutas reservadas a administración.
 *
 * Espeja exactamente `IsSuperAdmin` del backend (`apps/core/permissions.py`):
 * superusuario de Django o rol `superadmin`, y nada más. No usa
 * `PermissionsService.isAdmin()` a propósito — ese incluye `tecnico_admin`, que
 * el backend rechaza: la pantalla se abriría y cada guardado moriría con 403.
 *
 * Uso: { path: '...', canActivate: [SuperAdminGuard] }
 */
@Injectable({ providedIn: 'root' })
export class SuperAdminGuard implements CanActivate {
  constructor(
    private auth: AuthService,
    private permissions: PermissionsService,
    private router: Router,
  ) {}

  canActivate(): Observable<boolean | UrlTree> {
    // El usuario llega por HTTP: sin esperarlo, una recarga directa sobre la
    // URL evaluaría el rol contra `null` y expulsaría a un administrador.
    return this.auth.user$.pipe(
      filter(usuario => usuario !== null),
      take(1),
      map(() => this.permissions.hasRole('superadmin')
        ? true
        : this.router.parseUrl('/dashboard')),
    );
  }
}
