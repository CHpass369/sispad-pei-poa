import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import {
  BudgetService,
  RecursoTecho,
  Composition,
  TechoDirectivo,
} from './budget.service';
import { PermissionsService } from '../../../core/services/permissions.service';
import { DirectiveCeilingComponent } from './directive-ceiling.component';
import { MonedaPipe } from './moneda.pipe';

const composicionMock: Composition = {
  gestion: 2027,
  version: 1,
  estado: 'BORRADOR',
  sigep: '1000000.00',
  municipales: '250000.00',
  saldos: '0.00',
  otros: '0.00',
  gastos_obligatorios: '200000.00',
  reservas: '0.00',
  techo_bruto: '1250000.00',
  techo_distribuible: '1050000.00',
  por_fuente: [{ fuente: '11', denominacion: 'Tesoro General', monto: '1000000.00' }],
};

const recursoMock: RecursoTecho = {
  id: 1,
  version: 1,
  origen: 'SIGEP',
  origen_display: 'SIGEP',
  rubro: null,
  rubro_detalle: null,
  fuente: null,
  fuente_detalle: null,
  organismo: null,
  organismo_detalle: null,
  entidad_otorgante: null,
  entidad_detalle: null,
  concepto: 'Coparticipación tributaria',
  monto: '1000000.00',
  documento: null,
  documento_nombre: null,
};

const techoMock: TechoDirectivo = {
  id: 7,
  gestion: 'g1',
  gestion_anio: 2027,
  estado: 'BORRADOR',
  estado_display: 'Borrador',
  version_actual: 1,
  version: {
    id: 1,
    numero: 1,
    estado: 'BORRADOR',
    estado_display: 'Borrador',
    hash: '',
    fecha_fijacion: null,
    fijado_por: null,
    fijado_por_email: null,
    observaciones: '',
    inmutable: false,
    recursos: [recursoMock],
    gastos_obligatorios: [],
  },
  composicion: composicionMock,
  created_at: '2026-08-14T12:00:00Z',
  updated_at: '2026-08-14T12:00:00Z',
};

