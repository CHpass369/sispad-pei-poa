import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { ReformsComponent } from './reforms.component';
import {
  Apertura,
  BudgetService,
  FiscalYear,
  Reforma,
} from './budget.service';
import { MonedaPipe } from './moneda.pipe';

describe('ReformsComponent', () => {
  let component: ReformsComponent;
  let fixture: ComponentFixture<ReformsComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const gestion: FiscalYear = {
    id: '2030', anio: 2030, estado: 'HABILITADA', estado_display: 'Habilitada',
    descripcion: '', anio_inicio_plurianual: null, anio_fin_plurianual: null,
    fecha_apertura: null, fecha_cierre: null, activa: true, gestion_anterior: null,
  };

  const aperturaA: Apertura = {
    id: 1, gestion: '2030', gestion_anio: 2030, version: 1, orden: 0,
    unidad_organizacional: null, unidad_detalle: null, distrito: null,
    distrito_detalle: null, da: null, da_detalle: null, ue: null, ue_detalle: null,
    categoria: null, categoria_detalle: null, proyecto_codigo: '',
    codigo_sisin: '12345678', actividad_codigo: '', denominacion: 'Apertura A',
    tipo_apertura: 'DETAIL', estado: 'ACTIVA', estado_display: 'Activa',
    fuentes: [{
      id: 1, fuente: 'fuente-1',
      fuente_detalle: { codigo: '11', denominacion: 'Tesoro General' },
      organismo: null, organismo_detalle: null, monto: '1000.00',
    }],
    total: '1000.00',
  };

  const aperturaB: Apertura = {
    ...aperturaA, id: 2, denominacion: 'Apertura B', total: '300.00',
  };

  const DISPLAY: Record<string, string> = {
    BORRADOR: 'Borrador',
    EN_REVISION: 'En revisión',
    OBSERVADA: 'Observada',
    APROBADA: 'Aprobada',
    APLICADA: 'Aplicada',
    RECHAZADA: 'Rechazada',
  };

  const reform = (estado: string): Reforma => ({
    id: 1, gestion: '2030', gestion_anio: 2030, tipo: 'TRASPASO',
    tipo_display: 'Traspaso entre aperturas', estado,
    estado_display: DISPLAY[estado], motivo: 'Reasignación', resolucion: '',
    documento: null, version_origen: 1, version_origen_numero: 1,
    version_resultante: null, solicitada_por: 'u1',
    solicitada_por_email: 'admin@techo.test', aprobada_por: null,
    aprobada_por_email: null, fecha_aplicacion: null,
    movimientos: [{
      id: 1, tipo: 'TRASPASO', tipo_display: 'Traspaso',
      apertura_origen: 1,
      apertura_origen_detalle: { id: '1', denominacion: 'Apertura A', codigo_sisin: '12345678' },
      apertura_destino: 2,
      apertura_destino_detalle: { id: '2', denominacion: 'Apertura B', codigo_sisin: '12345678' },
      fuente: 'fuente-1',
      fuente_detalle: { codigo: '11', denominacion: 'Tesoro General' },
      organismo: null, organismo_detalle: null, monto: '500.00',
      saldo_antes: estado === 'APLICADA' ? '1000.00' : null,
      saldo_despues: estado === 'APLICADA' ? '500.00' : null,
      motivo: '',
    }],
    created_at: '',
  });

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'listarReforms', 'listarAperturas', 'opcionesCatalogo',
      'crearReform', 'submitReform', 'observarReform', 'aprobarReform',
      'rechazarReform', 'aplicarReform',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestion] } as never));
    serviceSpy.listarReforms.and.returnValue(of({ count: 1, results: [reform('BORRADOR')] } as never));
    serviceSpy.listarAperturas.and.returnValue(of({ count: 2, results: [aperturaA, aperturaB] } as never));
    serviceSpy.opcionesCatalogo.and.returnValue(of({
      fuentes: [{ id: 'fuente-1', codigo: '11', nombre: 'Tesoro General' }],
      organismos: [], rubros: [], objetos_gasto: [], entidades_transferencia: [],
      distritos: [], direcciones: [], unidades_ejecutoras: [],
      unidades_organizacionales: [],
    } as never));
    serviceSpy.crearReform.and.returnValue(of(reform('BORRADOR') as never));
    serviceSpy.submitReform.and.returnValue(of(reform('EN_REVISION') as never));
    serviceSpy.observarReform.and.returnValue(of(reform('OBSERVADA') as never));
    serviceSpy.aprobarReform.and.returnValue(of(reform('APROBADA') as never));
    serviceSpy.rechazarReform.and.returnValue(of(reform('RECHAZADA') as never));
    serviceSpy.aplicarReform.and.returnValue(of(reform('APLICADA') as never));

    await TestBed.configureTestingModule({
      declarations: [ReformsComponent, MonedaPipe],
      imports: [HttpClientTestingModule, FormsModule],
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(ReformsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load reforms and aperturas on init', () => {
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(serviceSpy.listarReforms).toHaveBeenCalledWith({ gestion: '2030' });
    expect(component.reforms.length).toBe(1);
    expect(component.aperturas.length).toBe(2);
  });

  it('should render the list with estado badges', () => {
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Reformulaciones Presupuestarias');
    expect(rendered.textContent).toContain('Traspaso entre aperturas');
    expect(rendered.textContent).toContain('Borrador');
  });

  it('should show the Enviar button only for BORRADOR/OBSERVADA', () => {
    component.verDetalle(reform('BORRADOR'));
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Enviar a revisión');
    expect(rendered.textContent).not.toContain('Aplicar');

    component.verDetalle(reform('EN_REVISION'));
    fixture.detectChanges();
    expect(rendered.textContent).not.toContain('Enviar a revisión');
    expect(rendered.textContent).toContain('Observar');
    expect(rendered.textContent).toContain('Aprobar');
    expect(rendered.textContent).toContain('Rechazar');
  });

  it('should show the Aplicar button only for APROBADA', () => {
    component.verDetalle(reform('APROBADA'));
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).toContain('Aplicar');
    expect(rendered.textContent).not.toContain('Enviar a revisión');
  });

  it('should show no workflow buttons for terminal states', () => {
    component.verDetalle(reform('APLICADA'));
    fixture.detectChanges();
    const rendered = fixture.nativeElement as HTMLElement;
    expect(rendered.textContent).not.toContain('Aplicar');
    expect(rendered.textContent).not.toContain('Aprobar');
    expect(rendered.textContent).toContain('Bs 1.000,00');
    expect(rendered.textContent).toContain('Bs 500,00');
  });

  it('should submit a BORRADOR reform calling the service', () => {
    component.verDetalle(reform('BORRADOR'));
    component.enviar();
    expect(serviceSpy.submitReform).toHaveBeenCalledWith(1);
    expect(component.mensaje).toContain('enviada a revisión');
  });

  it('should observe with motivo via prompt', () => {
    spyOn(window, 'prompt').and.returnValue('Falta la resolución');
    component.verDetalle(reform('EN_REVISION'));
    component.revisar();
    expect(serviceSpy.observarReform).toHaveBeenCalledWith(
      1, 'Falta la resolución',
    );
  });

  it('should reject with motivo via prompt', () => {
    spyOn(window, 'prompt').and.returnValue('No corresponde');
    component.verDetalle(reform('EN_REVISION'));
    component.rechazar();
    expect(serviceSpy.rechazarReform).toHaveBeenCalledWith(1, 'No corresponde');
  });

  it('should create a reform with movements', () => {
    component.gestionSeleccionada = '2030';
    component.abrirFormulario();
    component.nueva.tipo = 'TRASPASO';
    component.nueva.motivo = 'Reasignación entre aperturas';
    component.filasMovimientos = [{
      tipo: 'TRASPASO', apertura_origen: 1, apertura_destino: 2,
      fuente: 'fuente-1', organismo: null, monto: 500,
    }];
    component.guardarReform();
    expect(serviceSpy.crearReform).toHaveBeenCalledWith(jasmine.objectContaining({
      gestion: '2030',
      tipo: 'TRASPASO',
      motivo: 'Reasignación entre aperturas',
      movimientos: [jasmine.objectContaining({
        tipo: 'TRASPASO', apertura_origen: 1, apertura_destino: 2,
        fuente: 'fuente-1', monto: 500,
      })],
    }));
    expect(component.mensaje).toContain('BORRADOR');
  });

  it('should reject a movement without monto before calling the service', () => {
    component.gestionSeleccionada = '2030';
    component.abrirFormulario();
    component.filasMovimientos = [{
      tipo: 'TRASPASO', apertura_origen: 1, apertura_destino: 2,
      fuente: 'fuente-1', organismo: null, monto: null,
    }];
    component.guardarReform();
    expect(serviceSpy.crearReform).not.toHaveBeenCalled();
    expect(component.error).toContain('fuente y monto');
  });

  it('should show BUDGET_EXCEEDED error when apply fails', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    serviceSpy.aplicarReform.and.returnValue(throwError(() => ({
      error: { detail: ['El monto solicitado supera el saldo disponible.'] },
      code: 'BUDGET_EXCEEDED',
      details: { requested: '2000.00', available: '1000.00', difference: '1000.00' },
    })));
    component.verDetalle(reform('APROBADA'));
    component.aplicar();
    expect(serviceSpy.aplicarReform).toHaveBeenCalledWith(1);
    expect(component.error).toContain('supera el saldo disponible');
    expect(component.mensaje).toBe('');
  });

  it('should apply a reform with confirm', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    component.verDetalle(reform('APROBADA'));
    component.aplicar();
    expect(serviceSpy.aplicarReform).toHaveBeenCalledWith(1);
    expect(component.mensaje).toContain('aplicada');
  });
});
