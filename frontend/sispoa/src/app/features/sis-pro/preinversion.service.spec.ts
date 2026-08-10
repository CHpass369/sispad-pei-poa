import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PreinversionService } from './preinversion.service';
import { environment } from '../../../environments/environment';

describe('PreinversionService', () => {
  let service: PreinversionService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [PreinversionService],
    });
    service = TestBed.inject(PreinversionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists preinvestment projects with filters', () => {
    service.listarProyectos({ gestion: 2027, tipologia_rm115: 'III' }).subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/?gestion=2027&tipologia_rm115=III`,
    );
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, results: [] });
  });

  it('classifies a project typology', () => {
    service.clasificar('pr1').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/clasificar/`,
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ aceptar: true });
    req.flush({ tipologia_sugerida: 'II' });
  });

  it('initializes ITCP and EDTP', () => {
    service.inicializarItcp('pr1').subscribe();
    httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/inicializar_itcp/`,
    ).flush({ itcp_id: 'i1', condiciones: 9 });
    service.inicializarEdtp('pr1').subscribe();
    httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/inicializar_edtp/`,
    ).flush({ edtp_id: 'e1', secciones: 21 });
  });

  it('computes readiness', () => {
    service.calcularMadurez('pr1').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/calcular_madurez/`,
    );
    expect(req.request.method).toBe('POST');
    req.flush({ puntaje_madurez: '95', habilitado_poa: true });
  });

  it('validates ITCP approval', () => {
    service.validarAprobacion('pr1', 'ITCP').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/validar_aprobacion/`,
    );
    expect(req.request.body).toEqual({ documento: 'ITCP' });
    req.flush({ aprobable: false, errores: ['x'], estado_preinversion: 'itcp_elaboracion' });
  });

  it('generates a document', () => {
    service.generarDocumento('pr1', 'EDTP').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/generar_documento/`,
    );
    expect(req.request.body).toEqual({ tipo_documento: 'EDTP' });
    req.flush({ documento_generado_id: 'g1', estado: 'completado' });
  });

  it('gets the transfer package', () => {
    service.paqueteTransferencia('pr1').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/paquete_transferencia/`,
    );
    expect(req.request.method).toBe('GET');
    req.flush({ project_code: 'P-1' });
  });

  it('changes the preinvestment status', () => {
    service.cambiarEstado('pr1', 'enviado_poa').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/pr1/cambiar_estado/`,
    );
    expect(req.request.body).toEqual({ estado_preinversion: 'enviado_poa' });
    req.flush({});
  });

  it('lists eligible-for-poa projects', () => {
    service.elegiblesPoa().subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/proyectos-preinversion/elegibles_poa/`,
    );
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('updates an ITCP condition', () => {
    service.actualizarCondicion('c1', { estado: 'cumple' }).subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pro/itcp-condiciones/c1/`,
    );
    expect(req.request.method).toBe('PATCH');
    req.flush({});
  });

  it('creates TDR items and EDTP costs', () => {
    service.crearActividadTdr({ tdr: 't1', codigo: 'A1' } as any).subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/tdr-actividades/`).flush({});
    service.crearItemCosto({ edtp: 'e1', descripcion: 'x' } as any).subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/edtp-items-costo/`).flush({});
    service.crearFinanciamiento({ edtp: 'e1', codigo_fuente: 'F1' } as any).subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/edtp-financiamiento/`).flush({});
  });

  it('maps typology and condition labels', () => {
    expect(service.tipologiaNombre('III')).toBe('Desarrollo Social');
    expect(service.condicionCategoria('ambiente')).toBe('Impactos ambientales');
    expect(service.etiquetaEstadoExpediente('habilitado_poa')).toBe('Habilitado para POA');
    expect(service.estadosCondicion.length).toBeGreaterThan(0);
  });
});
