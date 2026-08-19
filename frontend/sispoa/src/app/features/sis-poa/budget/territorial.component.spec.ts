import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { TerritorialComponent } from './territorial.component';
import {
  BudgetService,
  FiscalYear,
  DistribucionTerritorial,
} from './budget.service';
import { MonedaPipe } from './moneda.pipe';

describe('TerritorialComponent', () => {
  let component: TerritorialComponent;
  let fixture: ComponentFixture<TerritorialComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const gestion: FiscalYear = {
    id: '2030', anio: 2030, estado: 'HABILITADA', estado_display: 'Habilitada',
    descripcion: '', anio_inicio_plurianual: null, anio_fin_plurianual: null,
    fecha_apertura: null, fecha_cierre: null, activa: true, gestion_anterior: null,
  };

  const calculada: DistribucionTerritorial = {
    id: 1, gestion: '2030', gestion_anio: 2030, version: null,
    fuente: 'fuente-1',
    fuente_detalle: { codigo: '11', denominacion: 'Tesoro General' },
    organismo: null, organismo_detalle: null,
    metodo: 'POBLACION', metodo_display: 'Población',
    bolsa_total: '600.00', estado: 'CALCULADA', estado_display: 'Calculada',
    observaciones: '',
    asignaciones: [
      { id: 1, distrito: 'd1', distrito_detalle: { codigo: 'D1', nombre: 'Centro' }, poblacion: 100, porcentaje: null, monto_calculado: '100.00', ajuste: '0.00', monto_final: '100.00' },
      { id: 2, distrito: 'd2', distrito_detalle: { codigo: 'D2', nombre: 'Norte' }, poblacion: 200, porcentaje: null, monto_calculado: '200.00', ajuste: '0.00', monto_final: '200.00' },
      { id: 3, distrito: 'd3', distrito_detalle: { codigo: 'D3', nombre: 'Sur' }, poblacion: 300, porcentaje: null, monto_calculado: '300.00', ajuste: '0.00', monto_final: '300.00' },
    ],
    total_asignado: '600.00',
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'opcionesCatalogo', 'listarTerritoriales',
      'crearTerritorial', 'calcularTerritorial',
      'aplicarTerritorial', 'liberarTerritorial',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestion] } as never));
    serviceSpy.opcionesCatalogo.and.returnValue(of({
      fuentes: [{ id: 'fuente-1', codigo: '11', denominacion: 'Tesoro General' }],
      organismos: [], rubros: [], objetos_gasto: [],
      entidades_transferencia: [],
      distritos: [
        { id: 'd1', codigo: 'D1', nombre: 'Centro' },
        { id: 'd2', codigo: 'D2', nombre: 'Norte' },
        { id: 'd3', codigo: 'D3', nombre: 'Sur' },
      ],
      direcciones: [], unidades_ejecutoras: [], unidades_organizacionales: [],
    } as never));
    serviceSpy.listarTerritoriales.and.returnValue(of({ count: 0, results: [] } as never));

    await TestBed.configureTestingModule({
      declarations: [TerritorialComponent, MonedaPipe],
      imports: [HttpClientTestingModule, FormsModule],
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(TerritorialComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load gestiones y catálogos on init', () => {
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(serviceSpy.opcionesCatalogo).toHaveBeenCalled();
    expect(component.gestionSeleccionada).toBe('2030');
  });

  it('calcular muestra los montos calculados y la suma coincide con la bolsa', () => {
    component.actual = calculada;
    component.seleccionar(calculada);
    serviceSpy.calcularTerritorial.and.returnValue(of(calculada as never));
    component.calcular();
    expect(serviceSpy.calcularTerritorial).toHaveBeenCalledWith(
      1, jasmine.arrayContaining([jasmine.objectContaining({ distrito: 'd1' })])
    );
    expect(component.actual?.asignaciones.length).toBe(3);
    expect(component.sumaAsignada()).toBe(600);
    expect(component.coincide()).toBeTrue();
    expect(component.montoAsignacion(component.filas[0], 'monto_final')).toBe('100.00');
  });

  it('aplicar llama al servicio de aplicación', () => {
    component.actual = calculada;
    spyOn(window, 'confirm').and.returnValue(true);
    serviceSpy.aplicarTerritorial.and.returnValue(of(calculada as never));
    component.aplicar();
    expect(serviceSpy.aplicarTerritorial).toHaveBeenCalledWith(1);
  });

  it('liberar llama al servicio de liberación', () => {
    const aplicada = { ...calculada, estado: 'APLICADA', estado_display: 'Aplicada' };
    component.actual = aplicada;
    spyOn(window, 'confirm').and.returnValue(true);
    serviceSpy.liberarTerritorial.and.returnValue(of(calculada as never));
    component.liberar();
    expect(serviceSpy.liberarTerritorial).toHaveBeenCalledWith(1);
  });

  it('muestra error BUDGET_EXCEEDED al aplicar', () => {
    component.actual = calculada;
    spyOn(window, 'confirm').and.returnValue(true);
    serviceSpy.aplicarTerritorial.and.returnValue(throwError(() => ({
      error: {
        error: { detail: ['El monto solicitado supera el saldo disponible de la fuente (1600 > 1500).'] },
        code: 'BUDGET_EXCEEDED',
        details: { requested: '1600.00', available: '1500.00', difference: '100.00' },
      },
    })));
    component.aplicar();
    expect(component.error).toContain('supera el saldo disponible');
  });
});
