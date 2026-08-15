import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { ImportsComponent } from './imports.component';
import { BudgetImport, BudgetService, FiscalYear } from './budget.service';

describe('ImportsComponent', () => {
  let component: ImportsComponent;
  let fixture: ComponentFixture<ImportsComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const gestion: FiscalYear = {
    id: '2030', anio: 2030, estado: 'HABILITADA', estado_display: 'Habilitada',
    descripcion: '', anio_inicio_plurianual: null, anio_fin_plurianual: null,
    fecha_apertura: null, fecha_cierre: null, activa: true, gestion_anterior: null,
  };

  const importacionBase = {
    id: 1, gestion: '2030', gestion_anio: 2030,
    perfil: 'SISPOA_GASTOS_HISTORICO', perfil_display: 'GASTOS histórico',
    filename: 'gastos.xlsx', mime_type: 'application/vnd...', size: 1000,
    sha256: 'a'.repeat(64), hoja_seleccionada: 'gastos',
    mapeo_json: {
      hoja: 'gastos',
      columnas: { 'CT': 'ct', 'DENOMINACIÓN DEL PROYECTO': 'denominacion' },
      fuentes: { ct: '41', re: '20', ore: '20', idh: '41', tgn: '11' },
    },
    estado: 'STAGING', estado_display: 'En staging', tipo_importacion: 'GASTOS',
    storage_path: 'budget/imports/gastos.xlsx', conteos: {}, created_at: '',
  } as BudgetImport;

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'listarImportaciones', 'subirImportacion', 'hojasImportacion',
      'mapearImportacion', 'validarImportacion', 'erroresImportacion',
      'aplicarImportacion',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [gestion] } as never));
    serviceSpy.listarImportaciones.and.returnValue(of({ count: 0, results: [] } as never));
    serviceSpy.subirImportacion.and.returnValue(of({ ...importacionBase } as never));
    serviceSpy.hojasImportacion.and.returnValue(of({ hojas: ['gastos', 'resumen'] } as never));
    serviceSpy.mapearImportacion.and.returnValue(of({ ...importacionBase } as never));
    serviceSpy.validarImportacion.and.returnValue(of({
      ...importacionBase,
      estado: 'VALIDADO',
      conteos: { INFO: 0, WARNING: 0, ERROR: 0, CRITICAL: 0 },
    } as never));
    serviceSpy.erroresImportacion.and.returnValue(of([] as never));
    serviceSpy.aplicarImportacion.and.returnValue(of({
      ...importacionBase,
      estado: 'APLICADO',
      resultado: { aperturas_creadas: 2, total_importado: '1100.00' },
    } as never));

    await TestBed.configureTestingModule({
      declarations: [ImportsComponent],
      imports: [HttpClientTestingModule, FormsModule],
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(ImportsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load fiscal years on init', () => {
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(component.gestiones.length).toBe(1);
    expect(component.gestionSeleccionada).toBe('2030');
  });

  it('should move through wizard steps on upload', () => {
    component.archivo = new File(['x'], 'gastos.xlsx');
    component.subir();
    expect(serviceSpy.subirImportacion).toHaveBeenCalled();
    expect(component.paso).toBe(2);
    expect(component.hojas).toEqual(['gastos', 'resumen']);
    expect(component.filasMapeo.length).toBe(2);
  });

  it('should validate and show no critical errors', () => {
    component.importacion = { ...importacionBase } as BudgetImport;
    component.validar();
    expect(serviceSpy.validarImportacion).toHaveBeenCalledWith(1);
    expect(component.importacion?.estado).toBe('VALIDADO');
    expect(component.bloques).toBeFalse();
    expect(serviceSpy.erroresImportacion).toHaveBeenCalledWith(1);
  });

  it('should apply when valid and report result', () => {
    component.importacion = {
      ...importacionBase, estado: 'VALIDADO',
      conteos: { INFO: 0, WARNING: 0, ERROR: 0, CRITICAL: 0 },
    } as BudgetImport;
    component.aplicar();
    expect(serviceSpy.aplicarImportacion).toHaveBeenCalledWith(1);
    expect(component.importacion?.estado).toBe('APLICADO');
    expect(component.resultado).toContain('2 aperturas BORRADOR');
  });

  it('should block apply when critical errors remain', () => {
    serviceSpy.aplicarImportacion.and.returnValue(throwError(() => ({
      error: { error: { detail: ['No se puede aplicar la importación: hay 1 error(es) crítico(s) sin resolver.'] } },
    })));
    component.importacion = {
      ...importacionBase,
      conteos: { INFO: 0, WARNING: 0, ERROR: 1, CRITICAL: 1 },
    } as BudgetImport;
    component.aplicar();
    expect(component.error).toContain('crítico');
    expect(component.importacion?.estado).toBe('STAGING');
    expect(serviceSpy.aplicarImportacion).toHaveBeenCalled();
  });

  it('should flag bloques with critical counts', () => {
    component.importacion = importacionBase;
    component.conteos = { INFO: 0, WARNING: 0, ERROR: 0, CRITICAL: 1 };
    expect(component.bloques).toBeTrue();
  });

  it('should reset wizard state', () => {
    component.reiniciar();
    expect(component.paso).toBe(1);
    expect(component.importacion).toBeNull();
    expect(component.error).toBe('');
  });
});
