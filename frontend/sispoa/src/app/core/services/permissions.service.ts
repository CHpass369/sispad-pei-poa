import { Injectable } from '@angular/core';
import { AuthService } from './auth.service';
import { CapabilitiesService } from './capabilities.service';

@Injectable({ providedIn: 'root' })
export class PermissionsService {
  constructor(
    private authService: AuthService,
    private capabilitiesService: CapabilitiesService,
  ) {}

  /** Superuser tiene acceso a todo, sin importar roles asignados */
  private get isSuperuser(): boolean {
    // `userSubject` es privado y se alcanza por índice: un doble de
    // `AuthService` que no lo declare hacía reventar todo el filtrado del menú
    // con «Cannot read properties of undefined». Ausente equivale a «no es
    // superusuario», que es la respuesta segura.
    return this.authService['userSubject']?.value?.is_superuser ?? false;
  }

  hasRole(role: string): boolean {
    return this.isSuperuser || this.authService.hasRole(role);
  }

  hasAnyRole(roles: string[]): boolean {
    return this.isSuperuser || roles.some(role => this.hasRole(role));
  }

  /** Autorización V2 por capacidad (ADR-003): el backend es la autoridad. */
  hasCapability(codigo: string): boolean {
    return this.isSuperuser || this.capabilitiesService.tiene(codigo);
  }

  hasAnyCapability(codigos: string[]): boolean {
    return this.isSuperuser || this.capabilitiesService.tieneAlguna(codigos);
  }

  canEdit(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'planificador']);
  }

  canApprove(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin']);
  }

  canDelete(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin']);
  }

  isAdmin(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin']);
  }

  isPlanificador(): boolean {
    return this.hasRole('planificador');
  }

  isJefeUe(): boolean {
    return this.hasRole('jefe_ue');
  }

  isDirector(): boolean {
    return this.hasRole('director');
  }

  isEvaluador(): boolean {
    return this.hasRole('evaluador');
  }

  canAccessPlanificacion(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'planificador']);
  }

  canAccessPOAU(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'jefe_ue', 'director']);
  }

  canAccessEvaluacion(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'evaluador']);
  }

  canAccessSeguimiento(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'jefe_ue', 'director', 'tecnico']);
  }
}
