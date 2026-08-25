import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, Subject, throwError } from 'rxjs';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { AdminUsuariosModule } from './admin-usuarios.module';
import {
  AdminRegistrationRequest,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { RequestApprovalDialogComponent } from './request-approval-dialog.component';
import { RequestsAdminTabComponent } from './requests-admin-tab.component';

describe('RequestsAdminTabComponent', () => {
  let component: RequestsAdminTabComponent;
  let fixture: ComponentFixture<RequestsAdminTabComponent>;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let capabilities: jasmine.SpyObj<CapabilitiesService>;
  let dialog: jasmine.SpyObj<MatDialog>;
  let canApprove: boolean;

  const pending: AdminRegistrationRequest = {
    id: 'request-1',
    email: 'ana.pendiente@gob.bo',
    first_name: 'Ana',
    last_name: 'Pendiente',
    cargo: 'Analista',
    date_joined: '2026-08-25T10:30:00Z',
    unidad_solicitada: { id: 'unit-1', nombre: 'Dirección de Planificación' },
    estado: 'PENDIENTE',
  };
  const notPending: AdminRegistrationRequest = {
    ...pending,
    id: 'active-1',
    email: 'activa@gob.bo',
    estado: 'ACTIVO',
  };
  const page = {
    count: 2,
    next: null,
    previous: null,
    results: [pending, notPending],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService',
      ['listRequests'],
    );
    capabilities = jasmine.createSpyObj<CapabilitiesService>('CapabilitiesService', ['tiene']);
    dialog = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    canApprove = false;
    capabilities.tiene.and.callFake(code => code === 'accounts.solicitud.approve' && canApprove);
    adminUsers.listRequests.and.returnValue(of(page));

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: AdminUsuariosService, useValue: adminUsers },
        { provide: CapabilitiesService, useValue: capabilities },
        { provide: MatDialog, useValue: dialog },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RequestsAdminTabComponent);
    component = fixture.componentInstance;
  });

  it('renders only pending requests with the required columns', () => {
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    for (const heading of [
      'Usuario', 'Cargo', 'UO solicitada', 'Fecha de solicitud', 'Estado', 'Acciones',
    ]) {
      expect(text).toContain(heading);
    }
    expect(text).toContain('Ana Pendiente');
    expect(text).toContain('Dirección de Planificación');
    expect(text).toContain('Pendiente');
    expect(text).not.toContain('activa@gob.bo');
  });

  it('requests the selected backend page and refreshes from page one', () => {
    fixture.detectChanges();
    adminUsers.listRequests.calls.reset();

    component.changePage({ pageIndex: 2, previousPageIndex: 1, pageSize: 25, length: 80 });
    expect(adminUsers.listRequests).toHaveBeenCalledOnceWith(3);

    adminUsers.listRequests.calls.reset();
    component.refresh();
    expect(component.pageIndex).toBe(0);
    expect(adminUsers.listRequests).toHaveBeenCalledOnceWith(1);
  });

  it('shows loading, actionable error and empty states', () => {
    const pendingResponse = new Subject<typeof page>();
    adminUsers.listRequests.and.returnValue(pendingResponse.asObservable());
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Cargando solicitudes');

    pendingResponse.error(new Error('network'));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No pudimos consultar las solicitudes');

    adminUsers.listRequests.and.returnValue(of({ ...page, count: 0, results: [] }));
    component.loadRequests();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay solicitudes pendientes');
  });

  it('hides approval without capability and opens it when granted', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[aria-label="Aprobar solicitud de Ana Pendiente"]')).toBeNull();

    canApprove = true;
    const closed = new Subject<undefined>();
    dialog.open.and.returnValue({
      afterClosed: () => closed.asObservable(),
    } as MatDialogRef<RequestApprovalDialogComponent>);
    fixture.detectChanges();

    const action = fixture.nativeElement.querySelector(
      '[aria-label="Aprobar solicitud de Ana Pendiente"]',
    ) as HTMLButtonElement;
    expect(action).not.toBeNull();
    action.click();
    expect(dialog.open).toHaveBeenCalled();
  });

  it('removes and reloads the request and emits refresh after approval', () => {
    canApprove = true;
    adminUsers.listRequests.and.returnValues(
      of({ ...page, count: 1, results: [pending] }),
      of({ ...page, count: 0, results: [] }),
    );
    dialog.open.and.returnValue({
      afterClosed: () => of({ approved: true as const, requestId: pending.id }),
    } as MatDialogRef<RequestApprovalDialogComponent>);
    spyOn(component.requestApproved, 'emit');
    fixture.detectChanges();

    component.openApproval(pending);

    expect(component.requestApproved.emit).toHaveBeenCalledOnceWith(pending.id);
    expect(adminUsers.listRequests).toHaveBeenCalledTimes(2);
    expect(component.requests).toEqual([]);
  });

  it('keeps an actionable error when the requests endpoint fails', () => {
    adminUsers.listRequests.and.returnValue(throwError(() => new Error('offline')));
    fixture.detectChanges();
    expect(component.error).toContain('No se pudo cargar');
  });
});
