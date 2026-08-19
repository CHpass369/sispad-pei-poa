import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { AuditEvent, BudgetService, FiscalYear } from './budget.service';
import { AuditComponent } from './audit.component';

describe('AuditComponent', () => {
  let component: AuditComponent;
  let fixture: ComponentFixture<AuditComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const mockGestiones: FiscalYear[] = [
    {
      id: 'g1',
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
    },
  ];

  const mockEvento: AuditEvent = {
    id: 'e1',
    usuario: 'u1',
    usuario_email: 'admin@test.local',
    usuario_nombre: 'Admin Test',
    accion: 'crear',
    accion_display: 'Creación',
    entidad: 'Apertura',
    entidad_display: 'Apertura programática',
    entidad_id: '42',
    version: 1,
    resumen: 'Apertura "A" creada (gestión 2026)',
    datos_previos: null,
    datos_posteriores: { total: '1000.00', denominacion: 'A' },
    direccion_ip: null,
    gestion: 2026,
    creado_en: '2026-08-14T12:00:00Z',
  };

  const mockEvento2: AuditEvent = {
    ...mockEvento,
    id: 'e2',
    accion: 'aprobar',
    accion_display: 'Aprobación',
    entidad: 'TechoVersion',
    entidad_display: 'Techo directivo',
    resumen: 'Techo directivo fijado v1 (gestión 2026)',
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', ['listar', 'listarAuditoria']);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: mockGestiones }));
    serviceSpy.listarAuditoria.and.returnValue(
      of({ count: 2, results: [mockEvento, mockEvento2] }),
    );

    await TestBed.configureTestingModule({
      declarations: [AuditComponent],
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(AuditComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load fiscal years and query the audit log on init', () => {
    fixture.detectChanges();
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(serviceSpy.listarAuditoria).toHaveBeenCalledWith(
      jasmine.objectContaining({ gestion: 'g1' }),
    );
    expect(component.eventos.length).toBe(2);
    expect(component.total).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should render table rows with operation badge and summary', () => {
    fixture.detectChanges();
    const filas = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(filas.length).toBe(2);
    const badges = fixture.nativeElement.querySelectorAll('tbody .badge');
    expect(badges.length).toBe(2);
    expect(badges[0].textContent).toContain('Creación');
    expect(badges[1].textContent).toContain('Aprobación');
    expect(filas[0].textContent).toContain('Apertura "A" creada');
    expect(component.badgeClase('crear')).toContain('badge-crear');
    expect(component.badgeClase('aprobar')).toContain('badge-aprobar');
  });

  it('should call listarAuditoria with filters on buscar', () => {
    fixture.detectChanges();
    component.filtros = {
      gestion: 'g1',
      entidad: 'reform',
      accion: 'aprobar',
      desde: '2026-01-01',
      hasta: '2026-12-31',
    };
    component.buscar();
    expect(serviceSpy.listarAuditoria).toHaveBeenCalledWith(
      jasmine.objectContaining({
        gestion: 'g1',
        entidad: 'reform',
        accion: 'aprobar',
        desde: '2026-01-01',
        hasta: '2026-12-31',
        page: 1,
      }),
    );
    expect(component.pagina).toBe(1);
  });

  it('should reset filters on limpiar', () => {
    fixture.detectChanges();
    component.filtros = { gestion: 'g1', entidad: 'reform' };
    component.limpiar();
    expect(component.filtros).toEqual({});
    expect(serviceSpy.listarAuditoria).toHaveBeenCalledWith(
      jasmine.objectContaining({ page: 1 }),
    );
  });

  it('should toggle detail and render readable JSON', () => {
    fixture.detectChanges();
    const fila = fixture.nativeElement.querySelectorAll('tbody tr')[0];
    fila.click();
    fixture.detectChanges();
    expect(component.seleccionado?.id).toBe('e1');
    const detalle = fixture.nativeElement.querySelector('.detalle');
    expect(detalle).toBeTruthy();
    expect(detalle.textContent).toContain('Apertura programática');
    const pre = fixture.nativeElement.querySelectorAll('pre.json');
    expect(pre.length).toBe(2);
    expect(pre[1].textContent).toContain('1000.00');
    // Segundo click cierra el detalle.
    fila.click();
    fixture.detectChanges();
    expect(component.seleccionado).toBeNull();
  });

  it('should paginate through pages', () => {
    fixture.detectChanges();
    expect(component.totalPaginas).toBe(1);
    component.total = 60;
    expect(component.totalPaginas).toBe(3);
    component.pagina = 2;
    component.paginaSiguiente();
    expect(component.pagina).toBe(3);
    component.paginaSiguiente(); // ya no hay página siguiente
    expect(component.pagina).toBe(3);
    component.paginaAnterior();
    expect(component.pagina).toBe(2);
    component.pagina = 1;
    component.paginaAnterior(); // ya no hay página anterior
    expect(component.pagina).toBe(1);
  });
});
