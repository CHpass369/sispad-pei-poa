import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../../shared/shared.module';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../core/testing/gestion-habilitada.stub';
import { PoauRecursosWizardComponent } from './poau-recursos-wizard.component';
import { PoauRecursosViewerComponent } from './poau-recursos-viewer.component';
import { grupoDePartida, requerimientoVacio } from './poau-recursos.model';

describe('grupoDePartida', () => {
  it('el grupo es el primer dígito de la partida y cuatro ceros', () => {
    expect(grupoDePartida('25200')).toBe('20000');
    expect(grupoDePartida('11100')).toBe('10000');
    expect(grupoDePartida('99200')).toBe('90000');
  });

  it('un código que no es de cinco dígitos no deduce nada', () => {
    // Vale más el campo vacío que un grupo inventado a partir de basura.
    expect(grupoDePartida('')).toBe('');
    expect(grupoDePartida('252')).toBe('');
    expect(grupoDePartida('252000')).toBe('');
    expect(grupoDePartida('2A200')).toBe('');
    expect(grupoDePartida(null as any)).toBe('');
  });

  it('ignora los espacios de los costados', () => {
    expect(grupoDePartida('  25200 ')).toBe('20000');
  });
});

describe('PoauRecursosWizardComponent · combos de catálogo', () => {
  let fixture: ComponentFixture<PoauRecursosWizardComponent>;
  let componente: PoauRecursosWizardComponent;
  let http: HttpTestingController;

  const ACCION = {
    id: 'ac-1', codigo_accion: 'ACP-01', denominacion: 'MEJORAR LA VIALIDAD',
    categoria_programatica: '170 0 001', cargo_responsable: 'JEFE DE OBRAS',
    gestion: 2027,
  };
  const DA = [
    { id: 'da-1', codigo: '1', nombre: 'SECRETARIA DE ADMINISTRACION Y FINANZAS' },
    { id: 'da-5', codigo: '5', nombre: 'SECRETARIA DE INFRAESTRUCTURA' },
  ];
  const UE = [
    { id: 'ue-1', codigo: '001', nombre: 'ADMINISTRACION CENTRAL', da: 'da-1' },
    { id: 'ue-2', codigo: '002', nombre: 'TESORERIA', da: 'da-1' },
    { id: 'ue-9', codigo: '009', nombre: 'OBRAS PUBLICAS', da: 'da-5' },
  ];
  const CATEGORIAS = [
    { codigo: '170 0 001', denominacion: 'CONSTRUCCION DE VIAS URBANAS' },
    { codigo: '000 0 001', denominacion: 'FUNCIONAMIENTO ALCALDIA MUNICIPAL' },
  ];
  const PARTIDA = {
    id: 'og-1', codigo: '25200', denominacion: 'Estudios e Investigaciones',
    nivel: 'partida',
  };
  const FUENTES = [
    { id: 'f-20', codigo: '20', denominacion: 'Recursos Específicos' },
    { id: 'f-41', codigo: '41', denominacion: 'Transferencias TGN' },
  ];
  const GRUPOS = [
    { id: 'g-2', codigo: '20000', denominacion: 'SERVICIOS NO PERSONALES' },
    { id: 'g-3', codigo: '30000', denominacion: 'MATERIALES Y SUMINISTROS' },
  ];

  const responderCatalogos = () => {
    http.expectOne(r => r.url.includes('/acciones-poa/')).flush({ results: [ACCION] });
    http.expectOne(r => r.url.includes('/operaciones/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('/actividades/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('/direcciones-administrativas/'))
        .flush({ results: DA });
    http.expectOne(r => r.url.includes('/unidades-ejecutoras/')).flush({ results: UE });
    http.expectOne(r => r.url.includes('/fuentes/')).flush({ results: FUENTES });
    http.expectOne(r => r.url.includes('nivel=grupo')).flush({ results: GRUPOS });
    http.expectOne(r => r.url.includes('/categorias-programaticas/')).flush(CATEGORIAS);
    fixture.detectChanges();
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule, SharedModule],
      declarations: [PoauRecursosWizardComponent, PoauRecursosViewerComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    fixture = TestBed.createComponent(PoauRecursosWizardComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('pide los catálogos de la gestión habilitada', () => {
    const da = http.expectOne(r => r.url.includes('/direcciones-administrativas/'));
    expect(da.request.urlWithParams).toContain('gestion=2027');
    da.flush({ results: DA });
    http.expectOne(r => r.url.includes('/acciones-poa/')).flush({ results: [ACCION] });
    http.expectOne(r => r.url.includes('/operaciones/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('/actividades/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('/unidades-ejecutoras/')).flush({ results: UE });
    http.expectOne(r => r.url.includes('/fuentes/')).flush({ results: FUENTES });
    http.expectOne(r => r.url.includes('nivel=grupo')).flush({ results: GRUPOS });
    http.expectOne(r => r.url.includes('/categorias-programaticas/')).flush(CATEGORIAS);
  });

  describe('acción de corto plazo', () => {
    it('hereda categoría y trae la denominación del catálogo', () => {
      responderCatalogos();
      componente.accionSel = 'ac-1';
      componente.onAccion();
      expect(componente.cabecera.categoriaProgramatica).toBe('170 0 001');
      expect(componente.cabecera.denominacionCategoria)
        .toBe('CONSTRUCCION DE VIAS URBANAS');
      expect(componente.cabecera.cargoReacp).toBe('JEFE DE OBRAS');
    });

    it('una categoría que no está en el catálogo deja la denominación vacía', () => {
      // Y la pantalla lo dice en vez de inventar un nombre.
      responderCatalogos();
      componente.acciones = [{ ...ACCION, categoria_programatica: '999 0 999' }];
      componente.accionSel = 'ac-1';
      componente.onAccion();
      expect(componente.cabecera.denominacionCategoria).toBe('');
    });

    it('ofrece las acciones con su código y su denominación', () => {
      responderCatalogos();
      expect(componente.opcionesAccion[0].etiqueta)
        .toBe('ACP-01 — MEJORAR LA VIALIDAD');
      expect(componente.opcionesAccion[0].detalle).toBe('170 0 001');
    });
  });

  describe('DA y UE', () => {
    it('la UE arranca vacía hasta que se elige la DA', () => {
      responderCatalogos();
      expect(componente.daId).toBe('');
      expect(componente.opcionesUe).toEqual([]);
    });

    it('solo ofrece las UE que cuelgan de la DA elegida', () => {
      responderCatalogos();
      componente.onDa({ valor: '1', etiqueta: '1 — SAF', dato: DA[0] });
      expect(componente.opcionesUe.map(o => o.valor)).toEqual(['001', '002']);
      componente.onDa({ valor: '5', etiqueta: '5 — INFRA', dato: DA[1] });
      expect(componente.opcionesUe.map(o => o.valor)).toEqual(['009']);
    });

    it('cambiar de DA borra la UE anterior', () => {
      // Sin esto queda la combinación DA 5 / UE 001, que no existe.
      responderCatalogos();
      componente.onDa({ valor: '1', etiqueta: '1 — SAF', dato: DA[0] });
      componente.cabecera.ue = '001';
      componente.onDa({ valor: '5', etiqueta: '5 — INFRA', dato: DA[1] });
      expect(componente.cabecera.ue).toBe('');
    });
  });

  describe('partida de gastos', () => {
    it('busca en el servidor, no en memoria', fakeAsync(() => {
      responderCatalogos();
      let recibido: any[] = [];
      componente.buscarPartidaPorCodigo('2520').subscribe(o => { recibido = o; });
      const pedido = http.expectOne(r => r.url.includes('/objetos-gasto/'));
      expect(pedido.request.urlWithParams).toContain('search=2520');
      expect(pedido.request.urlWithParams).toContain('gestion=2027');
      // `imputable` y no `nivel=partida`: se imputa tanto a partidas como a
      // detalles, y `25220` —un detalle— quedaba fuera del desplegable.
      expect(pedido.request.urlWithParams).toContain('imputable=true');
      expect(pedido.request.urlWithParams).not.toContain('nivel=partida');
      pedido.flush({ results: [PARTIDA] });
      tick();
      expect(recibido[0].valor).toBe('25200');
      expect(recibido[0].detalle).toBe('Estudios e Investigaciones · partida');
    }));

    it('el desplegable muestra el nivel para distinguir partida de detalle', fakeAsync(() => {
      responderCatalogos();
      let recibido: any[] = [];
      componente.buscarPartidaPorCodigo('252').subscribe(o => { recibido = o; });
      http.expectOne(r => r.url.includes('/objetos-gasto/')).flush({
        results: [{ codigo: '25220', denominacion: 'Consultores Individuales',
                    nivel: 'detalle' }],
      });
      tick();
      expect(recibido[0].valor).toBe('25220');
      expect(recibido[0].detalle).toBe('Consultores Individuales · detalle');
    }));

    it('el combo de descripción muestra el texto y guarda el texto', fakeAsync(() => {
      responderCatalogos();
      let recibido: any[] = [];
      componente.buscarPartidaPorDescripcion('estudios').subscribe(o => { recibido = o; });
      http.expectOne(r => r.url.includes('/objetos-gasto/')).flush({ results: [PARTIDA] });
      tick();
      expect(recibido[0].etiqueta).toBe('Estudios e Investigaciones');
      expect(recibido[0].detalle).toBe('25200 · partida');
    }));

    it('elegir por código llena la descripción', () => {
      responderCatalogos();
      const r = requerimientoVacio();
      componente.onPartida(r, {
        valor: '25200', etiqueta: '25200', dato: PARTIDA,
      });
      expect(r.codPartida).toBe('25200');
      expect(r.descripcionPartida).toBe('Estudios e Investigaciones');
    });

    it('elegir por descripción llena el código', () => {
      responderCatalogos();
      const r = requerimientoVacio();
      componente.onPartida(r, {
        valor: 'Estudios e Investigaciones',
        etiqueta: 'Estudios e Investigaciones', dato: PARTIDA,
      });
      expect(r.codPartida).toBe('25200');
      expect(r.descripcionPartida).toBe('Estudios e Investigaciones');
    });

    it('elegir la partida deduce el grupo de gasto', () => {
      responderCatalogos();
      const r = requerimientoVacio();
      componente.onPartida(r, { valor: '25200', etiqueta: '25200', dato: PARTIDA });
      expect(r.grupoGasto).toBe('20000');
      expect(componente.nombreGrupo(r.grupoGasto)).toBe('SERVICIOS NO PERSONALES');
    });

    it('un catálogo caído no rompe el formulario', fakeAsync(() => {
      responderCatalogos();
      let recibido: any[] | null = null;
      componente.buscarPartidaPorCodigo('x').subscribe(o => { recibido = o; });
      http.expectOne(r => r.url.includes('/objetos-gasto/'))
          .flush({}, { status: 500, statusText: 'Server Error' });
      tick();
      expect(recibido).toEqual([]);
    }));
  });

  describe('fuente, organismo y tipo de gasto', () => {
    it('ofrece las fuentes con su código y su denominación', () => {
      responderCatalogos();
      expect(componente.opcionesFuente.map(o => o.valor)).toEqual(['20', '41']);
      expect(componente.opcionesFuente[0].etiqueta)
        .toBe('20 — Recursos Específicos');
    });

    it('los organismos se buscan en el servidor', fakeAsync(() => {
      // Son 319: filtrar en memoria dejaría fuera a casi todos.
      responderCatalogos();
      let recibido: any[] = [];
      componente.buscarOrganismo('230').subscribe(o => { recibido = o; });
      const pedido = http.expectOne(r => r.url.includes('/organismos/'));
      expect(pedido.request.urlWithParams).toContain('search=230');
      expect(pedido.request.urlWithParams).toContain('gestion=2027');
      pedido.flush({ results: [{ codigo: '230', denominacion: 'Coparticipación' }] });
      tick();
      expect(recibido[0].valor).toBe('230');
      expect(recibido[0].etiqueta).toBe('230 — Coparticipación');
    }));

    it('el tipo de gasto sale de una lista y no de texto libre', () => {
      responderCatalogos();
      expect(componente.opcionesTipoGasto.map(o => o.valor))
        .toEqual(['Funcionamiento', 'Inversión']);
    });
  });
});
