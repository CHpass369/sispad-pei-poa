import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';
import { BandejaTareasComponent } from './bandeja-tareas.component';
import { WorkflowV2Service } from './workflow-v2.service';
import { WorkflowInstanceV2, WorkflowTaskV2 } from './models/workflow-v2.model';

const base = environment.apiUrlV2 + '/platform';

const tarea1: WorkflowTaskV2 = {
  id: 'task-1',
  instancia: 'inst-1',
  definicion: 'APROBACION_PEI',
  paso_nombre: 'Revisión técnica',
  paso: 'step-1',
  asignado_a: 'user-1',
  estado: 'pendiente',
  creado_en: '2026-08-15T10:00:00Z',
  completado_en: null,
};

const tarea2: WorkflowTaskV2 = {
  id: 'task-2',
  instancia: 'inst-2',
  definicion: 'APROBACION_POA',
  paso_nombre: 'Aprobación final',
  paso: 'step-2',
  asignado_a: 'user-1',
  estado: 'en_curso',
  creado_en: '2026-08-15T11:00:00Z',
  completado_en: null,
};

const instanciaMock: WorkflowInstanceV2 = {
  id: 'inst-1',
  definicion: 'def-1',
  definicion_codigo: 'APROBACION_PEI',
  entidad_tipo: 'VersionInstrumento',
  entidad_id: 'ent-1',
  estado_actual: 'en_revision',
  cerrado: false,
  iniciado_en: '2026-08-15T10:00:00Z',
  tarea_actual: {
    id: 'task-1',
    paso: 'Revisión técnica',
    estado: 'pendiente',
    asignado_a: 'user-1',
  },
};

describe('BandejaTareasComponent', () => {
  let component: BandejaTareasComponent;
  let fixture: ComponentFixture<BandejaTareasComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BandejaTareasComponent],
      imports: [CommonModule, FormsModule, HttpClientTestingModule],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(BandejaTareasComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    httpMock.verify();
  });

  function flushTareas(): void {
    const req = httpMock.expectOne(`${base}/workflow-tareas/?mias=true`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 2, results: [tarea1, tarea2] });
  }

  it('crea el componente y carga mis tareas', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    expect(component.tareas.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('renderiza filas con definicion, paso y estado', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('APROBACION_PEI');
    expect(texto).toContain('Revisión técnica');
    expect(texto).toContain('Pendiente');
    expect(texto).toContain('APROBACION_POA');
    expect(texto).toContain('En curso');
  });

  it('filtra por estado client-side', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.filtroEstado = 'en_curso';
    component.aplicarFiltros();
    fixture.detectChanges();

    expect(component.filtradas.length).toBe(1);
    expect(component.filtradas[0].id).toBe('task-2');
    const texto = fixture.nativeElement.textContent;
    expect(texto).not.toContain('APROBACION_PEI');
    expect(texto).toContain('APROBACION_POA');
  });

  it('busca por texto client-side', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.busqueda = 'Revisión técnica';
    component.aplicarFiltros();
    fixture.detectChanges();

    expect(component.filtradas.length).toBe(1);
    expect(component.filtradas[0].id).toBe('task-1');
  });

  it('aprobar llama POST a la URL correcta con body y recarga', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.aprobar(tarea1);

    const req = httpMock.expectOne(`${base}/workflow-instancias/inst-1/aprobar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ comentario: '' });
    req.flush(instanciaMock);

    flushTareas();
    expect(component.mensaje).toBe('Instancia aprobada');
  });

  it('observar con prompt mockeado llama POST observar y recarga', () => {
    spyOn(window, 'prompt').and.returnValue('Corregir montos');
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.observar(tarea1);

    const req = httpMock.expectOne(`${base}/workflow-instancias/inst-1/observar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ texto: 'Corregir montos', severidad: 'moderada' });
    req.flush(instanciaMock);

    flushTareas();
    expect(component.mensaje).toBe('Observación registrada');
  });

  it('delegar llama POST delegar con el usuario indicado', () => {
    spyOn(window, 'prompt').and.returnValue('user-2');
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.delegar(tarea1);

    const req = httpMock.expectOne(`${base}/workflow-instancias/inst-1/delegar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ delegado_a: 'user-2', motivo: '' });
    req.flush(instanciaMock);

    flushTareas();
    expect(component.mensaje).toBe('Tarea delegada');
  });

  it('avanzar llama POST avanzar y recarga', () => {
    fixture.detectChanges();
    flushTareas();
    fixture.detectChanges();

    component.avanzar(tarea2);

    const req = httpMock.expectOne(`${base}/workflow-instancias/inst-2/avanzar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ comentario: '' });
    req.flush(instanciaMock);

    flushTareas();
    expect(component.mensaje).toBe('Instancia avanzada');
  });

  it('error al cargar muestra mensaje', () => {
    fixture.detectChanges();

    const req = httpMock.expectOne(`${base}/workflow-tareas/?mias=true`);
    req.flush({ detail: 'Error interno' }, { status: 500, statusText: 'Error' });
    fixture.detectChanges();

    expect(component.cargando).toBeFalse();
    expect(component.error).toBe('Error al cargar las tareas');
    expect(fixture.nativeElement.textContent).toContain('Error al cargar las tareas');
  });
});
