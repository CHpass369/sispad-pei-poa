import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { DistributionComponent } from './distribution.component';
import {
  Allocation,
  BudgetService,
  DistributionSummary,
  FiscalYear,
} from './budget.service';
import { MonedaPipe } from './moneda.pipe';

describe('DistributionComponent', () => {
  let component: DistributionComponent;
  let fixture: ComponentFixture<DistributionComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const gestion: FiscalYear = {
    id: '2030', anio: 2030, estado: 'HABILITADA', estado_display: 'Habilitada',
    descripcion: '', anio_inicio_plurianual: null, anio_fin_plurianual: null,
    fecha_apertura: null, fecha_cierre: null, activa: true, gestion_anterior: null,
  };

  const resumen: DistributionSummary = {
    gestion: 2030,
    techo_distribuible: '1500.00',
    distribuido: '1000.00',
    reservado: '200.00',
    disponible: '300.00',
    porcentaje: 66.67,
    aperturas_count: 1,
    por_fuente: [{
      fuente_id: 'fuente-1', denominacion: 'Tesoro General',
      techo: '1500.00', distribuido: '1000.00', reservado: '200.00',
      disponible: '300.00', porcentaje: 66.67,
    }],
  };

  const apertura: Allocation = {
    id: 1, gestion: '2030', gestion_anio: 2030, version: 1, orden: 0,
    unidad_organizacional: null, unidad_detalle: null, distrito: null,
    distrito_detalle: null, da: null, da_detalle: null, ue: null, ue_detalle: null,
    categoria: null, categoria_detalle: null, proyecto_codigo: '',
    codigo_sisin: '12345678', actividad_codigo: '', denominacion: 'Apertura demo',
    tipo_apertura: 'DETAIL', estado: 'ACTIVA', estado_display: 'Activa',
    fuentes: [{ id: 1, fuente: 'fuente-1', fuente_detalle: { codigo: '11', denominacion: 'Tesoro General' }, organismo: null, organismo_detalle: null, monto: '1000.00' }],
    total: '1000.00',
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'resumenDistribucion', 'listarAperturas', 'listarReservas',
      'listarVersionesDistribucion', 'listarCategorias', 'opcionesCatalogo',
      'crearApertura', 'actualizarApertura', 'eliminarApertura',
      'cerrarApertura', 'crearReserva', 'liberarReserva',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestion] } as never));
    serviceSpy.resumenDistribucion.and.returnValue(of(resumen as never));
    serviceSpy.listarAperturas.and.returnValue(of({ count: 1, results: [apertura] } as never));
    serviceSpy.listarReservas.and.returnValue(of({ count: 0, results: [] } as never));
    serviceSpy.listarVersionesDistribucion.and.returnValue(of([] as never));
    serviceSpy.listarCategorias.and.returnValue(of({ count: 0, results: [] } as never));
    serviceSpy.opcionesCatalogo.and.returnValue(of({
      fuentes: [], organismos: [], rubros: [], objetos_gasto: [],
      entidades_transferencia: [], distritos: [], direcciones: [],
      unidades_ejecutoras: [], unidades_organizacionales: [],
    } as never));

    await TestBed.configureTestingModule({
      declarations: [DistributionComponent, MonedaPipe],
      imports: [HttpClientTestingModule, FormsModule],
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(DistributionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load summary and aperturas on init', () => {
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(serviceSpy.resumenDistribucion).toHaveBeenCalledWith('2030');
    expect(serviceSpy.listarAperturas).toHaveBeenCalledWith({ gestion: '2030' });
    expect(component.resumen?.techo_distribuible).toBe('1500.00');
    expect(component.aperturas.length).toBe(1);
  });

  it('should render summary cards', () => {
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Techo distribuible');
    expect(rendered.textContent).toContain('Bs 1.500,00');
    expect(rendered.textContent).toContain('66.67%');
    expect(rendered.textContent).toContain('Apertura demo');
  });

  it('should create an aperture calling the service', () => {
    serviceSpy.crearApertura.and.returnValue(of(apertura as never));
    component.gestionSeleccionada = '2030';
    component.abrirFormulario();
    component.nueva.denominacion = 'Apertura nueva';
    component.nueva.codigo_sisin = '87654321';
    component.filasFuentes = [{ fuente: 'fuente-1', organismo: '', monto: 500 }];
    component.guardar();
    expect(serviceSpy.crearApertura).toHaveBeenCalledWith(jasmine.objectContaining({
      gestion: '2030',
      denominacion: 'Apertura nueva',
      fuentes: [{ fuente: 'fuente-1', organismo: null, monto: 500 }],
    }));
    expect(component.mostrarFormulario).toBeFalse();
  });

  it('should show BUDGET_EXCEEDED error from create', () => {
    serviceSpy.crearApertura.and.returnValue(throwError(() => ({
      error: {
        error: { detail: ['El monto solicitado supera el saldo disponible de la fuente (1000 > 300).'] },
        code: 'BUDGET_EXCEEDED',
        details: { requested: '1000.00', available: '300.00', difference: '700.00' },
      },
    })));
    component.gestionSeleccionada = '2030';
    component.abrirFormulario();
    component.nueva.denominacion = 'Apertura excede';
    component.filasFuentes = [{ fuente: 'fuente-1', organismo: '', monto: 1000 }];
    component.guardar();
    expect(component.error).toContain('supera el saldo disponible');
    expect(component.mostrarFormulario).toBeTrue();
  });
});
