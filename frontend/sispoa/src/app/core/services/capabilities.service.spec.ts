import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CapabilitiesService } from './capabilities.service';
import { environment } from '../../../environments/environment';

describe('CapabilitiesService', () => {
  let service: CapabilitiesService;
  let httpMock: HttpTestingController;

  const mockResponse = {
    usuario: { id: 'u1', email: 'cap@test.gob.bo' },
    roles: ['revisor_planificacion'],
    capabilities: ['sis_pe.pad.validate', 'sis_pe.instrumento.read'],
    alcances: [
      {
        tipo: 'organizacional',
        unidad_id: 'ue-1',
        unidad_nombre: 'Secretaría de Capacidades',
        sigla: 'SECCAP',
        vigente_desde: '2026-01-01',
        vigente_hasta: null,
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CapabilitiesService],
    });
    service = TestBed.inject(CapabilitiesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should request the V2 capabilities endpoint', () => {
    service.cargar().subscribe(data => {
      expect(data.capabilities).toContain('sis_pe.pad.validate');
    });

    const req = httpMock.expectOne(`${environment.apiUrlV2}/me/capabilities/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should expose capabilities after load', () => {
    service.cargar().subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/me/capabilities/`).flush(mockResponse);

    expect(service.tiene('sis_pe.pad.validate')).toBeTrue();
    expect(service.tiene('sis_poa.budget.manage')).toBeFalse();
    expect(service.tieneAlguna(['sis_pe.pad.validate', 'x'])).toBeTrue();
    expect(service.tieneAlguna(['x', 'y'])).toBeFalse();
    expect(service.listar()).toEqual(['sis_pe.pad.validate', 'sis_pe.instrumento.read']);
  });

  it('should expose organizational scopes after load', () => {
    service.cargar().subscribe();
    httpMock.expectOne(`${environment.apiUrlV2}/me/capabilities/`).flush(mockResponse);

    const alcances = service.listarAlcances();
    expect(alcances.length).toBe(1);
    expect(alcances[0].tipo).toBe('organizacional');
    expect(alcances[0].unidad_nombre).toBe('Secretaría de Capacidades');
  });
});
