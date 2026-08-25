import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { forkJoin } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import {
  GestionHabilitada,
  GestionHabilitadaService,
} from '../../core/services/gestion-habilitada.service';
import { adminApiErrorMessage } from './admin-api-error';
import { fixedScopeForRole } from './admin-role-scope';
import {
  AdminApprovalPayload,
  AdminAssignmentScope,
  AdminRegistrationRequest,
  AdminRole,
  AdminSystem,
  AdminUsuariosService,
} from './admin-usuarios.service';

export interface RequestApprovalDialogData {
  request: AdminRegistrationRequest;
}

export interface RequestApprovalDialogResult {
  approved: true;
  requestId: string;
}

@Component({
  standalone: false,
  selector: 'app-request-approval-dialog',
  templateUrl: './request-approval-dialog.component.html',
  styleUrl: './request-approval-dialog.component.scss',
})
export class RequestApprovalDialogComponent implements OnInit {
  readonly scopes: AdminAssignmentScope[] = ['SELF', 'DESCENDANTS', 'GLOBAL'];

  organizationalUnits: PublicOrganizationalUnit[] = [];
  roles: AdminRole[] = [];
  unitId = '';
  roleCode = '';
  system: AdminSystem | null = null;
  scope: AdminAssignmentScope = 'SELF';
  fiscalYear: GestionHabilitada | null;
  loading = false;
  saving = false;
  catalogError = '';
  approvalError = '';

  constructor(
    @Inject(MAT_DIALOG_DATA) public readonly data: RequestApprovalDialogData,
    private readonly dialogRef: MatDialogRef<
      RequestApprovalDialogComponent,
      RequestApprovalDialogResult
    >,
    private readonly adminUsers: AdminUsuariosService,
    private readonly auth: AuthService,
    fiscalManagement: GestionHabilitadaService,
  ) {
    this.unitId = data.request.unidad_solicitada?.id ?? '';
    this.fiscalYear = fiscalManagement.gestion();
  }

  ngOnInit(): void {
    this.loadCatalogs();
  }

  get selectedRole(): AdminRole | undefined {
    return this.roles.find(role => role.codigo === this.roleCode);
  }

  get availableSystems(): AdminSystem[] {
    return this.businessSystems(this.selectedRole);
  }

  get fixedScope(): AdminAssignmentScope | null {
    return fixedScopeForRole(this.roleCode);
  }

  get showSystemSelector(): boolean {
    return this.availableSystems.length > 1;
  }

  get showScopeSelector(): boolean {
    return this.fixedScope === null;
  }

  get canApprove(): boolean {
    return Boolean(
      !this.loading
      && !this.catalogError
      && this.unitId
      && this.roleCode
      && this.system,
    );
  }

  loadCatalogs(): void {
    this.loading = true;
    this.catalogError = '';
    forkJoin({
      roles: this.adminUsers.listRoles(),
      units: this.auth.listPublicOrganizationalUnits(),
    }).subscribe({
      next: ({ roles, units }) => {
        this.roles = roles.filter(role => this.businessSystems(role).length > 0);
        this.organizationalUnits = this.includeRequestedUnit(units);
        if (!this.unitId) {
          this.unitId = this.organizationalUnits[0]?.id ?? '';
        }
        if (!this.roleCode) {
          this.roleCode = this.roles[0]?.codigo ?? '';
        }
        this.roleChanged();
        if (!this.roles.length || !this.organizationalUnits.length) {
          this.catalogError = 'Se necesita al menos un rol permitido y una unidad organizacional disponible.';
        }
        this.loading = false;
      },
      error: error => {
        this.catalogError = adminApiErrorMessage(
          error,
          'No se pudieron cargar los roles o las unidades organizacionales.',
        );
        this.loading = false;
      },
    });
  }

  roleChanged(): void {
    const systems = this.availableSystems;
    if (!this.system || !systems.includes(this.system)) {
      this.system = systems[0] ?? null;
    }
    this.scope = this.fixedScope ?? 'SELF';
    this.approvalError = '';
  }

  systemChanged(): void {
    this.approvalError = '';
  }

  scopeLabel(scope: AdminAssignmentScope): string {
    const labels: Record<AdminAssignmentScope, string> = {
      SELF: 'Solo esta unidad',
      DESCENDANTS: 'Unidad y dependencias',
      GLOBAL: 'Toda la organización',
    };
    return labels[scope];
  }

  systemLabel(system: AdminSystem): string {
    return system === 'sis_pe' ? 'SIS-PE' : 'SIS-POA';
  }

  approvalPayload(): AdminApprovalPayload {
    return {
      unidad_organizacional_id: this.unitId,
      rol_codigo: this.roleCode,
      scope_type: this.fixedScope ?? this.scope,
      sistema: this.system as AdminSystem,
      fiscal_year_id: this.system === 'sis_poa'
        ? this.fiscalYear?.id ?? null
        : null,
    };
  }

  approve(): void {
    if (!this.canApprove || this.saving) {
      return;
    }
    this.saving = true;
    this.approvalError = '';
    this.adminUsers.approveRequest(
      this.data.request.id,
      this.approvalPayload(),
    ).subscribe({
      next: () => this.dialogRef.close({
        approved: true,
        requestId: this.data.request.id,
      }),
      error: error => {
        this.approvalError = adminApiErrorMessage(
          error,
          'No se pudo aprobar la solicitud. Revise los datos seleccionados.',
        );
        this.saving = false;
      },
    });
  }

  close(): void {
    if (!this.saving) {
      this.dialogRef.close();
    }
  }

  fullName(): string {
    const request = this.data.request;
    return `${request.first_name} ${request.last_name}`.trim() || request.email;
  }

  private businessSystems(role?: AdminRole): AdminSystem[] {
    if (!role) {
      return [];
    }
    return role.sistemas.filter(
      (system): system is AdminSystem => system === 'sis_pe' || system === 'sis_poa',
    );
  }

  private includeRequestedUnit(
    units: PublicOrganizationalUnit[],
  ): PublicOrganizationalUnit[] {
    const requested = this.data.request.unidad_solicitada;
    if (!requested || units.some(unit => unit.id === requested.id)) {
      return [...units];
    }
    return [{
      id: requested.id,
      codigo: '',
      nombre: requested.nombre,
      sigla: '',
      padre: null,
    }, ...units];
  }
}
