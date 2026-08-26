import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { AdminUsuariosModule } from './admin-usuarios.module';
import {
  AdminRole,
  AdminUser,
  AdminUsuariosService,
} from './admin-usuarios.service';
import {
  UsuarioEdicionDialogComponent,
  UsuarioEdicionDialogData,
} from './usuario-edicion-dialog.component';

describe('UsuarioEdicionDialogComponent', () => {
  let fixture: ComponentFixture<UsuarioEdicionDialogComponent>;
  let component: UsuarioEdicionDialogComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let fiscalManagement: jasmine.SpyObj<GestionHabilitadaService>;
  let dialogRef: jasmine.SpyObj<MatDialogRef<UsuarioEdicionDialogComponent>>;
  let data: UsuarioEdicionDialogData;

  const unit: PublicOrganizationalUnit = {
    id: 'unit-1',
    codigo: 'DPL',
    nombre: 'Dirección de Planificación',
    sigla: 'DPL',
    padre: null,
  };

  const otherUnit: PublicOrganizationalUnit = {
    id: 'unit-2',
    codigo: 'SMF',
    nombre: 'Secretaría Municipal Financiera',
    sigla: 'SMF',
    padre: null,
  };

  const roles: AdminRole[] = [
    {
      id: 'role-base',
      codigo: 'JEFE_PE',
      nombre: 'Jefatura PE',
      descripcion: '',
      activo: true,
      es_sistema: true,
      deprecated: false,
      orden: 1,
      sistemas: ['sis_pe'],
      capacidades: [],
    },
    {
      id: 'role-custom',
      codigo: 'CUSTOM_POA',
      nombre: 'Rol personalizado POA',
      descripcion: '',
      activo: true,
      es_sistema: false,
      deprecated: false,
      orden: 2,
      sistemas: ['sis_poa'],
      capacidades: [],
    },
  ];

  const user: AdminUser = {
    id: 'user-1',
    first_name: 'Ana',
    last_name: 'Planificadora',
    email: 'ana@gob.bo',
    cargo: 'Especialista',
    telefono: '4455667',
    estado: 'ACTIVO',
    activo: true,
    is_active: true,
    last_login: null,
    roles: [],
    alcances: [
      {
        rol: 'JEFE_PE',
        unidad: { id: unit.id, codigo: unit.codigo, nombre: unit.nombre },
        scope_type: 'SELF',
        fiscal_year: null,
      },
      {
        rol: 'CUSTOM_POA',
        unidad: { id: unit.id, codigo: unit.codigo, nombre: unit.nombre },
        scope_type: 'DESCENDANTS',
        fiscal_year: null,
      },
    ],
    sistemas: ['sis_pe', 'sis_poa'],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService',
      ['getAssignments', 'listRoles', 'patchUser', 'putAssignments'],
    );
    fiscalManagement = jasmine.createSpyObj<GestionHabilitadaService>(
      'GestionHabilitadaService',
      ['gestion'],
    );
    dialogRef = jasmine.createSpyObj<MatDialogRef<UsuarioEdicionDialogComponent>>(
      'MatDialogRef',
      ['close'],
    );
    data = {
      user: { ...user, alcances: user.alcances.map(scope => ({ ...scope })) },
      organizationalUnits: [unit],
      canEditPersonal: true,
      canViewAssignments: true,
      canAssign: true,
      canViewRequests: true,
    };
    adminUsers.getAssignments.and.returnValue(of(data.user));
    adminUsers.listRoles.and.returnValue(of(roles));
    adminUsers.patchUser.and.returnValue(of(data.user));
    adminUsers.putAssignments.and.returnValue(of(data.user));
    fiscalManagement.gestion.and.returnValue(null);

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useFactory: () => data },
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: AdminUsuariosService, useValue: adminUsers },
        { provide: GestionHabilitadaService, useValue: fiscalManagement },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UsuarioEdicionDialogComponent);
    component = fixture.componentInstance;
  });

  it('fixes base-role scope and leaves custom scope editable', () => {
    fixture.detectChanges();

    const base = component.rows.find(row => row.role_code === 'JEFE_PE');
    const custom = component.rows.find(row => row.role_code === 'CUSTOM_POA');
    expect(base?.scope_type).toBe('GLOBAL');
    expect(component.fixedScope('JEFE_PE')).toBe('GLOBAL');
    expect(component.fixedScope('CUSTOM_POA')).toBeNull();

    if (custom) {
      custom.scope_type = 'SELF';
      component.roleChanged(custom);
      expect(custom.scope_type).toBe('SELF');
    }
  });

  it('adds and removes local rows and derives the system from the selected role', () => {
    fixture.detectChanges();
    const initialLength = component.rows.length;

    component.addAssignment();
    const added = component.rows[component.rows.length - 1];
    added.role_code = 'CUSTOM_POA';
    component.roleChanged(added);

    expect(component.rows.length).toBe(initialLength + 1);
    expect(component.systemsForRole(added.role_code)).toBe('SIS-POA');

    component.removeAssignment(added);
    expect(component.rows.length).toBe(initialLength);
  });

  it('filters organizational units by normalized, case-insensitive name input', () => {
    component.organizationalUnits.push(otherUnit);
    fixture.detectChanges();
    const row = component.rows[0];
    const input = fixture.nativeElement.querySelector(
      '.assignment-row input[matInput]',
    ) as HTMLInputElement;

    input.value = '  secretaría   MUNICIPAL ';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(component.filteredOrganizationalUnits(row)).toEqual([otherUnit]);
    expect(row.organizational_unit_id).toBe('');
  });

  it('displays the selected organizational unit and preserves its ID in the PUT payload', () => {
    component.organizationalUnits.push(otherUnit);
    fixture.detectChanges();
    const row = component.rows[0];

    component.selectOrganizationalUnit(row, otherUnit);
    expect(component.displayOrganizationalUnit(component.organizationalUnitQueries[row.localId]))
      .toBe('SMF · Secretaría Municipal Financiera');
    expect(row.organizational_unit_id).toBe(otherUnit.id);

    component.saveAssignments();

    expect(adminUsers.putAssignments.calls.mostRecent().args[1].assignments[0])
      .toEqual(jasmine.objectContaining({ organizational_unit_id: otherUnit.id }));
  });

  it('does not load or edit assignments for a pending user', () => {
    component.currentUser = { ...user, estado: 'PENDIENTE' };
    adminUsers.getAssignments.calls.reset();
    adminUsers.listRoles.calls.reset();

    fixture.detectChanges();

    expect(adminUsers.getAssignments).not.toHaveBeenCalled();
    expect(adminUsers.listRoles).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('La cuenta todavía está pendiente');
    component.goToRequests();
    expect(dialogRef.close).toHaveBeenCalledWith({
      navigateToRequests: true,
    });
  });

  it('keeps assignment rows and the dialog open when the atomic PUT fails', () => {
    fixture.detectChanges();
    const custom = component.rows.find(row => row.role_code === 'CUSTOM_POA');
    if (custom) {
      custom.scope_type = 'GLOBAL';
    }
    const localRows = component.rows.map(row => ({ ...row }));
    adminUsers.putAssignments.and.returnValue(throwError(() => new Error('invalid')));

    component.saveAssignments();
    fixture.detectChanges();

    expect(component.rows).toEqual(localRows);
    expect(component.assignmentsError).toContain('No se actualizaron las asignaciones');
    expect(fixture.nativeElement.querySelectorAll('.assignment-row').length).toBe(2);
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('shows but excludes assignments for roles outside the backend catalog', () => {
    adminUsers.listRoles.and.returnValue(of([roles[0]]));
    fixture.detectChanges();

    expect(component.preservedAssignments.map(scope => scope.rol)).toEqual(['CUSTOM_POA']);
    expect(component.rows.map(row => row.role_code)).toEqual(['JEFE_PE']);

    component.addAssignment();
    component.saveAssignments();
    const payload = adminUsers.putAssignments.calls.mostRecent().args[1];
    expect(payload.assignments.every(item => item.role_code === 'JEFE_PE')).toBeTrue();
  });

  it('sends a personal-only patch and emits the refreshed user', () => {
    fixture.detectChanges();
    const updated = { ...user, first_name: 'Ana María' };
    adminUsers.patchUser.and.returnValue(of(updated));
    const emitted: AdminUser[] = [];
    component.userSaved.subscribe(value => emitted.push(value));
    expect(component.personal.telefono).toBe('4455667');
    component.personal.first_name = 'Ana María';

    component.savePersonal();

    expect(adminUsers.patchUser).toHaveBeenCalledWith(user.id, {
      first_name: 'Ana María',
    });
    expect(adminUsers.patchUser.calls.mostRecent().args[1].telefono).toBeUndefined();
    expect(emitted[0].first_name).toBe('Ana María');
    expect(emitted[0].telefono).toBe('4455667');
    expect(component.personalSuccess).toContain('actualizados');
  });

  it('sends the phone only when its real value changes', () => {
    fixture.detectChanges();
    const updated = { ...user, telefono: '70000001' };
    adminUsers.patchUser.and.returnValue(of(updated));
    component.personal.telefono = '70000001';

    component.savePersonal();

    expect(adminUsers.patchUser).toHaveBeenCalledWith(user.id, {
      telefono: '70000001',
    });
    expect(component.currentUser.telefono).toBe('70000001');
    expect(component.personal.telefono).toBe('70000001');
  });

  it('hides or disables sections according to capabilities', () => {
    data.canEditPersonal = false;
    data.canAssign = false;
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).not.toContain('Datos personales');
    expect(fixture.nativeElement.textContent).toContain('Roles y alcances');
    expect(fixture.nativeElement.textContent).not.toContain('Guardar asignaciones');
  });
});
