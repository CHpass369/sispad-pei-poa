import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, Subject, throwError } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { AdminUser, AdminUsuariosService } from './admin-usuarios.service';
import { UsuariosListaComponent } from './usuarios-lista.component';
import { UsuarioEdicionDialogComponent } from './usuario-edicion-dialog.component';
import { RequestsAdminTabComponent } from './requests-admin-tab.component';

describe('UsuariosListaComponent', () => {
  let component: UsuariosListaComponent;
  let fixture: ComponentFixture<UsuariosListaComponent>;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let auth: jasmine.SpyObj<AuthService>;
  let capabilities: jasmine.SpyObj<CapabilitiesService>;
  let matDialog: jasmine.SpyObj<MatDialog>;
  let granted: Set<string>;

  const unit: PublicOrganizationalUnit = {
    id: 'unit-1',
    codigo: 'DPL',
    nombre: 'Dirección de Planificación',
    sigla: 'DPL',
    padre: null,
  };

  const activeUser: AdminUser = {
    id: 'user-1',
    first_name: 'Ana',
    last_name: 'Planificadora',
    email: 'ana@gob.bo',
    cargo: 'Especialista estratégica',
    telefono: '4455667',
    estado: 'ACTIVO',
    activo: true,
    is_active: true,
    last_login: '2026-08-24T10:30:00Z',
    roles: [{ codigo: 'ANALISTA_PE', nombre: 'Analista PE', sistemas: ['sis_pe'] }],
    alcances: [{
      rol: 'ANALISTA_PE',
      unidad: { id: unit.id, codigo: unit.codigo, nombre: unit.nombre },
      scope_type: 'DESCENDANTS',
      fiscal_year: null,
    }],
    sistemas: ['sis_pe'],
  };

  const inactiveUser: AdminUser = {
    ...activeUser,
    id: 'user-2',
    first_name: 'Boris',
    last_name: 'Operativo',
    email: 'boris@gob.bo',
    cargo: 'Analista POA',
    estado: 'INACTIVO',
    activo: false,
    is_active: false,
    last_login: null,
    roles: [{ codigo: 'ANALISTA_POA', nombre: 'Analista POA', sistemas: ['sis_poa'] }],
    sistemas: ['sis_poa'],
  };

  const page = {
    count: 2,
    next: null,
    previous: null,
    results: [activeUser, inactiveUser],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService',
      [
        'listUsers', 'getUser', 'activate', 'deactivate', 'listRolesPage',
        'listCapabilities', 'listRequests',
      ],
    );
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['listPublicOrganizationalUnits']);
    capabilities = jasmine.createSpyObj<CapabilitiesService>('CapabilitiesService', ['tiene']);
    matDialog = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    granted = new Set(['accounts.usuario.view']);
    capabilities.tiene.and.callFake(code => granted.has(code));
    adminUsers.listUsers.and.returnValue(of(page));
    adminUsers.listRolesPage.and.returnValue(of({
      count: 0, next: null, previous: null, results: [],
    }));
    adminUsers.listCapabilities.and.returnValue(of({
      count: 0, next: null, previous: null, results: [],
    }));
    adminUsers.listRequests.and.returnValue(of({
      count: 0, next: null, previous: null, results: [],
    }));
    adminUsers.getUser.and.returnValue(of(activeUser));
    adminUsers.activate.and.returnValue(of({
      ...inactiveUser,
      estado: 'ACTIVO',
      activo: true,
      is_active: true,
    }));
    adminUsers.deactivate.and.returnValue(of({
      ...activeUser,
      estado: 'INACTIVO',
      activo: false,
      is_active: false,
    }));
    auth.listPublicOrganizationalUnits.and.returnValue(of([unit]));

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: AdminUsuariosService, useValue: adminUsers },
        { provide: AuthService, useValue: auth },
        { provide: CapabilitiesService, useValue: capabilities },
        { provide: MatDialog, useValue: matDialog },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UsuariosListaComponent);
    component = fixture.componentInstance;
  });

  it('renders the required columns and backend data', () => {
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    for (const heading of [
      'Usuario', 'Cargo', 'Unidad organizacional', 'Rol', 'Sistema',
      'Estado', 'Último acceso', 'Acciones',
    ]) {
      expect(text).toContain(heading);
    }
    expect(text).toContain('Ana Planificadora');
    expect(text).toContain('Dirección de Planificación');
    expect(text).toContain('Analista PE');
    expect(text).toContain('SIS-POA');
  });

  it('sends filters and resets the backend page', () => {
    fixture.detectChanges();
    adminUsers.listUsers.calls.reset();
    component.pageIndex = 3;
    component.filters = {
      search: 'Ana',
      organizational_unit: unit.id,
      role: 'ANALISTA_PE',
      system: 'sis_pe',
      state: 'ACTIVO',
    };

    component.applyFilters();

    expect(component.pageIndex).toBe(0);
    expect(adminUsers.listUsers).toHaveBeenCalledOnceWith(component.filters, 1);
  });

  it('requests the selected backend page', () => {
    fixture.detectChanges();
    adminUsers.listUsers.calls.reset();

    component.changePage({ pageIndex: 2, previousPageIndex: 1, pageSize: 25, length: 80 });

    expect(adminUsers.listUsers).toHaveBeenCalledOnceWith(component.filters, 3);
  });

  it('shows loading while the request is pending', () => {
    const pending = new Subject<typeof page>();
    adminUsers.listUsers.and.returnValue(pending.asObservable());

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Cargando usuarios');
    expect(component.loading).toBeTrue();
  });

  it('shows an actionable error and retries', () => {
    adminUsers.listUsers.and.returnValue(throwError(() => new Error('network')));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No pudimos consultar los usuarios');
    expect(fixture.nativeElement.textContent).toContain('Reintentar');

    adminUsers.listUsers.and.returnValue(of(page));
    component.loadUsers();
    expect(component.users.length).toBe(2);
  });

  it('shows the empty state when the backend returns no users', () => {
    adminUsers.listUsers.and.returnValue(of({ ...page, count: 0, results: [] }));

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No hay usuarios para mostrar');
    expect(fixture.nativeElement.textContent).toContain('Limpiar filtros');
  });

  it('loads user detail from the V2 service', () => {
    fixture.detectChanges();

    component.openDetail(activeUser);
    fixture.detectChanges();

    expect(adminUsers.getUser).toHaveBeenCalledOnceWith(activeUser.id);
    expect(fixture.nativeElement.textContent).toContain('Ana Planificadora');
  });

  it('hides state actions without activate capability', () => {
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-label="Desactivar Ana Planificadora"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Activar Boris Operativo"]')).toBeNull();
  });

  it('shows and executes activate/deactivate actions with capability', () => {
    granted.add('accounts.usuario.activate');
    spyOn(window, 'confirm').and.returnValue(true);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-label="Desactivar Ana Planificadora"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[aria-label="Activar Boris Operativo"]')).not.toBeNull();

    component.toggleUserState(activeUser);
    component.toggleUserState(inactiveUser);

    expect(adminUsers.deactivate).toHaveBeenCalledOnceWith(activeUser.id);
    expect(adminUsers.activate).toHaveBeenCalledOnceWith(inactiveUser.id);
  });

  it('shows only tabs backed by granted capabilities', () => {
    granted.add('accounts.rol.view');
    granted.add('accounts.capacidad.view');
    fixture.detectChanges();

    const labels = Array.from(
      fixture.nativeElement.querySelectorAll('.mdc-tab__text-label'),
      (element: Element) => element.textContent?.trim(),
    );
    expect(labels).toEqual(['Usuarios', 'Roles', 'Permisos']);
    expect(labels).not.toContain('Solicitudes');
  });

  it('shows Requests only with view capability and refreshes Users after approval', () => {
    granted.add('accounts.solicitud.view');
    fixture.detectChanges();
    const labels = Array.from(
      fixture.nativeElement.querySelectorAll('.mdc-tab__text-label'),
      (element: Element) => element.textContent?.trim(),
    );
    expect(labels).toContain('Solicitudes');

    adminUsers.listUsers.calls.reset();
    component.selectedTabIndex = 1;
    fixture.detectChanges();
    const requestsTab = fixture.debugElement.query(
      By.directive(RequestsAdminTabComponent),
    ).componentInstance as RequestsAdminTabComponent;
    component.selectedUser = { ...activeUser, id: 'approved-request' };
    requestsTab.requestApproved.emit('approved-request');

    expect(adminUsers.listUsers).toHaveBeenCalledOnceWith(component.filters, 1);
    expect(component.selectedUser).toBeNull();
  });

  it('hides editing without capabilities and shows it with personal edit capability', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[aria-label="Editar Ana Planificadora"]')).toBeNull();

    granted.add('accounts.alcance.assign');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[aria-label="Editar Ana Planificadora"]')).toBeNull();

    granted.add('accounts.usuario.edit');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[aria-label="Editar Ana Planificadora"]')).not.toBeNull();
  });

  it('refreshes the table and open detail when the dialog emits a successful save', () => {
    granted.add('accounts.usuario.edit');
    const saved = new Subject<AdminUser>();
    const closed = new Subject<{ navigateToRequests?: boolean } | undefined>();
    const dialogRef = {
      componentInstance: { userSaved: saved },
      afterClosed: () => closed.asObservable(),
    } as unknown as MatDialogRef<UsuarioEdicionDialogComponent>;
    matDialog.open.and.returnValue(dialogRef);
    fixture.detectChanges();
    component.selectedUser = activeUser;

    component.openEditor(activeUser);
    const updated = { ...activeUser, first_name: 'Ana María', cargo: 'Jefa' };
    saved.next(updated);

    expect(component.users[0]).toEqual(updated);
    expect(component.selectedUser).toEqual(updated);
    expect(matDialog.open).toHaveBeenCalled();
  });
});
