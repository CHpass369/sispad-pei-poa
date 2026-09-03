import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../../shared/shared.module';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../core/testing/gestion-habilitada.stub';
import { PoauRecursosWizardComponent } from './poau-recursos-wizard.component';
import { PoauRecursosViewerComponent } from './poau-recursos-viewer.component';
import {
  MESES, grupoDePartida, requerimientoVacio, saldoRestante,
} from './poau-recursos.model';

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

describe('saldoRestante', () => {
  /** Un requerimiento que consume `monto` en un solo mes. */
  const porMonto = (monto: number) => {
    const r = requerimientoVacio();
    r.programacion[MESES[0]] = monto;
    return r;
  };

  it('descuenta del saldo lo ya programado', () => {
    expect(saldoRestante(250000, [porMonto(100000)])).toBe(150000);
  });

  it('suma todos los requerimientos, no solo el último', () => {
    expect(saldoRestante(250000, [porMonto(100000), porMonto(60000)])).toBe(90000);
  });

  it('pasarse del techo devuelve el déficit en negativo', () => {
    // El negativo se devuelve tal cual: recortarlo a cero escondería
    // justamente el dato que hay que corregir.
    expect(saldoRestante(250000, [porMonto(300000)])).toBe(-50000);
  });

  it('sin saldo conocido no hay resto que mostrar', () => {
    // `null` y no cero: no es lo mismo «no queda nada» que «no se sabe».
    expect(saldoRestante(null, [porMonto(100000)])).toBeNull();
  });

  it('sin requerimientos el resto es el saldo entero', () => {
    expect(saldoRestante(250000, [])).toBe(250000);
  });
});

