import { Component, EventEmitter, Inject, OnInit, Output } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { forkJoin } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import {
  GestionHabilitada,
  GestionHabilitadaService,
} from '../../core/services/gestion-habilitada.service';
import {
  AdminAssignmentInput,
  AdminAssignmentScope,
  AdminRole,
  AdminUser,
  AdminUserPersonalPatch,
  AdminUserScope,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { fixedScopeForRole } from './admin-role-scope';

export interface UsuarioEdicionDialogData {
  user: AdminUser;
  organizationalUnits: PublicOrganizationalUnit[];
  canEditPersonal: boolean;
  canViewAssignments: boolean;
  canAssign: boolean;
  canViewRequests: boolean;
}

export interface UsuarioEdicionDialogResult {
  navigateToRequests?: boolean;
}

interface PersonalFormValue {
  first_name: string;
  last_name: string;
  cargo: string;
  telefono: string;
}

export interface AssignmentRow {
  localId: number;
  role_code: string;
  organizational_unit_id: string;
  scope_type: AdminAssignmentScope;
  fiscal_year_id: string | null;
}

@Component({
  standalone: false,
  selector: 'app-usuario-edicion-dialog',
  templateUrl: './usuario-edicion-dialog.component.html',
  styleUrl: './usuario-edicion-dialog.component.scss',
})
export class UsuarioEdicionDialogComponent implements OnInit {
  @Output() readonly userSaved = new EventEmitter<AdminUser>();

  readonly scopes: AdminAssignmentScope[] = ['SELF', 'DESCENDANTS', 'GLOBAL'];
  currentUser: AdminUser;
  personal: PersonalFormValue;
  roles: AdminRole[] = [];
  rows: AssignmentRow[] = [];
  preservedAssignments: AdminUserScope[] = [];
  organizationalUnits: PublicOrganizationalUnit[];
  fiscalYears: GestionHabilitada[] = [];
  loadingAssignments = false;
  savingPersonal = false;
  savingAssignments = false;
  personalError = '';
  personalSuccess = '';
  assignmentsLoadError = '';
  assignmentsError = '';
  assignmentsSuccess = '';
  fiscalCatalogError = '';

  private personalBaseline: PersonalFormValue;
  private assignmentsBaseline = '[]';
  private nextRowId = 1;

  constructor(
    @Inject(MAT_DIALOG_DATA) public readonly data: UsuarioEdicionDialogData,
    private readonly dialogRef: MatDialogRef<UsuarioEdicionDialogComponent, UsuarioEdicionDialogResult>,
    private readonly adminUsers: AdminUsuariosService,
    private readonly fiscalManagement: GestionHabilitadaService,
  ) {
    this.currentUser = data.user;
    this.personal = this.personalValue(data.user);
    this.personalBaseline = { ...this.personal };
    this.organizationalUnits = [...data.organizationalUnits];
  }

  ngOnInit(): void {
    if (this.data.canViewAssignments && !this.isPending) {
      this.loadAssignments();
      this.loadFiscalYears();
    }
  }

  get isPending(): boolean {
    return this.currentUser.estado === 'PENDIENTE';
  }

  get personalDirty(): boolean {
    return this.personal.first_name.trim() !== this.personalBaseline.first_name
      || this.personal.last_name.trim() !== this.personalBaseline.last_name
      || this.personal.cargo.trim() !== this.personalBaseline.cargo
      || this.personal.telefono.trim() !== this.personalBaseline.telefono;
  }

  get assignmentsDirty(): boolean {
    return this.data.canAssign
      && JSON.stringify(this.assignmentPayload()) !== this.assignmentsBaseline;
  }

  get showFiscalYearSelector(): boolean {
    return this.fiscalYears.length > 0;
  }

  loadAssignments(): void {
    this.loadingAssignments = true;
    this.assignmentsLoadError = '';
    this.assignmentsError = '';
    this.assignmentsSuccess = '';
    forkJoin({
      user: this.adminUsers.getAssignments(this.currentUser.id),
      roles: this.adminUsers.listRoles(),
    }).subscribe({
      next: ({ user, roles }) => {
        this.currentUser = user;
        this.roles = roles;
        this.initializeAssignments(user, roles);
        this.loadingAssignments = false;
      },
      error: () => {
        this.assignmentsLoadError = 'No se pudieron cargar los roles y alcances administrables. Revise sus permisos e inténtelo nuevamente.';
        this.loadingAssignments = false;
      },
    });
  }

  addAssignment(): void {
    if (!this.data.canAssign) {
      return;
    }
    const role = this.roles[0];
    const unit = this.organizationalUnits[0];
    if (!role || !unit) {
      this.assignmentsError = 'Se necesita al menos un rol y una unidad organizacional disponibles.';
      return;
    }
    this.rows = [...this.rows, {
      localId: this.nextRowId++,
      role_code: role.codigo,
      organizational_unit_id: unit.id,
      scope_type: this.fixedScope(role.codigo) ?? 'SELF',
      fiscal_year_id: null,
    }];
    this.assignmentsError = '';
    this.assignmentsSuccess = '';
  }

  removeAssignment(row: AssignmentRow): void {
    if (!this.data.canAssign) {
      return;
    }
    this.rows = this.rows.filter(item => item.localId !== row.localId);
    this.assignmentsSuccess = '';
  }

  roleChanged(row: AssignmentRow): void {
    const fixed = this.fixedScope(row.role_code);
    if (fixed) {
      row.scope_type = fixed;
    }
    this.assignmentsSuccess = '';
  }

  fixedScope(roleCode: string): AdminAssignmentScope | null {
    return fixedScopeForRole(roleCode);
  }

  scopeLabel(scope: AdminAssignmentScope): string {
    const labels: Record<AdminAssignmentScope, string> = {
      SELF: 'Solo esta unidad',
      DESCENDANTS: 'Unidad y dependencias',
      GLOBAL: 'Toda la organización',
    };
    return labels[scope];
  }

  systemsForRole(roleCode: string): string {
    const systems = this.roles.find(role => role.codigo === roleCode)?.sistemas ?? [];
    return systems.map(system => this.systemLabel(system)).join(' · ') || 'Sin sistema';
  }

  isUnknownFiscalYear(id: string | null): id is string {
    return Boolean(id) && !this.fiscalYears.some(year => year.id === id);
  }

  savePersonal(): void {
    if (!this.data.canEditPersonal || this.savingPersonal) {
      return;
    }
    this.personalError = '';
    this.personalSuccess = '';
    if (!this.personal.first_name.trim() || !this.personal.last_name.trim()) {
      this.personalError = 'Los nombres y apellidos son obligatorios.';
      return;
    }

    const patch = this.personalPatch();
    if (Object.keys(patch).length === 0) {
      this.personal = { ...this.personalBaseline };
      this.personalSuccess = 'No hay cambios en los datos personales.';
      return;
    }

    this.savingPersonal = true;
    this.adminUsers.patchUser(this.currentUser.id, patch).subscribe({
      next: updated => {
        this.currentUser = updated;
        this.personal = this.personalValue(updated);
        this.personalBaseline = { ...this.personal };
        this.personalSuccess = 'Datos personales actualizados.';
        this.savingPersonal = false;
        this.userSaved.emit(updated);
      },
      error: () => {
        this.personalError = 'No se pudieron guardar los datos personales. Los cambios permanecen en el formulario.';
        this.savingPersonal = false;
      },
    });
  }

  saveAssignments(): void {
    if (!this.data.canAssign || this.savingAssignments || this.isPending) {
      return;
    }
    this.assignmentsError = '';
    this.assignmentsSuccess = '';
    if (this.rows.some(row => !row.role_code || !row.organizational_unit_id)) {
      this.assignmentsError = 'Cada asignación debe tener rol y unidad organizacional.';
      return;
    }

    const assignments = this.assignmentPayload();
    this.savingAssignments = true;
    this.adminUsers.putAssignments(this.currentUser.id, { assignments }).subscribe({
      next: updated => {
        this.currentUser = updated;
        this.initializeAssignments(updated, this.roles);
        this.assignmentsSuccess = 'Asignaciones actualizadas de forma atómica.';
        this.savingAssignments = false;
        this.userSaved.emit(updated);
      },
      error: () => {
        this.assignmentsError = 'No se actualizaron las asignaciones. Revise combinaciones duplicadas, scopes y permisos; las filas locales se conservaron.';
        this.savingAssignments = false;
      },
    });
  }

  hasUnsavedChanges(): boolean {
    return this.personalDirty || this.assignmentsDirty;
  }

  confirmDiscard(): boolean {
    return window.confirm('Hay cambios sin guardar. ¿Desea descartarlos y cerrar?');
  }

  close(): void {
    this.dialogRef.close({});
  }

  goToRequests(): void {
    this.dialogRef.close({ navigateToRequests: true });
  }

  trackRow(_index: number, row: AssignmentRow): number {
    return row.localId;
  }

  private loadFiscalYears(): void {
    const current = this.fiscalManagement.gestion();
    this.fiscalYears = current ? [current] : [];
    this.fiscalCatalogError = current
      ? ''
      : 'No hay una gestión fiscal habilitada. Las filas nuevas se guardarán sin gestión y las existentes conservarán su valor.';
  }

  private initializeAssignments(user: AdminUser, roles: AdminRole[]): void {
    const editableCodes = new Set(roles.map(role => role.codigo));
    const editable = user.alcances.filter(scope => scope.rol && editableCodes.has(scope.rol));
    this.preservedAssignments = user.alcances.filter(
      scope => !scope.rol || !editableCodes.has(scope.rol),
    );
    this.includeAssignedUnits(user.alcances);
    this.rows = editable.map(scope => ({
      localId: this.nextRowId++,
      role_code: scope.rol as string,
      organizational_unit_id: scope.unidad.id,
      scope_type: this.fixedScope(scope.rol as string) ?? scope.scope_type,
      fiscal_year_id: scope.fiscal_year,
    }));
    this.assignmentsBaseline = JSON.stringify(this.assignmentPayload());
  }

  private includeAssignedUnits(scopes: AdminUserScope[]): void {
    const known = new Set(this.organizationalUnits.map(unit => unit.id));
    for (const scope of scopes) {
      if (!known.has(scope.unidad.id)) {
        this.organizationalUnits.push({
          id: scope.unidad.id,
          codigo: scope.unidad.codigo,
          nombre: scope.unidad.nombre,
          sigla: '',
          padre: null,
        });
        known.add(scope.unidad.id);
      }
    }
  }

  private assignmentPayload(): AdminAssignmentInput[] {
    return this.rows.map(row => ({
      role_code: row.role_code,
      organizational_unit_id: row.organizational_unit_id,
      scope_type: this.fixedScope(row.role_code) ?? row.scope_type,
      fiscal_year_id: row.fiscal_year_id,
    }));
  }

  private personalPatch(): AdminUserPersonalPatch {
    const patch: AdminUserPersonalPatch = {};
    const fields: Array<keyof Omit<PersonalFormValue, 'telefono'>> = [
      'first_name', 'last_name', 'cargo',
    ];
    for (const field of fields) {
      const value = this.personal[field].trim();
      if (value !== this.personalBaseline[field]) {
        patch[field] = value;
      }
    }
    const telefono = this.personal.telefono.trim();
    if (telefono !== this.personalBaseline.telefono) {
      patch.telefono = telefono;
    }
    return patch;
  }

  private personalValue(user: AdminUser): PersonalFormValue {
    return {
      first_name: user.first_name.trim(),
      last_name: user.last_name.trim(),
      cargo: user.cargo.trim(),
      telefono: user.telefono.trim(),
    };
  }

  private systemLabel(system: string): string {
    if (system === 'sis_pe') {
      return 'SIS-PE';
    }
    if (system === 'sis_poa') {
      return 'SIS-POA';
    }
    return system === 'accounts' ? 'CORE' : system.toUpperCase();
  }
}
