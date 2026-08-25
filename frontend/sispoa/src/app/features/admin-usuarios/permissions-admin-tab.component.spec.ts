import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, Subject, throwError } from 'rxjs';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { AdminCapability, AdminUsuariosService } from './admin-usuarios.service';
import { PermissionsAdminTabComponent } from './permissions-admin-tab.component';

describe('PermissionsAdminTabComponent', () => {
  let fixture: ComponentFixture<PermissionsAdminTabComponent>;
  let component: PermissionsAdminTabComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;

  const capability: AdminCapability = {
    id: 'cap-1',
    codigo: 'sis_pe.pad.view',
    nombre: 'Ver PAD',
    descripcion: 'Consulta del PAD',
    sistema: 'sis_pe',
    activo: true,
    orden: 1,
  };
  const page = {
    count: 2,
    next: null,
    previous: null,
    results: [
      capability,
      {
        ...capability,
        id: 'cap-accounts',
        codigo: 'accounts.usuario.view',
        nombre: 'Ver usuarios',
        sistema: 'accounts' as const,
      },
    ],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService', ['listCapabilities'],
    );
    adminUsers.listCapabilities.and.returnValue(of(page));

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [{ provide: AdminUsuariosService, useValue: adminUsers }],
    }).compileComponents();

    fixture = TestBed.createComponent(PermissionsAdminTabComponent);
    component = fixture.componentInstance;
  });

  it('renders the read-only capability catalog without mutation actions', () => {
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('sis_pe.pad.view');
    expect(text).toContain('accounts.usuario.view');
    expect(text).toContain('Sistema efectivo');
    expect(text).toContain('Solo lectura');
    expect(text).not.toContain('Crear permiso');
    expect(text).not.toContain('Editar permiso');
  });

  it('sends permission filters and the selected backend page', () => {
    fixture.detectChanges();
    adminUsers.listCapabilities.calls.reset();
    component.filters = { search: 'usuario', system: 'accounts', active: false };
    component.pageIndex = 2;

    component.applyFilters();
    expect(adminUsers.listCapabilities).toHaveBeenCalledOnceWith(component.filters, 1);

    component.changePage({ pageIndex: 3, previousPageIndex: 2, pageSize: 25, length: 100 });
    expect(adminUsers.listCapabilities).toHaveBeenCalledWith(component.filters, 4);
  });

  it('shows loading, error and empty states', () => {
    const pending = new Subject<typeof page>();
    adminUsers.listCapabilities.and.returnValue(pending.asObservable());
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Cargando permisos');

    adminUsers.listCapabilities.and.returnValue(throwError(() => new Error('network')));
    component.loadCapabilities();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No pudimos consultar los permisos');

    adminUsers.listCapabilities.and.returnValue(of({ ...page, count: 0, results: [] }));
    component.loadCapabilities();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay permisos para mostrar');
  });

  it('defensively excludes SIS-PRO from the rendered catalog', () => {
    adminUsers.listCapabilities.and.returnValue(of({
      ...page,
      results: [{
        ...capability,
        id: 'cap-pro',
        codigo: 'sis_pro.project.view',
        sistema: 'sis_pro',
      } as unknown as AdminCapability],
    }));
    fixture.detectChanges();

    expect(component.capabilities).toEqual([]);
    expect(fixture.nativeElement.textContent).not.toContain('sis_pro.project.view');
  });
});
