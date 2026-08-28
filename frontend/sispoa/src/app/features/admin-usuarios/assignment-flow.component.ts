import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ModuleMetadata, MODULES_CONFIG, ModuleSystem } from '../../core/config/modules.config';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { GestionHabilitada } from '../../core/services/gestion-habilitada.service';
import {
  AdminAccessPreviewResponse, AdminAssignmentInput, AdminAssignmentScope, AdminCapability, AdminRole,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { fixedScopeForRole } from './admin-role-scope';

@Component({
  selector: 'app-assignment-flow',
  standalone: false,
  templateUrl: './assignment-flow.component.html',
  styles: [`
    :host { display: block; }
    .flow-grid { display: grid; gap: var(--e-2); }
    .flow-capabilities { margin: 0; padding-left: 1.25rem; }
    .flow-capabilities-note { color: var(--pip-ink-soft); margin: 0 0 var(--e-2); }
    .flow-actions { display: flex; flex-wrap: wrap; gap: var(--e-2); justify-content: flex-end; }
    .flow-error { color: var(--error-tinta); }
    @media (prefers-reduced-motion: reduce) { :host { scroll-behavior: auto; } }
  `],
})
export class AssignmentFlowComponent {
  @Input() userId = '';
  @Input() roles: AdminRole[] = [];
  @Input() organizationalUnits: PublicOrganizationalUnit[] = [];
  @Input() fiscalYears: GestionHabilitada[] = [];
  @Output() readonly saveRequested = new EventEmitter<AdminAssignmentInput>();

  readonly systems: ModuleSystem[] = ['sis_pe', 'sis_poa'];
  readonly scopes: AdminAssignmentScope[] = ['SELF', 'DESCENDANTS', 'GLOBAL'];
  selectedSystem: ModuleSystem | '' = '';
  selectedModule: ModuleMetadata | null = null;
  selectedRoleCode = '';
  selectedUnitId = '';
  selectedScope: AdminAssignmentScope = 'SELF';
  selectedFiscalYearId: string | null = null;
  unitQuery = '';
  previewResult: AdminAccessPreviewResponse | null = null;
  loadingPreview = false;
  error = '';

  constructor(private readonly adminUsers: AdminUsuariosService) {}

  get modules(): readonly ModuleMetadata[] {
    return MODULES_CONFIG.filter(module => module.sistema === this.selectedSystem);
  }

  get compatibleRoles(): AdminRole[] {
    if (!this.selectedModule) { return []; }
    return this.roles.filter(role => role.sistemas.includes(this.selectedModule!.sistema)
      && role.capacidades.some(capability => this.selectedModule!.capacidades.includes(capability.codigo)));
  }

  get selectedRole(): AdminRole | undefined {
    return this.compatibleRoles.find(role => role.codigo === this.selectedRoleCode);
  }

  get effectiveRoleCapabilities(): AdminCapability[] {
    if (!this.selectedModule || !this.selectedRole) { return []; }
    return this.selectedRole.capacidades.filter(capability =>
      this.selectedModule!.capacidades.includes(capability.codigo));
  }

  get fixedScope(): AdminAssignmentScope | null {
    return fixedScopeForRole(this.selectedRoleCode);
  }

  get requiresFiscalYear(): boolean {
    return this.selectedRole?.capacidades.some(capability =>
      capability.codigo.startsWith('sis_poa.')) ?? false;
  }

  get canSubmit(): boolean { return this.buildAssignment() !== null; }

  get filteredUnits(): PublicOrganizationalUnit[] {
    const query = this.normalize(this.unitQuery);
    return query ? this.organizationalUnits.filter(unit =>
      this.normalize(`${unit.nombre} ${unit.sigla} ${unit.codigo}`).includes(query))
      : this.organizationalUnits;
  }

  selectSystem(system: ModuleSystem): void {
    this.selectedSystem = system;
    this.selectedModule = null;
    this.selectedRoleCode = '';
    this.selectedScope = 'SELF';
    this.selectedFiscalYearId = null;
    this.previewResult = null;
  }

  selectModule(module: ModuleMetadata): void {
    this.selectedModule = module;
    this.selectedRoleCode = '';
    this.selectedScope = 'SELF';
    this.selectedFiscalYearId = null;
    this.previewResult = null;
    this.error = '';
  }

  selectRole(roleCode: string): void {
    const role = this.compatibleRoles.find(item => item.codigo === roleCode);
    this.selectedRoleCode = role?.codigo ?? '';
    this.selectedScope = fixedScopeForRole(this.selectedRoleCode) ?? 'SELF';
    if (!this.requiresFiscalYear) { this.selectedFiscalYearId = null; }
    this.previewResult = null;
    this.error = '';
  }

  searchUnits(value: string): void { this.unitQuery = value; this.selectedUnitId = ''; }

  selectOrganizationalUnit(unit: PublicOrganizationalUnit): void {
    this.selectedUnitId = unit.id;
    this.unitQuery = `${unit.codigo} · ${unit.nombre}`;
    this.error = '';
  }

  buildAssignment(): AdminAssignmentInput | null {
    const role = this.selectedRole;
    if (!role || !this.selectedModule || !this.selectedUnitId
      || (this.requiresFiscalYear && !this.selectedFiscalYearId)) {
      return null;
    }
    return {
      role_code: role.codigo,
      organizational_unit_id: this.selectedUnitId,
      scope_type: this.selectedScope,
      fiscal_year_id: this.requiresFiscalYear ? this.selectedFiscalYearId : null,
    };
  }

  preview(): void {
    const assignment = this.buildAssignment();
    if (!assignment) { this.error = 'Seleccione un rol compatible y complete módulo, unidad y gestión aplicable antes de previsualizar.'; return; }
    this.loadingPreview = true;
    this.error = '';
    this.adminUsers.previewAccess({ user_id: this.userId, assignments: [assignment] }).subscribe({
      next: result => { this.previewResult = result; this.loadingPreview = false; },
      error: () => { this.error = 'No se pudo generar la vista previa.'; this.loadingPreview = false; },
    });
  }

  save(): void {
    const assignment = this.buildAssignment();
    if (!assignment) { this.error = 'Seleccione un rol compatible y complete los pasos requeridos antes de guardar.'; return; }
    this.saveRequested.emit(assignment);
  }

  systemLabel(system: ModuleSystem): string { return system === 'sis_pe' ? 'SIS-PE' : 'SIS-POA'; }

  private normalize(value: string): string {
    return value.trim().replace(/\s+/g, ' ').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
}
