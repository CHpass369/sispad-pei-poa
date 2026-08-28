import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { MODULES_CONFIG } from '../../core/config/modules.config';
import {
  AdminCapability,
  AdminRole,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { AssignmentFlowComponent } from './assignment-flow.component';

describe('AssignmentFlowComponent', () => {
  let fixture: ComponentFixture<AssignmentFlowComponent>;
  let component: AssignmentFlowComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;

  const capability = (code: string): AdminCapability => ({
    id: `cap-${code}`,
    codigo: code,
    nombre: code,
    descripcion: '',
    sistema: code.split('.')[0],
    activo: true,
    orden: 1,
  });

  const role = (
    code: string,
    systems: string[],
    capabilityCodes: string[],
  ): AdminRole => ({
    id: `role-${code}`,
    codigo: code,
    nombre: code,
    descripcion: '',
    activo: true,
    es_sistema: true,
    deprecated: false,
    orden: 1,
    sistemas: systems,
    capacidades: capabilityCodes.map(capability),
  });

  const selectRole = (code: string): void => {
    (component as unknown as { selectRole(roleCode: string): void }).selectRole(code);
  };

  const selectPoau = (): void => {
    component.selectSystem('sis_poa');
    component.selectModule(MODULES_CONFIG.find(module => module.codigo === 'poau')!);
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj('AdminUsuariosService', ['previewAccess']);
    adminUsers.previewAccess.and.returnValue(of({
      capabilities: [{ codigo: 'sis_poa.poau.view', nombre: 'Ver POAU', sistema: 'sis_poa', modulo: 'poau' }],
      effective_uos: [{ id: 'unit-1', codigo: 'DPL', nombre: 'Dirección de Planificación' }],
      modules: [{ codigo: 'poau', sistema: 'sis_poa', visible: true }],
    }));
    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [{ provide: AdminUsuariosService, useValue: adminUsers }],
    }).compileComponents();
    fixture = TestBed.createComponent(AssignmentFlowComponent);
    component = fixture.componentInstance;
    component.userId = 'user-1';
    component.roles = [
      role('SUPER_ADMIN', ['sis_pe', 'sis_poa'], ['sis_poa.poau.view', 'sis_pe.instrumento.read']),
      role('FORMULADOR_POAU', ['sis_poa'], ['sis_poa.poau.view', 'sis_poa.poau.edit']),
      role('ANALISTA_PE', ['sis_pe'], ['sis_pe.instrumento.read']),
    ];
    component.organizationalUnits = [{ id: 'unit-1', codigo: 'DPL', nombre: 'Dirección de Planificación', sigla: 'DPL', padre: null }];
    component.fiscalYears = [{ id: 'year-2026', anio: 2026, estado: 'A', estado_display: 'Abierta', fecha_apertura: null, fecha_cierre: null }];
  });

  it('never auto-selects a role even when SUPER_ADMIN is listed first', () => {
    component.selectSystem('sis_poa');
    expect(component.selectedRoleCode).toBe('');

    component.selectModule(MODULES_CONFIG.find(module => module.codigo === 'poau')!);
    expect(component.selectedRoleCode).toBe('');
  });

  it('blocks preview and save until an explicit compatible role is chosen', () => {
    selectPoau();
    component.selectOrganizationalUnit(component.organizationalUnits[0]);
    component.selectedFiscalYearId = 'year-2026';
    const emit = spyOn(component.saveRequested, 'emit');

    component.preview();
    component.save();

    expect(adminUsers.previewAccess).not.toHaveBeenCalled();
    expect(emit).not.toHaveBeenCalled();
    expect(component.error).toContain('rol');
  });

  it('synchronizes the SUPER_ADMIN fixed scope to GLOBAL on explicit selection', () => {
    selectPoau();

    selectRole('SUPER_ADMIN');
    component.selectOrganizationalUnit(component.organizationalUnits[0]);
    component.selectedFiscalYearId = 'year-2026';

    expect(component.selectedRoleCode).toBe('SUPER_ADMIN');
    expect(component.selectedScope).toBe('GLOBAL');
    expect(component.buildAssignment()).toEqual(jasmine.objectContaining({
      role_code: 'SUPER_ADMIN', scope_type: 'GLOBAL', fiscal_year_id: 'year-2026',
    }));
  });

  it('submits the explicitly selected role in preview and save payloads', () => {
    selectPoau();
    selectRole('FORMULADOR_POAU');
    component.selectOrganizationalUnit(component.organizationalUnits[0]);
    component.selectedFiscalYearId = 'year-2026';
    const emit = spyOn(component.saveRequested, 'emit');

    component.preview();
    component.save();

    expect(component.buildAssignment()).toEqual({
      role_code: 'FORMULADOR_POAU', organizational_unit_id: 'unit-1',
      scope_type: 'SELF', fiscal_year_id: 'year-2026',
    });
    expect(adminUsers.previewAccess).toHaveBeenCalledWith(jasmine.objectContaining({
      user_id: 'user-1', assignments: [jasmine.objectContaining({ role_code: 'FORMULADOR_POAU' })],
    }));
    expect(emit).toHaveBeenCalledWith(jasmine.objectContaining({ role_code: 'FORMULADOR_POAU' }));
    expect(component.previewResult?.effective_uos[0].id).toBe('unit-1');
  });

  it('requires year only for POA and keeps PE assignments yearless', () => {
    selectPoau();
    selectRole('FORMULADOR_POAU');
    component.selectOrganizationalUnit(component.organizationalUnits[0]);
    expect(component.buildAssignment()).toBeNull();
    component.selectSystem('sis_pe');
    component.selectModule(MODULES_CONFIG.find(module => module.sistema === 'sis_pe')!);
    selectRole('ANALISTA_PE');
    expect(component.buildAssignment()?.fiscal_year_id).toBeNull();
  });

  it('presents role capabilities as derived read-only information, not a persisted subset', () => {
    selectPoau();
    component.selectedRoleCode = 'FORMULADOR_POAU';
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelectorAll('mat-checkbox').length).toBe(0);
    expect(fixture.nativeElement.textContent).toContain('Capacidades efectivas del rol');
    expect(fixture.nativeElement.textContent).toContain('solo se envía el rol completo');
  });
});
