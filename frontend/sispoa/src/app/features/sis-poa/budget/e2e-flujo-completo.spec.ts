import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
  TestRequest,
} from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { PermissionsService } from '../../../core/services/permissions.service';
import {
  Allocation,
  CatalogoOpciones,
  CeilingResource,
  Composition,
  DirectiveCeiling,
  DirectiveCeilingVersion,
  DistributionSummary,
  DistributionVersion,
  FiscalYear,
  MandatoryExpense,
  ProgrammaticCategory,
  Reserve,
  ValidacionDistribucion,
} from './budget.service';
import { FiscalYearComponent } from './fiscal-year.component';
import { DirectiveCeilingComponent } from './directive-ceiling.component';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';
import { DistributionComponent } from './distribution.component';
import { MonedaPipe } from './moneda.pipe';

/**
 * E2E del ciclo presupuestario completo por UI (Fase 12, §135).
 *
 * Espejo del `FlujoCompletoE2ETests` del backend (backend/apps/budget/tests.py),
 * pero del lado Angular: componentes reales montados con TestBed + servicio
 * real (`BudgetService`) interceptado con `HttpClientTestingModule`.
 * Las respuestas simuladas replican los serializers DRF (montos como string).
 */
describe('E2E UI: flujo completo presupuestario', () => {
  const BASE = '/api/v2/sis-poa/budget';

  // -- Fixtures: gestión fiscal (2027) ---------------------------------------

  const gestion2027: FiscalYear = {
    id: '2027',
    anio: 2027,
    estado: 'preparacion',
    estado_display: 'Preparación',
    descripcion: '',
    anio_inicio_plurianual: null,
    anio_fin_plurianual: null,
    fecha_apertura: null,
    fecha_cierre: null,
    activa: false,
    gestion_anterior: null,
  };

  const gestionHabilitada: FiscalYear = {
    ...gestion2027,
    estado: 'HABILITADA',
    estado_display: 'Habilitada',
    fecha_apertura: '2026-01-02',
    activa: true,
  };

  // -- Fixtures: techo directivo (Fase 2) ------------------------------------

  const fuenteDetalle = { id: '41', codigo: '41', denominacion: 'Coparticipación tributaria' };
  const organismoDetalle = { id: '113', codigo: '113', denominacion: 'Organismo financiador SIGEP' };

  /** Composición con los montos reales del reporte SIGEP 2027. */
  const composicionMock = (
    estado: string | null,
    gastosObligatorios: string,
    techoDistribuible: string,
  ): Composition => ({
    gestion: 2027,
    version: 1,
    estado,
    sigep: '245290497.00',
    municipales: '0.00',
    saldos: '0.00',
    otros: '0.00',
    gastos_obligatorios: gastosObligatorios,
    reservas: '0.00',
    techo_bruto: '245290497.00',
    techo_distribuible: techoDistribuible,
    por_fuente: [
      { fuente: '41', denominacion: 'Coparticipación tributaria', monto: '245290497.00' },
    ],
  });

  const recursoSIGEP: CeilingResource = {
    id: 1,
    version: 1,
    origen: 'SIGEP',
    origen_display: 'SIGEP',
    rubro: null,
    rubro_detalle: null,
    fuente: '41',
    fuente_detalle: fuenteDetalle,
    organismo: '113',
    organismo_detalle: organismoDetalle,
    entidad_otorgante: null,
    entidad_detalle: null,
    concepto: 'CT',
    monto: '245290497.00',
    documento: null,
    documento_nombre: null,
  };

  const gastoObligatorio: MandatoryExpense = {
    id: 1,
    version: 1,
    da: null,
    da_detalle: null,
    ue: null,
    ue_detalle: null,
    programa: '',
    actividad: '',
    denominacion: 'Gastos obligatorios',
    fuente: '41',
    fuente_detalle: fuenteDetalle,
    organismo: null,
    organismo_detalle: null,
    objeto_gasto: null,
    objeto_gasto_detalle: null,
    entidad_transferencia: '',
    monto: '6464396.00',
    documento: null,
    documento_nombre: null,
  };

  const versionTecho = (
    estado: string,
    inmutable: boolean,
    recursos: CeilingResource[],
    gastos: MandatoryExpense[],
  ): DirectiveCeilingVersion => ({
    id: 1,
    numero: 1,
    estado,
    estado_display: estado,
    hash: inmutable ? 'a'.repeat(64) : '',
    fecha_fijacion: inmutable ? '2026-08-15T12:00:00Z' : null,
    fijado_por: inmutable ? 1 : null,
    fijado_por_email: inmutable ? 'admin@e2e.test' : null,
    observaciones: '',
    inmutable,
    recursos,
    gastos_obligatorios: gastos,
  });

  const techoMock = (
    estado: string,
    version: DirectiveCeilingVersion,
    composicion: Composition,
  ): DirectiveCeiling => ({
    id: 7,
    gestion: '2027',
    gestion_anio: 2027,
    estado,
    estado_display: estado,
    version_actual: 1,
    version,
    composicion,
    created_at: '2026-08-14T12:00:00Z',
    updated_at: '2026-08-14T12:00:00Z',
  });

  // -- Fixtures: distribución presupuestaria (Fase 4 / 7) --------------------

  const versionDist = (estado: string, inmutable = false): DistributionVersion => ({
    id: 1,
    gestion: '2027',
    gestion_anio: 2027,
    numero: 1,
    estado,
    estado_display: estado,
    hash: inmutable ? 'a'.repeat(64) : '',
    fecha_fijacion: null,
    fijado_por: null,
    fijado_por_email: null,
    observaciones: '',
    inmutable,
  });

  const resumenDist = (
    distribuido: string,
    reservado: string,
    disponible: string,
    porcentaje: number,
    aperturasCount: number,
  ): DistributionSummary => ({
    gestion: 2027,
    techo_distribuible: '238826101.00',
    distribuido,
    reservado,
    disponible,
    porcentaje,
    aperturas_count: aperturasCount,
    por_fuente: [
      {
        fuente_id: '41',
        denominacion: 'Coparticipación tributaria',
        techo: '245290497.00',
        distribuido,
        reservado,
        disponible,
        porcentaje,
      },
    ],
  });

  const aperturaMock: Allocation = {
    id: 1,
    gestion: '2027',
    gestion_anio: 2027,
    version: 1,
    orden: 1,
    unidad_organizacional: null,
    unidad_detalle: null,
    distrito: null,
    distrito_detalle: null,
    da: null,
    da_detalle: null,
    ue: null,
    ue_detalle: null,
    categoria: null,
    categoria_detalle: null,
    proyecto_codigo: '',
    codigo_sisin: '12345678',
    actividad_codigo: '',
    denominacion: 'Apertura principal',
    tipo_apertura: 'DETAIL',
    estado: 'ACTIVA',
    estado_display: 'Activa',
    fuentes: [
      {
        id: 1,
        fuente: '41',
        fuente_detalle: fuenteDetalle,
        organismo: '113',
        organismo_detalle: organismoDetalle,
        monto: '1000000.00',
      },
    ],
    total: '1000000.00',
  };

  const reservaMock: Reserve = {
    id: 1,
    gestion: '2027',
    gestion_anio: 2027,
    version: 1,
    fuente: '41',
    fuente_detalle: fuenteDetalle,
    organismo: '113',
    organismo_detalle: organismoDetalle,
    tipo: 'DISTRITAL',
    tipo_display: 'Distrital',
    monto: '244290497.00',
    motivo: 'Reserva por el resto del techo distribuible',
    estado: 'ACTIVA',
    estado_display: 'Activa',
  };

  const validacionOk: ValidacionDistribucion = {
    valida: true,
    diferencias: [
      {
        fuente_id: '41',
        denominacion: 'Coparticipación tributaria',
        techo: '245290497.00',
        distribuido: '1000000.00',
        reservado: '244290497.00',
        diferencia: '0.00',
      },
    ],
  };

  const opcionesCatalogo: CatalogoOpciones = {
    fuentes: [fuenteDetalle],
    organismos: [organismoDetalle],
    rubros: [],
    objetos_gasto: [],
    entidades_transferencia: [],
    distritos: [],
    direcciones: [],
    unidades_ejecutoras: [],
    unidades_organizacionales: [],
  };

  // -- Fixtures: categorías programáticas (Fase 3) ---------------------------

  const catPrograma: ProgrammaticCategory = {
    id: 1,
    gestion: 2027,
    codigo: '09',
    denominacion: 'Servicios generales',
    nivel: 'PROGRAMA',
    nivel_display: 'Programa',
    parent: null,
    estado: 'ACTIVA',
    codigo_compuesto: '09',
  };

  const catSubprograma: ProgrammaticCategory = {
    id: 2,
    gestion: 2027,
    codigo: '010',
    denominacion: 'Servicios administrativos',
    nivel: 'SUBPROGRAMA',
    nivel_display: 'Subprograma',
    parent: 1,
    estado: 'ACTIVA',
    codigo_compuesto: '09.010',
  };

  // -- Ayudantes -------------------------------------------------------------

  let httpMock: HttpTestingController;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;

  /** Flush de una única petición pendiente que contiene `urlPart`. */
  function flush(urlPart: string, body: unknown, method = 'GET'): TestRequest {
    const req = httpMock.expectOne(
      (r) => r.method === method && r.url.includes(urlPart),
    );
    req.flush(body);
    return req;
  }

  /** Clic sobre un botón del fixture actual buscado por su texto visible. */
  function clickBoton(
    fixture: ComponentFixture<unknown>,
    texto: string,
  ): HTMLButtonElement {
    const el = fixture.nativeElement as HTMLElement;
    const botones = Array.from(el.querySelectorAll('button'));
    const btn = botones.find(
      (b) => (b.textContent ?? '').trim().includes(texto),
    ) as HTMLButtonElement | undefined;
    expect(btn).withContext(`botón "${texto}" visible`).toBeTruthy();
    btn!.click();
    fixture.detectChanges();
    return btn!;
  }

  function botonesTexto(fixture: ComponentFixture<unknown>): string[] {
    const el = fixture.nativeElement as HTMLElement;
    return Array.from(el.querySelectorAll('button')).map(
      (b: HTMLButtonElement) => (b.textContent ?? '').trim(),
    );
  }

  beforeEach(async () => {
    permissionsSpy = jasmine.createSpyObj('PermissionsService', [
      'hasAnyCapability',
    ]);
    permissionsSpy.hasAnyCapability.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [
        FiscalYearComponent,
        DirectiveCeilingComponent,
        ProgrammaticCategoriesComponent,
        DistributionComponent,
        MonedaPipe,
      ],
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      providers: [{ provide: PermissionsService, useValue: permissionsSpy }],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('recorre el ciclo presupuestario completo con componentes y servicio reales', () => {
    // ===================================================================
    // 1. Gestión fiscal: listar y habilitar la gestión 2027
    // ===================================================================
    const fixtureFiscal = TestBed.createComponent(FiscalYearComponent);
    const fiscal = fixtureFiscal.componentInstance;
    fixtureFiscal.detectChanges(); // ngOnInit -> listar()

    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestion2027] });
    fixtureFiscal.detectChanges();

    expect(fiscal.gestiones.length).toBe(1);
    expect(
      botonesTexto(fixtureFiscal).some((t) => t === 'Habilitar'),
    ).withContext('gestión en preparación muestra el botón Habilitar').toBeTrue();

    clickBoton(fixtureFiscal, 'Habilitar');

    const reqEnable = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/fiscal-years/2027/enable/'),
    );
    expect(reqEnable.request.body).toEqual({});
    reqEnable.flush(gestionHabilitada);

    // El habilitar recarga la lista: la gestión vuelve como HABILITADA.
    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestionHabilitada] });
    fixtureFiscal.detectChanges();

    expect(fiscal.gestiones[0].estado).toBe('HABILITADA');
    expect(fiscal.mensaje).toContain('Gestión 2027 habilitada');
    const htmlFiscal = fixtureFiscal.nativeElement as HTMLElement;
    expect(htmlFiscal.textContent).toContain('Habilitada');
    expect(
      botonesTexto(fixtureFiscal).some((t) => t === 'Habilitar'),
    ).withContext('gestión habilitada ya no muestra Habilitar').toBeFalse();
    fixtureFiscal.destroy();
    httpMock.verify();

    // ===================================================================
    // 2. Techo directivo: crear, recurso SIGEP, gasto obligatorio,
    //    composición exacta y submit → approve → freeze
    // ===================================================================
    const fixtureTecho = TestBed.createComponent(DirectiveCeilingComponent);
    const techo = fixtureTecho.componentInstance;
    fixtureTecho.detectChanges(); // cargar(): listarTechos + listar

    // Sin techos todavía: lista vacía + gestiones cargadas.
    flush(`${BASE}/directive-ceilings/`, { count: 0, results: [] });
    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestionHabilitada] });
    fixtureTecho.detectChanges();

    expect(techo.gestiones.length).toBe(1);

    // Crear el techo directivo para la gestión 2027 (BORRADOR v1).
    techo.gestionNueva = '2027';
    clickBoton(fixtureTecho, 'Nuevo techo');

    const reqCrearTecho = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/directive-ceilings/'),
    );
    expect(reqCrearTecho.request.body).toEqual({ gestion: '2027' });
    reqCrearTecho.flush(
      techoMock(
        'BORRADOR',
        versionTecho('BORRADOR', false, [], []),
        composicionMock('BORRADOR', '0.00', '245290497.00'),
      ),
    );

    // La creación recarga la lista; con techos se auto-selecciona el primero
    // (detalle + documentos).
    flush(`${BASE}/directive-ceilings/`, {
      count: 1,
      results: [
        techoMock(
          'BORRADOR',
          versionTecho('BORRADOR', false, [], []),
          composicionMock('BORRADOR', '0.00', '245290497.00'),
        ),
      ],
    });
    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestionHabilitada] });
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'BORRADOR',
        versionTecho('BORRADOR', false, [], []),
        composicionMock('BORRADOR', '0.00', '245290497.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    expect(techo.mensaje).toContain('Techo directivo creado');
    expect(techo.seleccion?.id).toBe(7);
    expect(techo.composicion?.sigep).toBe('245290497.00');

    // Registrar el recurso SIGEP (fuente 41 / organismo 113 / concepto CT).
    techo.formRecurso = { origen: 'SIGEP', concepto: 'CT', monto: 245290497.00 };
    clickBoton(fixtureTecho, 'Registrar recurso');

    const reqRecurso = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/resources/'),
    );
    expect(reqRecurso.request.body).toEqual({
      version: 1,
      origen: 'SIGEP',
      concepto: 'CT',
      monto: 245290497.00,
    });
    reqRecurso.flush(recursoSIGEP);

    // Refrescar el detalle con el recurso registrado + documentos.
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'BORRADOR',
        versionTecho('BORRADOR', false, [recursoSIGEP], []),
        composicionMock('BORRADOR', '0.00', '245290497.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    expect(techo.recursos.length).toBe(1);
    expect(techo.recursos[0].monto).toBe('245290497.00');
    expect(techo.mensaje).toContain('Recurso registrado');

    // Registrar el gasto obligatorio (6.464.396,00).
    techo.formGasto = {
      programa: '',
      actividad: '',
      denominacion: 'Gastos obligatorios',
      monto: 6464396.00,
    };
    clickBoton(fixtureTecho, 'Registrar gasto');

    const reqGasto = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/mandatory-expenses/'),
    );
    expect(reqGasto.request.body).toEqual({
      version: 1,
      programa: '',
      actividad: '',
      denominacion: 'Gastos obligatorios',
      monto: 6464396.00,
    });
    reqGasto.flush(gastoObligatorio);

    // Detalle con la composición final del reporte SIGEP 2027.
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'BORRADOR',
        versionTecho('BORRADOR', false, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('BORRADOR', '6464396.00', '238826101.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    // Composición renderizada con montos exactos (SIGEP 245.290.497,00;
    // obligatorios 6.464.396,00; bruto 245.290.497,00; distribuible
    // 238.826.101,00).
    const cards = Array.from(
      (fixtureTecho.nativeElement as HTMLElement).querySelectorAll('.comp-card'),
    ).map((c) => (c.textContent ?? '').trim());
    expect(
      cards.some((t) => t.includes('SIGEP') && t.includes('Bs 245.290.497,00')),
    ).withContext('card SIGEP').toBeTrue();
    expect(
      cards.some(
        (t) =>
          t.includes('Gastos obligatorios') && t.includes('Bs 6.464.396,00'),
      ),
    ).withContext('card Gastos obligatorios').toBeTrue();
    expect(
      cards.some(
        (t) => t.includes('Techo bruto') && t.includes('Bs 245.290.497,00'),
      ),
    ).withContext('card Techo bruto').toBeTrue();
    expect(
      cards.some(
        (t) =>
          t.includes('Techo distribuible') && t.includes('Bs 238.826.101,00'),
      ),
    ).withContext('card Techo distribuible').toBeTrue();

    // La tabla de recursos muestra concepto CT y monto SIGEP.
    const filaRecurso = (fixtureTecho.nativeElement as HTMLElement).querySelector(
      '.seccion .data-table tbody tr',
    ) as HTMLElement | null;
    expect(filaRecurso?.textContent).toContain('CT');
    expect(filaRecurso?.textContent).toContain('Bs 245.290.497,00');

    // BORRADOR: solo se puede enviar a revisión.
    expect(botonesTexto(fixtureTecho)).toContain('Enviar a revisión');
    expect(botonesTexto(fixtureTecho)).not.toContain('Aprobar');
    expect(botonesTexto(fixtureTecho)).not.toContain('Fijar techo');

    // Enviar a revisión (BORRADOR → EN_REVISION).
    clickBoton(fixtureTecho, 'Enviar a revisión');

    const reqSubmit = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/directive-ceilings/7/submit/'),
    );
    reqSubmit.flush(
      techoMock(
        'EN_REVISION',
        versionTecho('EN_REVISION', false, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('EN_REVISION', '6464396.00', '238826101.00'),
      ),
    );
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'EN_REVISION',
        versionTecho('EN_REVISION', false, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('EN_REVISION', '6464396.00', '238826101.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    expect(techo.mensaje).toContain('enviado a revisión');
    expect(botonesTexto(fixtureTecho)).toContain('Aprobar');
    expect(botonesTexto(fixtureTecho)).toContain('Observar');
    expect(botonesTexto(fixtureTecho)).not.toContain('Enviar a revisión');

    // Aprobar (EN_REVISION → APROBADO).
    clickBoton(fixtureTecho, 'Aprobar');

    const reqApprove = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/directive-ceilings/7/approve/'),
    );
    reqApprove.flush(
      techoMock(
        'APROBADO',
        versionTecho('APROBADO', false, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('APROBADO', '6464396.00', '238826101.00'),
      ),
    );
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'APROBADO',
        versionTecho('APROBADO', false, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('APROBADO', '6464396.00', '238826101.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    expect(techo.mensaje).toContain('Techo aprobado');
    expect(botonesTexto(fixtureTecho)).toContain('Fijar techo');

    // Fijar (APROBADO → FIJADO, inmutable).
    clickBoton(fixtureTecho, 'Fijar techo');

    const reqFreeze = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/directive-ceilings/7/freeze/'),
    );
    expect(reqFreeze.request.body).toEqual({ observaciones: '' });
    reqFreeze.flush(
      techoMock(
        'FIJADO',
        versionTecho('FIJADO', true, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('FIJADO', '6464396.00', '238826101.00'),
      ),
    );
    flush(`${BASE}/directive-ceilings/7/`, {
      ...techoMock(
        'FIJADO',
        versionTecho('FIJADO', true, [recursoSIGEP], [gastoObligatorio]),
        composicionMock('FIJADO', '6464396.00', '238826101.00'),
      ),
    });
    flush(`${BASE}/documents/`, { count: 0, results: [] });
    fixtureTecho.detectChanges();

    // Techo fijado: sin acciones de ciclo y sin formularios editables.
    expect(techo.versionEditable).toBeFalse();
    expect(techo.seleccion?.estado).toBe('FIJADO');
    expect(techo.seleccion?.version?.inmutable).toBeTrue();
    expect(techo.composicion?.techo_distribuible).toBe('238826101.00');
    const botonesTecho = botonesTexto(fixtureTecho);
    expect(botonesTecho).not.toContain('Enviar a revisión');
    expect(botonesTecho).not.toContain('Aprobar');
    expect(botonesTecho).not.toContain('Fijar techo');
    expect(botonesTecho.some((t) => t.includes('Registrar recurso')))
      .withContext('formulario de recursos oculto tras fijar').toBeFalse();
    fixtureTecho.destroy();
    httpMock.verify();

    // ===================================================================
    // 3. Categorías programáticas: cargar el árbol de la gestión
    // ===================================================================
    const fixtureCat = TestBed.createComponent(ProgrammaticCategoriesComponent);
    const categorias = fixtureCat.componentInstance;
    fixtureCat.detectChanges(); // ngOnInit -> listar()

    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestionHabilitada] });
    flush(`${BASE}/programmatic-categories/`, {
      count: 2,
      results: [catPrograma, catSubprograma],
    });
    fixtureCat.detectChanges();

    expect(categorias.categorias.length).toBe(2);
    const htmlCat = fixtureCat.nativeElement as HTMLElement;
    expect(htmlCat.textContent).toContain('Servicios generales');
    expect(htmlCat.textContent).toContain('Servicios administrativos');
    expect(htmlCat.textContent).toContain('09.010');
    fixtureCat.destroy();
    httpMock.verify();

    // ===================================================================
    // 4. Distribución: resumen por fuente, apertura, reserva, validación
    //    y submit → approve → freeze
    // ===================================================================
    // Estado mutable del backend simulado.
    let versionesDist: DistributionVersion[] = [];
    let aperturas: Allocation[] = [];
    let reservas: Reserve[] = [];
    let resumenActual = resumenDist('0.00', '0.00', '238826101.00', 0, 0);

    function flushCargaDistribucion(): void {
      flush(`${BASE}/distributions/dashboard/`, resumenActual);
      flush(`${BASE}/allocations/`, { count: aperturas.length, results: aperturas });
      flush(`${BASE}/reserves/`, { count: reservas.length, results: reservas });
      flush(`${BASE}/distributions/versions/`, versionesDist);
      flush(`${BASE}/programmatic-categories/`, {
        count: 2,
        results: [catPrograma, catSubprograma],
      });
      flush(`${BASE}/catalogs/`, opcionesCatalogo);
    }

    const fixtureDist = TestBed.createComponent(DistributionComponent);
    const distribucion = fixtureDist.componentInstance;
    fixtureDist.detectChanges(); // ngOnInit -> listar()

    flush(`${BASE}/fiscal-years/`, { count: 1, results: [gestionHabilitada] });
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    // Resumen inicial: techo distribuible 238.826.101,00; fuente 41 con
    // techo SIGEP 245.290.497,00 y sin distribución.
    expect(distribucion.gestionSeleccionada).toBe('2027');
    expect(distribucion.resumen?.techo_distribuible).toBe('238826101.00');
    const htmlDist = fixtureDist.nativeElement as HTMLElement;
    expect(htmlDist.textContent).toContain('Techo distribuible');
    expect(htmlDist.textContent).toContain('Bs 238.826.101,00');
    expect(htmlDist.textContent).toContain('Coparticipación tributaria');
    expect(htmlDist.textContent).toContain('Bs 245.290.497,00');

    // Crear la apertura de 1.000.000,00 (fuente 41 / organismo 113).
    clickBoton(fixtureDist, 'Nueva apertura');
    distribucion.nueva.denominacion = 'Apertura principal';
    distribucion.nueva.codigo_sisin = '12345678';
    distribucion.filasFuentes = [
      { fuente: '41', organismo: '113', monto: 1000000.00 },
    ];
    fixtureDist.detectChanges();
    clickBoton(fixtureDist, 'Crear apertura');

    const reqApertura = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/allocations/'),
    );
    expect(reqApertura.request.body).toEqual(
      jasmine.objectContaining({
        gestion: '2027',
        denominacion: 'Apertura principal',
        fuentes: [{ fuente: '41', organismo: '113', monto: 1000000.00 }],
      }),
    );
    reqApertura.flush(aperturaMock);

    // La apertura activa la versión 1 de la distribución (BORRADOR).
    aperturas = [aperturaMock];
    versionesDist = [versionDist('BORRADOR')];
    resumenActual = resumenDist('1000000.00', '0.00', '237826101.00', 0.42, 1);
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    expect(distribucion.aperturas.length).toBe(1);
    expect(htmlDist.textContent).toContain('Apertura principal');
    expect(htmlDist.textContent).toContain('Bs 1.000.000,00');
    expect(
      botonesTexto(fixtureDist).some((t) => t.includes('Enviar a revisión')),
    ).withContext('versión BORRADOR muestra Enviar a revisión').toBeTrue();

    // Reserva DISTRITAL por el resto del techo distribuible de la fuente 41.
    distribucion.formReserva = {
      fuente: '41',
      organismo: '113',
      tipo: 'DISTRITAL',
      monto: 244290497.00,
      motivo: 'Reserva por el resto del techo distribuible',
    };
    fixtureDist.detectChanges();
    clickBoton(fixtureDist, 'Crear reserva');

    const reqReserva = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/reserves/'),
    );
    expect(reqReserva.request.body).toEqual({
      gestion: '2027',
      fuente: '41',
      organismo: '113',
      tipo: 'DISTRITAL',
      monto: 244290497.00,
      motivo: 'Reserva por el resto del techo distribuible',
    });
    reqReserva.flush(reservaMock);

    // Σ por fuente: distribuido + reservado = techo → disponible 0.
    reservas = [reservaMock];
    resumenActual = resumenDist('1000000.00', '244290497.00', '0.00', 100, 1);
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    expect(distribucion.reservas.length).toBe(1);
    expect(htmlDist.textContent).toContain('Bs 0,00');
    expect(htmlDist.textContent).toContain('100%');

    // Validar la fijación: todas las fuentes con diferencia 0.
    clickBoton(fixtureDist, 'Validar distribución');

    const reqValidar = httpMock.expectOne(
      (r) => r.method === 'GET' && r.url.includes('/distributions/1/validate/'),
    );
    reqValidar.flush(validacionOk);
    fixtureDist.detectChanges();

    expect(distribucion.validacion?.valida).toBeTrue();
    expect(htmlDist.textContent).toContain('La distribución está completa');
    expect(htmlDist.textContent).toContain('diferencia 0');
    expect(htmlDist.textContent).toContain('válida');

    // Enviar a revisión (BORRADOR → EN_REVISION).
    clickBoton(fixtureDist, 'Enviar a revisión');

    const reqSubmitDist = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/distributions/1/submit/'),
    );
    reqSubmitDist.flush(versionDist('EN_REVISION'));
    versionesDist = [versionDist('EN_REVISION')];
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    expect(distribucion.mensaje).toContain('enviada a revisión');
    expect(botonesTexto(fixtureDist)).toContain('Observar');
    expect(botonesTexto(fixtureDist)).toContain('Aprobar');

    // Aprobar (EN_REVISION → APROBADO).
    clickBoton(fixtureDist, 'Aprobar');

    const reqApproveDist = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/distributions/1/approve/'),
    );
    reqApproveDist.flush(versionDist('APROBADO'));
    versionesDist = [versionDist('APROBADO')];
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    expect(distribucion.mensaje).toContain('Distribución aprobada');
    expect(botonesTexto(fixtureDist)).toContain('Fijar distribución');

    // Fijar (APROBADO → FIJADO, inmutable con checksum).
    spyOn(window, 'confirm').and.returnValue(true);
    clickBoton(fixtureDist, 'Fijar distribución');

    const reqFreezeDist = httpMock.expectOne(
      (r) => r.method === 'POST' && r.url.includes('/distributions/1/freeze/'),
    );
    expect(reqFreezeDist.request.body).toEqual({ observaciones: '' });
    reqFreezeDist.flush(versionDist('FIJADO', true));
    versionesDist = [versionDist('FIJADO', true)];
    flushCargaDistribucion();
    fixtureDist.detectChanges();

    // Distribución fijada: sin acciones del ciclo y con botón Ajuste.
    expect(distribucion.versionActiva()).toBeNull();
    expect(distribucion.mensaje).toContain('fijada (inmutable)');
    expect(htmlDist.textContent).toContain('FIJADA (inmutable)');
    expect(htmlDist.textContent).toContain('Distribución fijada');
    expect(botonesTexto(fixtureDist)).toContain('Ajuste');
    const botonesDist = botonesTexto(fixtureDist);
    expect(botonesDist.some((t) => t.includes('Enviar a revisión')))
      .withContext('sin Enviar a revisión tras fijar').toBeFalse();
    expect(botonesDist).not.toContain('Aprobar');
    expect(botonesDist).not.toContain('Fijar distribución');
    fixtureDist.destroy();
    httpMock.verify();
  });
});
