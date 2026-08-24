import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef } from '@angular/core';
import { fakeAsync, tick } from '@angular/core/testing';
import { NEVER, Subject, of, throwError } from 'rxjs';
import { BudgetService, FiscalYear } from './budget.service';
import { AuthService } from '../../../core/services/auth.service';
import { PermissionsService } from '../../../core/services/permissions.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../../core/testing/gestion-habilitada.stub';
import { FiscalYearComponent } from './fiscal-year.component';

describe('FiscalYearComponent', () => {
  let component: FiscalYearComponent;
  let fixture: ComponentFixture<FiscalYearComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;
  let authSpy: jasmine.SpyObj<AuthService>;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;

  const mockGestiones: FiscalYear[] = [
    {
      id: 'a1',
      anio: 2026,
      estado: 'HABILITADA',
      estado_display: 'Habilitada',
      descripcion: '',
      anio_inicio_plurianual: null,
      anio_fin_plurianual: null,
      fecha_apertura: '2026-01-05T12:00:00Z',
      fecha_cierre: null,
      activa: true,
      gestion_anterior: null,
      puede_habilitar: false,
      puede_reabrir: false,
      puede_cerrar: true,
      puede_eliminar: false,
    },
    {
      id: 'a2',
      anio: 2027,
      estado: 'preparacion',
      estado_display: 'Preparación',
      descripcion: '',
      anio_inicio_plurianual: null,
      anio_fin_plurianual: null,
      fecha_apertura: null,
      fecha_cierre: null,
      activa: true,
      gestion_anterior: 2026,
      puede_habilitar: true,
      puede_reabrir: false,
      puede_cerrar: true,
      puede_eliminar: true,
    },
  ];

  const gestionCerrada: FiscalYear = {
    id: 'a3',
    anio: 2025,
    estado: 'CERRADA',
    estado_display: 'Ciclo cerrado',
    descripcion: '',
    anio_inicio_plurianual: null,
    anio_fin_plurianual: null,
    fecha_apertura: '2025-01-05T12:00:00Z',
    fecha_cierre: '2025-12-31T12:00:00Z',
    activa: false,
    gestion_anterior: null,
    puede_habilitar: false,
    puede_reabrir: true,
    puede_cerrar: false,
    puede_eliminar: false,
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'crear', 'habilitar', 'cerrar', 'reabrir', 'eliminar',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 2, results: mockGestiones }));
    serviceSpy.crear.and.returnValue(of(mockGestiones[0]));
    serviceSpy.habilitar.and.returnValue(of(mockGestiones[0]));
    serviceSpy.cerrar.and.returnValue(of(mockGestiones[0]));
    serviceSpy.reabrir.and.returnValue(of(gestionCerrada));
    serviceSpy.eliminar.and.returnValue(of(void 0));

    authSpy = jasmine.createSpyObj('AuthService', [], { user$: of({
      id: 'u1',
      email: 'admin@budget.test',
      first_name: 'Ada',
      last_name: 'Admin',
      cargo: 'Responsable',
      telefono: '',
      roles: [],
      roles_detalle: [],
      activo: true,
      is_staff: true,
      is_superuser: true,
      debe_cambiar_password: false,
      last_login: '',
      date_joined: '',
    }) });

    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);
    permissionsSpy.hasAnyCapability.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [FiscalYearComponent],
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: BudgetService, useValue: serviceSpy },
        { provide: AuthService, useValue: authSpy },
        { provide: PermissionsService, useValue: permissionsSpy },
        // El candado se carga al arranque de la app, no por pantalla.
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FiscalYearComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list fiscal years on init', () => {
    fixture.detectChanges();
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(component.gestiones.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should mark the view after an asynchronous fiscal year response', () => {
    const response$ = new Subject<{ count: number; results: FiscalYear[] }>();
    serviceSpy.listar.and.returnValue(response$.asObservable());
    const markForCheck = spyOn(
      (component as unknown as { cdr: ChangeDetectorRef }).cdr,
      'markForCheck',
    );

    fixture.detectChanges();
    markForCheck.calls.reset();

    response$.next({ count: 2, results: mockGestiones });
    response$.complete();

    expect(component.gestiones).toEqual(mockGestiones);
    expect(component.cargando).toBeFalse();
    expect(markForCheck).toHaveBeenCalled();

    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('tbody tr').length).toBe(2);
  });

  it('should render rows with estado badge', () => {
    fixture.detectChanges();
    const filas = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(filas.length).toBe(2);
    const badges = fixture.nativeElement.querySelectorAll('.badge');
    expect(badges.length).toBe(2);
    expect(badges[0].textContent).toContain('Habilitada');
    expect(badges[0].className).toContain('badge-success');
  });

  const clickEnBoton = (etiqueta: string): HTMLButtonElement => {
    const boton = Array.from(fixture.nativeElement.querySelectorAll('button')).find(
      (b: Element) => b.textContent?.trim() === etiqueta,
    ) as HTMLButtonElement;
    expect(boton).withContext(`botón "${etiqueta}"`).toBeTruthy();
    boton.click();
    fixture.detectChanges();
    return boton;
  };

  it('should confirm before calling the habilitar service', () => {
    fixture.detectChanges();

    clickEnBoton('Habilitar');
    expect(serviceSpy.habilitar).not.toHaveBeenCalled();
    expect(component.accionPendiente?.tipo).toBe('habilitar');

    component.confirmarAccion();

    expect(serviceSpy.habilitar).toHaveBeenCalledWith('a2');
    expect(component.accionPendiente).toBeNull();
    expect(component.mensaje).toBe('Gestión 2027 habilitada');
  });

  it('should not offer transitions the backend rejected', () => {
    fixture.detectChanges();
    const etiquetas = Array.from(
      fixture.nativeElement.querySelectorAll('tbody tr:first-child button'),
    ).map((b: Element) => b.textContent?.trim());

    expect(etiquetas).toEqual(['Cerrar']);
  });

  it('should require a motivo before reopening a closed fiscal year', () => {
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestionCerrada] }));
    fixture.detectChanges();

    clickEnBoton('Reabrir');
    expect(component.confirmacionDeshabilitada).toBeTrue();

    component.confirmarAccion();
    expect(serviceSpy.reabrir).not.toHaveBeenCalled();

    component.motivo = '  se cerró por error  ';
    expect(component.confirmacionDeshabilitada).toBeFalse();

    component.confirmarAccion();
    expect(serviceSpy.reabrir).toHaveBeenCalledWith('a3', 'se cerró por error');
    expect(component.mensaje).toBe('Gestión 2025 reabierta');
  });

  it('should delete a fiscal year after confirmation', () => {
    fixture.detectChanges();

    clickEnBoton('Eliminar');
    expect(serviceSpy.eliminar).not.toHaveBeenCalled();

    component.confirmarAccion();

    expect(serviceSpy.eliminar).toHaveBeenCalledWith('a2');
    expect(component.mensaje).toBe('Gestión 2027 eliminada');
    expect(component.accionPendiente).toBeNull();
  });

  it('should surface the backend reason when an action is rejected', () => {
    serviceSpy.eliminar.and.returnValue(
      throwError(() => ({
        status: 400,
        message: 'detail: La gestión 2027 tiene registros dependientes y no se puede eliminar.',
      })),
    );
    fixture.detectChanges();

    clickEnBoton('Eliminar');
    component.confirmarAccion();
    fixture.detectChanges();

    expect(component.error)
      .toBe('La gestión 2027 tiene registros dependientes y no se puede eliminar.');
    expect(component.accionPendiente).withContext('el modal sigue abierto').not.toBeNull();
    expect(fixture.nativeElement.querySelector('.modal-error').textContent)
      .toContain('registros dependientes');
  });

  it('should report which fiscal year is open for formulation', () => {
    fixture.detectChanges();
    expect(component.gestionEnCurso?.anio).toBe(2026);
    expect(fixture.nativeElement.querySelector('.resumen-ciclo').textContent)
      .toContain('gestión 2026');

    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestionCerrada] }));
    component.cargar();
    fixture.detectChanges();

    expect(component.gestionEnCurso).toBeNull();
    expect(fixture.nativeElement.querySelector('.resumen-ciclo').textContent)
      .toContain('Ninguna gestión habilitada');
  });

  it('should show empty state when no fiscal years', () => {
    serviceSpy.listar.and.returnValue(of({ count: 0, results: [] }));
    fixture.detectChanges();
    const empty = fixture.nativeElement.querySelector('.empty');
    expect(empty).toBeTruthy();
    expect(empty.textContent).toContain('Sin gestiones');
  });

  it('should clear the error and keep a valid response', () => {
    component.error = 'Error anterior';
    component.cargar();

    expect(component.error).toBe('');
    expect(component.gestiones).toEqual(mockGestiones);
    expect(component.cargando).toBeFalse();
  });

  it('should use an empty list for a null response', () => {
    serviceSpy.listar.and.returnValue(of(null as unknown as { count: number; results: FiscalYear[] }));
    component.gestiones = mockGestiones;

    component.cargar();

    expect(component.gestiones).toEqual([]);
    expect(component.cargando).toBeFalse();
  });

  it('should use an empty list when results is not an array', () => {
    serviceSpy.listar.and.returnValue(of({ count: 1, results: {} } as unknown as { count: number; results: FiscalYear[] }));

    component.cargar();

    expect(component.gestiones).toEqual([]);
    expect(component.cargando).toBeFalse();
  });

  it('should show a session error and stop loading for unauthorized responses', () => {
    serviceSpy.listar.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 401 })),
    );

    component.cargar();

    expect(component.error).toContain('Inicie sesión nuevamente');
    expect(component.cargando).toBeFalse();
  });

  it('should show an error and stop loading after the request timeout', fakeAsync(() => {
    serviceSpy.listar.and.returnValue(NEVER);

    component.cargar();
    expect(component.cargando).toBeTrue();

    tick(10_000);

    expect(component.error).toContain('tardó demasiado');
    expect(component.cargando).toBeFalse();
  }));

  it('should hide action buttons without budget.manage capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    fixture.detectChanges();
    expect(component.puedeGestionar).toBeFalse();
    expect(fixture.nativeElement.querySelectorAll('tbody tr button').length).toBe(0);
  });

  it('should open an accessible modal and derive annual dates after year changes', () => {
    fixture.detectChanges();

    const abrir = Array.from(fixture.nativeElement.querySelectorAll('button'))
      .find((button: Element) => button.textContent?.includes('Nueva gestión')) as HTMLButtonElement;
    abrir.click();
    component.form.anio = 2027;
    fixture.detectChanges();

    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(component.fechaInicioProgramada).toBe('01/01/2027');
    expect(component.fechaCierreProgramada).toBe('31/12/2027');

    component.form.anio = 2031;
    expect(component.fechaInicioProgramada).toBe('01/01/2031');
    expect(component.fechaCierreProgramada).toBe('31/12/2031');
  });

  it('should require the habilitation document before creating', () => {
    component.abrirModal();
    component.form.anio = 2027;

    component.crear();

    expect(component.error).toContain('documento');
    expect(serviceSpy.crear).not.toHaveBeenCalled();
  });

  it('should close the form and open confirmation with the created year', () => {
    serviceSpy.crear.and.returnValue(of({ ...mockGestiones[0], anio: 2028 }));
    fixture.detectChanges();
    component.abrirModal();
    component.form.anio = 2028;
    component.archivo = new File(['document'], 'habilitacion.pdf', { type: 'application/pdf' });

    component.crear();
    fixture.detectChanges();

    expect(component.modalAbierto).toBeFalse();
    expect(component.confirmacionAbierta).toBeTrue();
    expect(component.anioCreado).toBe(2028);
    expect(component.form).toEqual({ anio: null, heredar_de: null });
    expect(component.archivo).toBeNull();
    expect(component.creando).toBeFalse();
    expect(serviceSpy.listar).toHaveBeenCalledTimes(2);

    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.getAttribute('aria-labelledby')).toBe('confirmacion-gestion-titulo');
    expect(dialog.textContent).toContain('Gestión fiscal 2028 creada correctamente.');
  });

  it('should close the creation confirmation when accepting', () => {
    component.anioCreado = 2028;
    component.confirmacionAbierta = true;
    fixture.detectChanges();

    const aceptar = Array.from(fixture.nativeElement.querySelectorAll('button'))
      .find((button: Element) => button.textContent?.trim() === 'Aceptar') as HTMLButtonElement;
    aceptar.click();

    expect(component.confirmacionAbierta).toBeFalse();
    expect(component.anioCreado).toBeNull();
  });

  it('should not open confirmation after a creation error', () => {
    serviceSpy.crear.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 400, error: { detail: 'Solicitud inválida' } })),
    );
    fixture.detectChanges();
    component.abrirModal();
    component.form.anio = 2028;
    component.archivo = new File(['document'], 'habilitacion.pdf', { type: 'application/pdf' });

    component.crear();
    fixture.detectChanges();

    expect(component.confirmacionAbierta).toBeFalse();
    expect(component.modalAbierto).toBeTrue();
    expect(component.creando).toBeFalse();
  });

  it('should reject a fiscal year that already exists without sending a request', () => {
    fixture.detectChanges();
    component.abrirModal();
    component.form.anio = 2027;
    component.archivo = new File(['document'], 'habilitacion.pdf', { type: 'application/pdf' });

    component.crear();
    fixture.detectChanges();

    expect(component.creando).toBeFalse();
    expect(component.error).toBe('Ya existe una gestión para el año 2027. Seleccione otro año.');
    expect(fixture.nativeElement.querySelector('.modal-error').textContent)
      .toContain('Ya existe una gestión para el año 2027.');
    expect(component.confirmacionAbierta).toBeFalse();
    expect(serviceSpy.crear).not.toHaveBeenCalled();
  });

  it('should show the interceptor message and stop creating after an HTTP 400', () => {
    serviceSpy.crear.and.returnValue(
      throwError(() => ({ status: 400, message: 'Ya existe una gestión para el año 2027.' })),
    );
    fixture.detectChanges();
    component.abrirModal();
    component.form.anio = 2028;
    component.archivo = new File(['document'], 'habilitacion.pdf', { type: 'application/pdf' });

    component.crear();
    fixture.detectChanges();

    expect(component.creando).toBeFalse();
    expect(component.error).toBe('Ya existe una gestión para el año 2027.');
    expect(fixture.nativeElement.querySelector('.modal-error').textContent)
      .toContain('Ya existe una gestión para el año 2027.');
    expect(component.confirmacionAbierta).toBeFalse();
    expect(serviceSpy.crear).toHaveBeenCalledTimes(1);
  });

  it('should show a timeout message and stop creating after 15 seconds', fakeAsync(() => {
    serviceSpy.crear.and.returnValue(NEVER);
    fixture.detectChanges();
    component.abrirModal();
    component.form.anio = 2028;
    component.archivo = new File(['document'], 'habilitacion.pdf', { type: 'application/pdf' });

    component.crear();
    expect(component.creando).toBeTrue();

    tick(15_000);
    fixture.detectChanges();

    expect(component.creando).toBeFalse();
    expect(component.error).toContain('La creación tardó demasiado');
    expect(fixture.nativeElement.querySelector('.modal-error').textContent)
      .toContain('La creación tardó demasiado');
    expect(component.confirmacionAbierta).toBeFalse();
  }));

  it('should send the authenticated user display as read-only modal data', () => {
    component.abrirModal();
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('#encargado-cargado') as HTMLInputElement;
    expect(input.readOnly).toBeTrue();
    expect(input.value).toBe('Ada Admin');
  });

  it('should cancel without saving and close the modal', () => {
    component.abrirModal();
    component.form.anio = 2027;
    component.cancelar();

    expect(component.modalAbierto).toBeFalse();
    expect(component.form.anio).toBeNull();
    expect(serviceSpy.crear).not.toHaveBeenCalled();
  });
});
