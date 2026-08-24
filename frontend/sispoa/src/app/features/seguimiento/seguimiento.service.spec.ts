import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SeguimientoService } from './seguimiento.service';

describe('SeguimientoService API contracts', () => {
  let service: SeguimientoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SeguimientoService],
    });
    service = TestBed.inject(SeguimientoService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('requests the real dashboard route without a management param', () => {
    // La gestión ya no viaja en la URL: la resuelve el candado en el backend
    // (ADR-007). Antes cada cliente elegía el año por su cuenta.
    service.obtenerDashboard().subscribe();

    const request = http.expectOne('/api/v1/entradas/dashboard/');
    expect(request.request.method).toBe('GET');
    request.flush({ gestion: 2027, total_actividades: 228 });
  });

  it('requests the correctly spelled semaphore route without a management param', () => {
    service.obtenerSemaforo().subscribe();

    const request = http.expectOne('/api/v1/entradas/semaforo/');
    expect(request.request.method).toBe('GET');
    request.flush({
      gestion: 2027,
      resumen: { verde: 0, amarillo: 0, rojo: 0, total: 0 },
      detalle: { verde: [], amarillo: [], rojo: [] },
    });
  });
});
