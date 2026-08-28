import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, Subject, throwError } from 'rxjs';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { AdminCapability, AdminRole, AdminUsuariosService } from './admin-usuarios.service';
import { RolesAdminTabComponent } from './roles-admin-tab.component';

describe('RolesAdminTabComponent', () => {
  let fixture: ComponentFixture<RolesAdminTabComponent>;
  let component: RolesAdminTabComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let capabilities: jasmine.SpyObj<CapabilitiesService>;
  let dialog: jasmine.SpyObj<MatDialog>;
  let granted: Set<string>;

  const capability: AdminCapability = {
    id: 'cap-1',
    codigo: 'sis_pe.pad.view',
    nombre: 'Ver PAD',
    descripcion: 'Consulta del PAD',
    sistema: 'sis_pe',
    activo: true,
    orden: 1,
  };
  const systemRole: AdminRole = {
    id: 'role-system',
    codigo: 'JEFE_PE',
    nombre: 'Jefatura PE',
    descripcion: 'Rol base',
    activo: true,
    es_sistema: true,
    deprecated: false,
    orden: 1,
    sistemas: ['sis_pe'],
    capacidades: [capability],
  };
  const customRole: AdminRole = {
    ...systemRole,
    id: 'role-custom',
    codigo: 'CUSTOM_PE',
    nombre: 'Rol personalizado PE',
    es_sistema: false,
    orden: 2,
  };
  const page = {
    count: 2,
    next: null,
    previous: null,
    results: [systemRole, customRole],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService', ['listRolesPage', 'deleteRole'],
    );
    capabilities = jasmine.createSpyObj<CapabilitiesService>('CapabilitiesService', ['tiene']);
    dialog = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    granted = new Set();
    capabilities.tiene.and.callFake(code => granted.has(code));
    adminUsers.listRolesPage.and.returnValue(of(page));
    adminUsers.deleteRole.and.returnValue(of(void 0));
    dialog.open.and.returnValue({
      afterClosed: () => of(undefined),
    } as unknown as MatDialogRef<unknown>);

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: AdminUsuariosService, useValue: adminUsers },
        { provide: CapabilitiesService, useValue: capabilities },
        { provide: MatDialog, useValue: dialog },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RolesAdminTabComponent);
    component = fixture.componentInstance;
  });

  it('renders all lifecycle actions for system and custom roles when authorized', () => {
    granted.add('accounts.rol.edit');
    granted.add('accounts.capacidad.assign');
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('JEFE_PE');
    expect(text).toContain('CUSTOM_PE');
    expect(text).toContain('Sistema');
    expect(text).toContain('Personalizado');
    expect(fixture.nativeElement.querySelector('[aria-label="Editar rol JEFE_PE"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Asignar permisos a JEFE_PE"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Eliminar rol JEFE_PE"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Editar rol CUSTOM_PE"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Asignar permisos a CUSTOM_PE"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Eliminar rol CUSTOM_PE"]')).not.toBeNull();
  });

  it('passes a system role to the existing edit and capability dialogs', () => {
    granted.add('accounts.rol.edit');
    granted.add('accounts.capacidad.assign');
    fixture.detectChanges();

    component.openEdit(systemRole);
    component.openCapabilities(systemRole);

    expect(dialog.open.calls.argsFor(0)[1]?.data).toEqual({ mode: 'edit', role: systemRole });
    expect(dialog.open.calls.argsFor(1)[1]?.data).toEqual({ role: systemRole });
  });

  it('deletes after confirmation and refreshes the current role page', () => {
    granted.add('accounts.rol.edit');
    spyOn(window, 'confirm').and.returnValue(true);
    fixture.detectChanges();
    adminUsers.listRolesPage.calls.reset();

    component.deleteRole(systemRole);

    expect(adminUsers.deleteRole).toHaveBeenCalledOnceWith(systemRole.id);
    expect(adminUsers.listRolesPage).toHaveBeenCalledOnceWith(component.filters, 1);
  });

  it('does nothing when role deletion is cancelled', () => {
    granted.add('accounts.rol.edit');
    spyOn(window, 'confirm').and.returnValue(false);
    fixture.detectChanges();

    component.deleteRole(systemRole);

    expect(adminUsers.deleteRole).not.toHaveBeenCalled();
  });

  it('surfaces an assigned-role conflict from the backend', () => {
    granted.add('accounts.rol.edit');
    spyOn(window, 'confirm').and.returnValue(true);
    adminUsers.deleteRole.and.returnValue(throwError(() => ({
      status: 409,
      error: { code: 'role_in_use', error: 'Retire primero las asignaciones del rol.' },
    })));
    fixture.detectChanges();

    component.deleteRole(systemRole);
    fixture.detectChanges();

    expect(component.actionError).toContain('Retire primero las asignaciones');
    expect(fixture.nativeElement.textContent).toContain('Retire primero las asignaciones');
  });

  it('sends role filters and the selected backend page', () => {
    fixture.detectChanges();
    adminUsers.listRolesPage.calls.reset();
    component.filters = { search: 'custom', system: 'accounts', active: false };
    component.pageIndex = 3;

    component.applyFilters();
    expect(adminUsers.listRolesPage).toHaveBeenCalledOnceWith(component.filters, 1);

    component.changePage({ pageIndex: 2, previousPageIndex: 1, pageSize: 25, length: 80 });
    expect(adminUsers.listRolesPage).toHaveBeenCalledWith(component.filters, 3);
  });

  it('shows loading, empty and actionable error states', () => {
    const pending = new Subject<typeof page>();
    adminUsers.listRolesPage.and.returnValue(pending.asObservable());
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Cargando roles');

    adminUsers.listRolesPage.and.returnValue(throwError(() => new Error('network')));
    component.loadRoles();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No pudimos consultar los roles');

    adminUsers.listRolesPage.and.returnValue(of({ ...page, count: 0, results: [] }));
    component.loadRoles();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay roles para mostrar');
  });

  it('shows create from capability and refreshes after a successful dialog result', () => {
    granted.add('accounts.rol.create');
    dialog.open.and.returnValue({
      afterClosed: () => of(customRole),
    } as unknown as MatDialogRef<unknown>);
    fixture.detectChanges();
    adminUsers.listRolesPage.calls.reset();

    expect(fixture.nativeElement.textContent).toContain('Crear rol personalizado');
    component.openCreate();

    expect(dialog.open).toHaveBeenCalled();
    expect(adminUsers.listRolesPage).toHaveBeenCalledOnceWith(component.filters, 1);
  });
});
