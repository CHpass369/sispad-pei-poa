import { HTTP_INTERCEPTORS, HttpClient, HttpErrorResponse } from '@angular/common/http';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthService } from '../services/auth.service';
import { ErrorApi, ErrorInterceptor } from './error.interceptor';

describe('ErrorInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let auth: jasmine.SpyObj<AuthService>;

  const URL = '/api/v2/admin/users/x/approve/';

  beforeEach(() => {
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['logout']);
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  function flatten(body: unknown, status: number): Promise<ErrorApi> {
    return new Promise(resolve => {
      http.post(URL, {}).subscribe({
        next: () => fail('expected the request to fail'),
        error: (flattened: ErrorApi) => resolve(flattened),
      });
      httpMock.expectOne(URL).flush(body, { status, statusText: 'Error' });
    });
  }

  it('joins a DRF error array without indexing it', async () => {
    // `Object.entries` over an array produced "0: La unidad organizacional…",
    // which leaked the index into the operator-facing message.
    const flattened = await flatten(
      { error: ['La unidad organizacional no pertenece a la gestión fiscal.'], status_code: 400 },
      400,
    );

    expect(flattened.message)
      .toBe('La unidad organizacional no pertenece a la gestión fiscal.');
    expect(flattened.status).toBe(400);
  });

  it('joins several messages of the same array', async () => {
    const flattened = await flatten({ error: ['Primero.', 'Segundo.'] }, 400);

    expect(flattened.message).toBe('Primero. Segundo.');
  });

  it('keeps the domain contract {detail, code}', async () => {
    const flattened = await flatten(
      { error: { detail: 'Gestión no habilitada.', code: 'gestion_no_habilitada' } },
      409,
    );

    expect(flattened.message).toBe('Gestión no habilitada.');
    expect(flattened.code).toBe('gestion_no_habilitada');
  });

  it('labels field errors with their field', async () => {
    const flattened = await flatten({ rol_codigo: ['Este campo es requerido.'] }, 400);

    expect(flattened.message).toBe('rol_codigo: Este campo es requerido.');
  });

  it('logs the user out on 401', async () => {
    await flatten({ detail: 'Token inválido.' }, 401);

    expect(auth.logout).toHaveBeenCalled();
  });

  it('does not log the user out on 403', async () => {
    await flatten({ error: ['Sin autoridad.'] }, 403);

    expect(auth.logout).not.toHaveBeenCalled();
  });

  it('surfaces a transport failure as an ErrorApi, not an HttpErrorResponse', async () => {
    const flattened = await flatten(null, 0);

    expect(flattened instanceof HttpErrorResponse).toBeFalse();
    expect(flattened.status).toBe(0);
  });
});
