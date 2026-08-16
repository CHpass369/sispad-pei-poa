import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SisPoaService } from './sis-poa.service';
import { environment } from '../../../environments/environment';

describe('SisPoaService', () => {
  let service: SisPoaService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SisPoaService],
    });
    service = TestBed.inject(SisPoaService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists POAs from the V2 sis-poa namespace', () => {
    service.listarPoas({ gestion: 2027 }).subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/poas/?gestion=2027`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, results: [] });
  });

  it('creates a POA via POST', () => {
    service.crearPoa({ codigo: 'P-2027' } as any).subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/poas/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('lists acciones of a POA', () => {
    service.accionesDePoa('p1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/poas/p1/acciones/`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('gets the budget summary', () => {
    service.resumenPresupuesto('p1').subscribe();
    const req = httpMock.expectOne(
      `${environment.apiUrlV2}/sis-poa/poas/p1/resumen_presupuesto/`,
    );
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('validates the ceiling', () => {
    service.validarTecho('p1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/poas/p1/validar_techo/`);
    expect(req.request.method).toBe('GET');
    req.flush({ excede: false, techo: '0', formulado: '0', mensaje: '' });
  });

  it('creates an accion under a POA', () => {
    service.crearAccion('p1', 'A1', 'Acción 1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/acciones/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ poa: 'p1', codigo: 'A1', nombre: 'Acción 1' });
    req.flush({});
  });

  it('gets programaciones by POA', () => {
    service.programacionesDePoa('p1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-poa/poas/p1/programaciones/`);
    expect(req.request.method).toBe('GET');
    req.flush({ poa: 'p1', codigo: 'P-2027', filas: [] });
  });
});
