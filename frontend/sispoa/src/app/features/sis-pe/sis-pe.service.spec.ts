import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SisPeService } from './sis-pe.service';
import { environment } from '../../../environments/environment';

describe('SisPeService', () => {
  let service: SisPeService;
  let httpMock: HttpTestingController;

  const instrumento = {
    id: 'i1', tipo: 't1', tipo_nombre: 'PAD', codigo: 'PAD-2027',
    nombre: 'PAD Municipal', periodo_inicio: 2027, periodo_fin: 2031,
    estado: 'borrador', versiones_count: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SisPeService],
    });
    service = TestBed.inject(SisPeService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('lists instruments from the V2 sis-pe namespace', () => {
    service.listarInstrumentos().subscribe(data => {
      expect(data.results[0].codigo).toBe('PAD-2027');
    });
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/instrumentos/`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, results: [instrumento] });
  });

  it('creates an instrument via POST', () => {
    service.crearInstrumento({ codigo: 'X' } as any).subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/instrumentos/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ codigo: 'X' });
    req.flush({});
  });

  it('creates a version via the instrument action', () => {
    service.crearVersion('i1', 'm1', 'V2').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pe/instrumentos/i1/crear_version/`,
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ metodologia: 'm1', etiqueta: 'V2' });
    req.flush({});
  });

  it('lists versions of an instrument', () => {
    service.versionesDeInstrumento('i1').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-pe/instrumentos/i1/versiones/`,
    );
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('gets nodes of a version', () => {
    service.nodosDeVersion('v1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/versiones/v1/nodos/`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('approves a version with the official norm', () => {
    service.aprobarVersion('v1', 'RM 1/2027').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/versiones/v1/aprobar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ norma_aprobacion: 'RM 1/2027' });
    req.flush({});
  });

  it('verifies the version checksum', () => {
    service.verificarVersion('v1').subscribe(data => {
      expect(data.consistente).toBeTrue();
    });
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/versiones/v1/verificar/`);
    expect(req.request.method).toBe('GET');
    req.flush({ inmutable: true, checksum_registrado: 'a', checksum_actual: 'a', consistente: true });
  });

  it('lists methodologies', () => {
    service.listarMetodologias().subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pe/metodologias/`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 0, results: [] });
  });
});