describe('PoauRecursosWizardComponent · combos de catálogo', () => {
  let fixture: ComponentFixture<PoauRecursosWizardComponent>;
  let componente: PoauRecursosWizardComponent;
  let http: HttpTestingController;

  // `EM-000-05` con la categoría `340 0 099` está en la planilla de saldos con
  // 250.000,00 Bs.: el caso se apoya en el catálogo real y no en un doble.
  const UNIDADES = [
    { codigo: 'EM-000-05', nombre: 'TRANSPARENCIA', sigla: 'TRANSP' },
    { codigo: 'EM-D01', nombre: 'SUBALCALDÍA DISTRITO 1', sigla: 'SD1' },
  ];
  const OPERACION = {
    nivel: 'operacion', objeto_id: 'op-1', codigo: 'OP-01',
    operacion: 'AUDITAR PROCESOS', categoria_programatica: '340 0 099',
    accion_id: 'ac-1', cod_accion_corto_plazo: 'ACP-01',
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
    http.expectOne(r => r.url.includes('/matriz-poau/'))
        .flush({ gestion: 2027, unidades: UNIDADES, filas: [] });
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
    http.expectOne(r => r.url.includes('/matriz-poau/'))
        .flush({ gestion: 2027, unidades: UNIDADES, filas: [] });
    http.expectOne(r => r.url.includes('/unidades-ejecutoras/')).flush({ results: UE });
    http.expectOne(r => r.url.includes('/fuentes/')).flush({ results: FUENTES });
    http.expectOne(r => r.url.includes('nivel=grupo')).flush({ results: GRUPOS });
    http.expectOne(r => r.url.includes('/categorias-programaticas/')).flush(CATEGORIAS);
  });

  describe('unidad, categoría y operación', () => {
    /** Elige la unidad y responde la matriz que pide su cascada. */
    const elegirUnidad = (codigo: string, filas: any[] = [OPERACION]) => {
      componente.unidadSel = codigo;
      componente.onUnidad();
      http.expectOne(r => r.url.includes('/matriz-poau/'))
          .flush({ gestion: 2027, unidades: [], filas });
    };

    it('ofrece las unidades con su código y su nombre', () => {
      responderCatalogos();
      expect(componente.opcionesUnidad[0].etiqueta)
        .toBe('EM-000-05 — TRANSPARENCIA');
      expect(componente.opcionesUnidad[0].detalle).toBe('TRANSP');
    });

    it('la unidad elegida trae sus categorías con saldo de la planilla', () => {
      responderCatalogos();
      elegirUnidad('EM-000-05');
      expect(componente.cabecera.codigoUnidad).toBe('EM-000-05');
      expect(componente.categoriasDeUnidad.map(c => c.categoriaProgramatica))
        .toEqual(['340 0 099']);
      expect(componente.categoriasDeUnidad[0].saldo).toBe(250000);
    });

    it('elegir la categoría fija el saldo disponible para programar', () => {
      responderCatalogos();
      elegirUnidad('EM-000-05');
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
      expect(componente.cabecera.categoriaProgramatica).toBe('340 0 099');
      expect(componente.cabecera.saldoDisponible).toBe(250000);
    });

    it('solo ofrece las operaciones del POAU físico de esa categoría', () => {
      responderCatalogos();
      elegirUnidad('EM-000-05', [
        OPERACION,
        { ...OPERACION, objeto_id: 'op-2', categoria_programatica: '999 0 999' },
        // Las actividades y tareas cuelgan de la operación: no son elegibles.
        { ...OPERACION, objeto_id: 'op-3', nivel: 'actividad' },
      ]);
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
      expect(componente.operacionesFiltradas.map(o => o.objeto_id)).toEqual(['op-1']);
    });

    it('el espaciado irregular de la categoría no descarta su operación', () => {
      // La planilla escribe `340 0 099` y el POAU puede traer `340  0 099`.
      responderCatalogos();
      elegirUnidad('EM-000-05',
                   [{ ...OPERACION, categoria_programatica: '340  0 099' }]);
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
      expect(componente.operacionesFiltradas.length).toBe(1);
    });

    it('la operación elegida arrastra su acción de corto plazo', () => {
      // La asignación de gasto sigue colgando de la acción, aunque ya no se
      // elija: sin esto el registro se iría sin `accion_poa`.
      responderCatalogos();
      elegirUnidad('EM-000-05');
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
      componente.operacionSel = 'op-1';
      componente.onOperacion();
      expect(componente.cabecera.operacionId).toBe('op-1');
      expect(componente.cabecera.accionPoaId).toBe('ac-1');
      expect(componente.cabecera.codigoAccion).toBe('ACP-01');
      expect(componente.cabecera.actividadId).toBeNull();
    });

    it('cambiar de unidad borra la categoría y la operación anteriores', () => {
      // Sin esto queda el saldo de una unidad con la operación de otra.
      responderCatalogos();
      elegirUnidad('EM-000-05');
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
      componente.operacionSel = 'op-1';
      componente.onOperacion();

      elegirUnidad('EM-D01', []);
      expect(componente.cabecera.categoriaProgramatica).toBe('');
      expect(componente.cabecera.saldoDisponible).toBeNull();
      expect(componente.cabecera.operacionId).toBeNull();
      expect(componente.cabecera.accionPoaId).toBeNull();
    });

    it('una unidad que no está en la planilla no ofrece categorías', () => {
      responderCatalogos();
      componente.unidades = [...UNIDADES, { codigo: 'XX-99', nombre: 'NUEVA', sigla: '' }];
      elegirUnidad('XX-99', []);
      expect(componente.categoriasDeUnidad).toEqual([]);
    });
  });

  describe('globo del saldo en requerimientos', () => {
    /** Deja la cabecera con el saldo de `EM-000-05` / `340 0 099`: 250.000. */
    const conSaldo = () => {
      componente.unidadSel = 'EM-000-05';
      componente.onUnidad();
      http.expectOne(r => r.url.includes('/matriz-poau/'))
          .flush({ gestion: 2027, unidades: [], filas: [] });
      componente.categoriaSel = '340 0 099';
      componente.onCategoria();
    };
    const programar = (monto: number) => {
      componente.requerimientos[0].programacion['enero'] = monto;
    };

    it('el globo arranca con el saldo entero y sin déficit', () => {
      responderCatalogos();
      conSaldo();
      expect(componente.restante).toBe(250000);
      expect(componente.enDeficit).toBe(false);
      expect(componente.montoGlobo).toBe(250000);
    });

    it('programar descuenta del globo', () => {
      responderCatalogos();
      conSaldo();
      programar(90000);
      expect(componente.restante).toBe(160000);
      expect(componente.enDeficit).toBe(false);
    });

    it('pasarse del saldo pone el globo en déficit', () => {
      responderCatalogos();
      conSaldo();
      programar(310000);
      expect(componente.restante).toBe(-60000);
      expect(componente.enDeficit).toBe(true);
    });

    it('en déficit el globo muestra cuánto falta, sin el signo', () => {
      // El rótulo ya dice «Déficit»; repetir el menos solo agrega ruido.
      responderCatalogos();
      conSaldo();
      programar(310000);
      expect(componente.montoGlobo).toBe(60000);
    });

    it('sin saldo conocido no hay globo ni déficit', () => {
      responderCatalogos();
      programar(500000);
      expect(componente.cabecera.saldoDisponible).toBeNull();
      expect(componente.restante).toBeNull();
      expect(componente.enDeficit).toBe(false);
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
