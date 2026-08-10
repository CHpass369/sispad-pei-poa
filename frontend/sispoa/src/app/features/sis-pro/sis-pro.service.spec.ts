import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SisProService } from './sis-pro.service';
import { environment } from '../../../environments/environment';

describe('SisProService', () => {
  let service: SisProService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SisProService],
    });
    service = TestBed.inject(SisProService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists projects from the V2 sis-pro namespace', () => {
    service.listarProyectos({ gestion: 2027 }).subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/?gestion=2027`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, results: [] });
  });

  it('creates a project', () => {
    service.crearProyecto({ codigo_interno: 'P-1' } as any).subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('gets the ascending chain', () => {
    service.cadena('pr1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/pr1/cadena/`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('advances the project phase', () => {
    service.avanzarFase('pr1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/pr1/avanzar_fase/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('gets the budget', () => {
    service.presupuesto('pr1').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/pr1/presupuesto/`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('lists condiciones and documentos', () => {
    service.condiciones('pr1').subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/pr1/condiciones/`).flush([]);
    service.documentos('pr1').subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/proyectos/pr1/documentos/`).flush([]);
  });

  it('creates a condicion', () => {
    service.crearCondicion('pr1', 'Saneamiento').subscribe();
    const req = httpMock.expectOne(`${environment.apiUrlV2}/sis-pro/condiciones/`);
    expect(req.request.body).toEqual({ proyecto: 'pr1', descripcion: 'Saneamiento' });
    req.flush({});
  });
});
