import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import {
  LoginRequest,
  LoginResponse,
  RegistrationRequest,
  Usuario,
} from '../models/usuario.model';
import { environment } from '../../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  const tokenKey = environment.tokenKey;

  const mockUser: Usuario = {
    id: '1',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    cargo: 'Técnico',
    telefono: '7777777',
    roles: ['superadmin'],
    roles_detalle: [{ id: '1', codigo: 'superadmin', nombre: 'Super Admin', descripcion: '', activo: true }],
    activo: true,
    is_staff: true,
    is_superuser: true,
    debe_cambiar_password: false,
    last_login: '2024-01-01',
    date_joined: '2024-01-01',
  };

  const mockLoginResponse: LoginResponse = {
    access: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxfQ.signature',
    refresh: 'refresh-token-value',
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should send POST request with correct credentials', () => {
      const credentials: LoginRequest = { email: 'test@example.com', password: '123456' };

      service.login(credentials).subscribe(res => {
        expect(res).toEqual(mockUser);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(credentials);
      req.flush(mockLoginResponse);

      const userReq = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      userReq.flush(mockUser);
    });

    it('should store token in localStorage after login', () => {
      const credentials: LoginRequest = { email: 'test@example.com', password: '123456' };

      service.login(credentials).subscribe(() => {
        const stored = localStorage.getItem(tokenKey);
        expect(stored).toBeTruthy();
        const parsed = JSON.parse(stored!);
        expect(parsed.access).toBe(mockLoginResponse.access);
        expect(parsed.refresh).toBe(mockLoginResponse.refresh);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      req.flush(mockLoginResponse);

      const userReq = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      userReq.flush(mockUser);
    });
  });

  describe('public registration V2', () => {
    const registration: RegistrationRequest = {
      first_name: 'Ana',
      last_name: 'Pérez',
      email: 'ana.perez@sacaba.gob.bo',
      cargo: 'Analista',
      unidad_organizacional_id: 'b41aec54-c047-438c-b5df-a32d47f0ee65',
      es_encargado_unidad: false,
      password: 'Clave.Segura.2026',
      password_confirm: 'Clave.Segura.2026',
    };

    it('posts the exact payload to the V2 registration URL', () => {
      service.register(registration).subscribe(response => {
        expect(response.detail).toContain('administrador');
      });

      const req = httpMock.expectOne(`${environment.apiUrlV2}/auth/register/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(registration);
      expect(req.request.url).not.toContain('/api/v1/api/v1');
      req.flush({ detail: 'Registro recibido. Un administrador revisará su solicitud.' });
    });

    it('lists public organizational units with an optional search', () => {
      service.listPublicOrganizationalUnits(' planificación ').subscribe(units => {
        expect(units[0].codigo).toBe('DIR-PLA');
      });

      const req = httpMock.expectOne(request => (
        request.url === `${environment.apiUrlV2}/auth/organizational-units/`
        && request.params.get('search') === 'planificación'
      ));
      expect(req.request.method).toBe('GET');
      expect(req.request.urlWithParams).not.toContain('/api/v1/api/v1');
      req.flush([{
        id: registration.unidad_organizacional_id,
        codigo: 'DIR-PLA',
        nombre: 'Dirección de Planificación',
        sigla: 'DPLA',
        padre: null,
      }]);
    });

    it('does not persist tokens after registration', () => {
      service.register(registration).subscribe();

      httpMock.expectOne(`${environment.apiUrlV2}/auth/register/`).flush({
        detail: 'Registro recibido. Un administrador revisará su solicitud.',
      });

      expect(localStorage.getItem(tokenKey)).toBeNull();
    });
  });

  describe('logout', () => {
    it('should clear token from localStorage', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.logout();

      expect(localStorage.getItem(tokenKey)).toBeNull();
    });

    it('should emit null on user$ after logout', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.logout();

      service.user$.subscribe(user => {
        expect(user).toBeNull();
      });
    });
  });

  describe('getToken', () => {
    it('should return null when no token is stored', () => {
      expect(service.getToken()).toBeNull();
    });

    it('should return access token from stored response', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));
      expect(service.getToken()).toBe(mockLoginResponse.access);
    });

    it('should return null for invalid JSON in localStorage', () => {
      localStorage.setItem(tokenKey, 'invalid-json');
      expect(service.getToken()).toBeNull();
    });
  });

  describe('getRefreshToken', () => {
    it('should return null when no token is stored', () => {
      expect(service.getRefreshToken()).toBeNull();
    });

    it('should return refresh token from stored response', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));
      expect(service.getRefreshToken()).toBe(mockLoginResponse.refresh);
    });
  });

  describe('loadUser', () => {
    it('should load user data from API', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.loadUser();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockUser);

      service.user$.subscribe(user => {
        expect(user).toEqual(mockUser);
      });
    });

    it('should logout on API error', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.loadUser();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      req.error(new ErrorEvent('Network error'));

      service.user$.subscribe(user => {
        expect(user).toBeNull();
      });
      expect(localStorage.getItem(tokenKey)).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return false when no token', () => {
      expect(service.isAuthenticated()).toBeFalse();
    });

    it('should return true when token exists', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));
      expect(service.isAuthenticated()).toBeTrue();
    });
  });

  describe('hasRole', () => {
    it('should return true when user has the specified role', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.loadUser();
      const req = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      req.flush(mockUser);

      expect(service.hasRole('superadmin')).toBeTrue();
    });

    it('should return false when user does not have the specified role', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.loadUser();
      const req = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      req.flush(mockUser);

      expect(service.hasRole('planificador')).toBeFalse();
    });

    it('should return false when no user is loaded', () => {
      expect(service.hasRole('superadmin')).toBeFalse();
    });
  });

  describe('init', () => {
    it('should call loadUser when token exists', () => {
      localStorage.setItem(tokenKey, JSON.stringify(mockLoginResponse));

      service.init();

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`);
      expect(req).toBeTruthy();
      req.flush(mockUser);
    });

    it('should not make HTTP request when no token', () => {
      service.init();
      httpMock.verify();
    });
  });
});