describe('DirectiveCeilingComponent', () => {
  let component: DirectiveCeilingComponent;
  let fixture: ComponentFixture<DirectiveCeilingComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listarTechos', 'listar', 'crearTecho', 'obtenerTecho',
      'enviarRevision', 'observarTecho', 'aprobarTecho', 'fijarTecho',
      'crearRecurso', 'eliminarRecurso', 'crearGasto', 'eliminarGasto',
      'listarDocumentos', 'subirDocumento',
    ]);
    serviceSpy.listarTechos.and.returnValue(of({ count: 1, results: [techoMock] }));
    serviceSpy.listar.and.returnValue(of({ count: 0, results: [] }));
    serviceSpy.obtenerTecho.and.returnValue(of(techoMock));
    serviceSpy.enviarRevision.and.returnValue(of(techoMock));
    serviceSpy.observarTecho.and.returnValue(of(techoMock));
    serviceSpy.aprobarTecho.and.returnValue(of(techoMock));
    serviceSpy.fijarTecho.and.returnValue(of(techoMock));
    serviceSpy.crearRecurso.and.returnValue(of(recursoMock));
    serviceSpy.crearGasto.and.returnValue(of({} as never));
    serviceSpy.eliminarRecurso.and.returnValue(of());
    serviceSpy.eliminarGasto.and.returnValue(of());
    serviceSpy.listarDocumentos.and.returnValue(of({ count: 0, results: [] }));

    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);
    permissionsSpy.hasAnyCapability.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [DirectiveCeilingComponent, MonedaPipe],
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: BudgetService, useValue: serviceSpy },
        { provide: PermissionsService, useValue: permissionsSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DirectiveCeilingComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list ceilings and select the first one on init', () => {
    fixture.detectChanges();
    expect(serviceSpy.listarTechos).toHaveBeenCalled();
    expect(component.techos.length).toBe(1);
    expect(serviceSpy.obtenerTecho).toHaveBeenCalledWith(7);
  });

  it('should render composition cards with formatted amounts', () => {
    fixture.detectChanges();
    const cards = fixture.nativeElement.querySelectorAll('.comp-card');
    expect(cards.length).toBeGreaterThanOrEqual(7);
    const textos = Array.from(cards).map(
      (c: HTMLElement) => c.textContent?.trim() ?? '',
    );
    expect(textos.some((t) => t.includes('SIGEP'))).toBeTrue();
    expect(textos.some((t) => t.includes('Bs 1.000.000,00'))).toBeTrue();
    expect(textos.some((t) => t.includes('Techo distribuible'))).toBeTrue();
    expect(textos.some((t) => t.includes('Bs 1.050.000,00'))).toBeTrue();
  });

  it('should render resources table with origen and monto', () => {
    fixture.detectChanges();
    const fila = fixture.nativeElement.querySelector('tbody tr');
    expect(fila).toBeTruthy();
    expect(fila.textContent).toContain('Coparticipación tributaria');
    expect(fila.textContent).toContain('Bs 1.000.000,00');
  });

  it('should show submit button in BORRADOR and hide approve/freeze', () => {
    fixture.detectChanges();
    const botones = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ).map((b: HTMLButtonElement) => b.textContent?.trim());
    expect(botones).toContain('Enviar a revisión');
    expect(botones).not.toContain('Aprobar');
    expect(botones).not.toContain('Fijar techo');
  });

  it('should show approve/observe in EN_REVISION and freeze in APROBADO', () => {
    const enRevision: TechoDirectivo = {
      ...techoMock,
      estado: 'EN_REVISION',
      estado_display: 'En revisión',
      version: { ...techoMock.version!, estado: 'EN_REVISION', estado_display: 'En revisión' },
    };
    serviceSpy.obtenerTecho.and.returnValue(of(enRevision));
    fixture.detectChanges();
    let botones = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ).map((b: HTMLButtonElement) => b.textContent?.trim());
    expect(botones).toContain('Aprobar');
    expect(botones).toContain('Observar');

    const aprobado: TechoDirectivo = {
      ...enRevision,
      estado: 'APROBADO',
      estado_display: 'Aprobado',
      version: { ...techoMock.version!, estado: 'APROBADO', estado_display: 'Aprobado' },
    };
    serviceSpy.obtenerTecho.and.returnValue(of(aprobado));
    component.refrescar();
    fixture.detectChanges();
    botones = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ).map((b: HTMLButtonElement) => b.textContent?.trim());
    expect(botones).toContain('Fijar techo');
  });

  it('should call fijarTecho and refresh on freeze', () => {
    const aprobado: TechoDirectivo = {
      ...techoMock,
      estado: 'APROBADO',
      estado_display: 'Aprobado',
      version: { ...techoMock.version!, estado: 'APROBADO', estado_display: 'Aprobado' },
    };
    serviceSpy.obtenerTecho.and.returnValue(of(aprobado));
    fixture.detectChanges();
    component.fijar();
    expect(serviceSpy.fijarTecho).toHaveBeenCalledWith(7);
    expect(serviceSpy.obtenerTecho).toHaveBeenCalledWith(7);
  });

  it('should hide edit forms without manage capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    fixture.detectChanges();
    expect(component.puedeGestionar).toBeFalse();
    const botones = fixture.nativeElement.querySelectorAll('button');
    expect(
      Array.from(botones).some((b: HTMLButtonElement) =>
        b.textContent?.includes('Registrar recurso'),
      ),
    ).toBeFalse();
  });

  it('should create ceiling and reload the list', () => {
    serviceSpy.crearTecho.and.returnValue(of(techoMock));
    fixture.detectChanges();
    component.gestionNueva = 'g1';
    component.crear();
    expect(serviceSpy.crearTecho).toHaveBeenCalledWith({ gestion: 'g1' });
    expect(serviceSpy.listarTechos).toHaveBeenCalled();
  });

  it('should register a resource and refresh detail', () => {
    fixture.detectChanges();
    component.formRecurso = { origen: 'SIGEP', concepto: 'CT', monto: 5000 };
    component.registrarRecurso();
    expect(serviceSpy.crearRecurso).toHaveBeenCalledWith({
      version: 1,
      origen: 'SIGEP',
      concepto: 'CT',
      monto: 5000,
    });
    expect(serviceSpy.obtenerTecho).toHaveBeenCalledWith(7);
  });
});
