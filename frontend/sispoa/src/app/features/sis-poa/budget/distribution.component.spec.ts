import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { DistributionComponent } from './distribution.component';
import {
  Allocation,
  BudgetService,
  DistributionSummary,
  DistributionVersion,
  FiscalYear,
  ValidacionDistribucion,
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

  const version = (estado: string, inmutable = false): DistributionVersion => ({
    id: 1, gestion: '2030', gestion_anio: 2030, numero: 1,
    estado, estado_display: estado, hash: inmutable ? 'a'.repeat(64) : '',
    fecha_fijacion: null, fijado_por: null, fijado_por_email: null,
    observaciones: '', inmutable,
  });

  const validacionInvalida: ValidacionDistribucion = {
    valida: false,
    diferencias: [{
      fuente_id: 'fuente-1', denominacion: 'Tesoro General',
      techo: '1500.00', distribuido: '1000.00', reservado: '200.00',
      diferencia: '300.00',
    }],
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'resumenDistribucion', 'listarAperturas', 'listarReservas',
      'listarVersionesDistribucion', 'listarCategorias', 'opcionesCatalogo',
      'crearApertura', 'actualizarApertura', 'eliminarApertura',
      'cerrarApertura', 'crearReserva', 'liberarReserva',
      'validarDistribucion', 'submitDistribucion', 'observarDistribucion',
      'aprobarDistribucion', 'fijarDistribucion', 'ajusteDistribucion',
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

  // -- Fijación de la distribución (Fase 7) ----------------------------------

  it('should show submit button in BORRADOR and hide approve/freeze', () => {
    component.versiones = [version('BORRADOR')];
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    const botones = rendered.querySelectorAll('button');
    expect(Array.from(botones).some((b) => b.textContent?.includes('Enviar a revisión'))).toBeTrue();
    expect(Array.from(botones).some((b) => b.textContent?.includes('Aprobar'))).toBeFalse();
    expect(Array.from(botones).some((b) => b.textContent?.includes('Fijar distribución'))).toBeFalse();
  });

  it('should show observe/approve in EN_REVISION and freeze in APROBADO', () => {
    component.versiones = [version('EN_REVISION')];
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    const botones = Array.from(rendered.querySelectorAll('button'))
      .map((b) => b.textContent?.trim() ?? '');
    expect(botones).toContain('Observar');
    expect(botones).toContain('Aprobar');
    expect(botones).not.toContain('Fijar distribución');

    component.versiones = [version('APROBADO')];
    fixture.detectChanges();
    const botones2 = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    ).map((b) => b.textContent?.trim() ?? '');
    expect(botones2).toContain('Fijar distribución');
  });

  it('should show Ajuste button only on frozen versions', () => {
    component.versiones = [version('FIJADO', true)];
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    expect(Array.from(rendered.querySelectorAll('button'))
      .some((b) => b.textContent?.includes('Ajuste'))).toBeTrue();
    expect(rendered.textContent).toContain('FIJADA (inmutable)');
    expect(rendered.textContent).toContain('Distribución fijada');
  });

  it('should load validation differences on validar()', () => {
    serviceSpy.validarDistribucion.and.returnValue(of(validacionInvalida as never));
    component.versiones = [version('BORRADOR')];
    fixture.detectChanges();
    component.validar();
    fixture.detectChanges();
    expect(serviceSpy.validarDistribucion).toHaveBeenCalledWith(1);
    expect(component.validacion?.valida).toBeFalse();
    expect(component.validacion?.diferencias[0].diferencia).toBe('300.00');
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Tesoro General');
    expect(rendered.textContent).toContain('Bs 300,00');
    expect(rendered.textContent).toContain('no válida');
  });

  it('should show success badge when validation passes', () => {
    serviceSpy.validarDistribucion.and.returnValue(of({
      valida: true,
      diferencias: [{
        fuente_id: 'fuente-1', denominacion: 'Tesoro General',
        techo: '1500.00', distribuido: '1000.00', reservado: '500.00',
        diferencia: '0.00',
      }],
    } as never));
    component.versiones = [version('BORRADOR')];
    fixture.detectChanges();
    component.validar();
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('diferencia 0');
    expect(rendered.textContent).toContain('válida');
  });

  it('should submit the active version and reload', () => {
    serviceSpy.submitDistribucion.and.returnValue(of(version('EN_REVISION') as never));
    component.versiones = [version('BORRADOR')];
    fixture.detectChanges();
    component.enviarRevision();
    expect(serviceSpy.submitDistribucion).toHaveBeenCalledWith(1);
    expect(serviceSpy.listarVersionesDistribucion).toHaveBeenCalled();
  });

  it('should observe require a motivo', () => {
    serviceSpy.observarDistribucion.and.returnValue(of(version('OBSERVADO') as never));
    component.versiones = [version('EN_REVISION')];
    fixture.detectChanges();
    component.observacionTexto = '';
    component.observar();
    expect(component.error).toContain('motivo');
    expect(serviceSpy.observarDistribucion).not.toHaveBeenCalled();
    component.observacionTexto = 'Falta desglose';
    component.observar();
    expect(serviceSpy.observarDistribucion).toHaveBeenCalledWith(1, 'Falta desglose');
  });

  it('should freeze the approved version', () => {
    serviceSpy.fijarDistribucion.and.returnValue(of(version('FIJADO', true) as never));
    spyOn(window, 'confirm').and.returnValue(true);
    component.versiones = [version('APROBADO')];
    fixture.detectChanges();
    component.observacionTexto = 'Cierre';
    component.fijar();
    expect(serviceSpy.fijarDistribucion).toHaveBeenCalledWith(1, 'Cierre');
  });

  it('should create the next version via ajuste', () => {
    const v1 = version('FIJADO', true);
    serviceSpy.ajusteDistribucion.and.returnValue(of({
      ...v1, id: 2, numero: 2, estado: 'BORRADOR', inmutable: false,
    } as never));
    spyOn(window, 'confirm').and.returnValue(true);
    component.versiones = [v1];
    fixture.detectChanges();
    component.ajustar(v1);
    expect(serviceSpy.ajusteDistribucion).toHaveBeenCalledWith(1);
    expect(component.mensaje).toContain('Versión 2');
  });
});
