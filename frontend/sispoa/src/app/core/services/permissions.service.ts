import { Injectable } from '@angular/core';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class PermissionsService {
  constructor(private authService: AuthService) {}

  hasRole(role: string): boolean {
    return this.authService.hasRole(role);
  }

  hasAnyRole(roles: string[]): boolean {
    return roles.some(role => this.hasRole(role));
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
