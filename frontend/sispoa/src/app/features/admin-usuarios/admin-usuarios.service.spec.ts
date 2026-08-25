import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import { AdminUser, AdminUsuariosService } from './admin-usuarios.service';

describe('AdminUsuariosService', () => {
  let service: AdminUsuariosService;
  let http: HttpTestingController;

  const user: AdminUser = {
    id: 'user-1',
    first_name: 'Ana',
    last_name: 'Planificadora',
    email: 'ana@gob.bo',
    cargo: 'Especialista',
    estado: 'ACTIVO',
    activo: true,
    is_active: true,
    last_login: null,
    roles: [],
    alcances: [],
    sistemas: ['sis_pe'],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AdminUsuariosService],
    });
    service = TestBed.inject(AdminUsuariosService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('builds V2 query params and parses the paginated response', () => {
    let resultCount = 0;
    service.listUsers({
      search: '  Ana  ',
      organizational_unit: 'unit-1',
      role: '  ANALISTA_PE ',
      system: 'sis_pe',
      state: 'ACTIVO',
    }, 3).subscribe(page => {
      resultCount = page.count;
      expect(page.results).toEqual([user]);
      expect(page.next).toContain('page=4');
    });

    const request = http.expectOne(req => req.url === `${environment.apiUrlV2}/admin/users/`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('page')).toBe('3');
    expect(request.request.params.get('search')).toBe('Ana');
    expect(request.request.params.get('organizational_unit')).toBe('unit-1');
    expect(request.request.params.get('role')).toBe('ANALISTA_PE');
    expect(request.request.params.get('system')).toBe('sis_pe');
    expect(request.request.params.get('state')).toBe('ACTIVO');
    request.flush({
      count: 26,
      next: '/api/v2/admin/users/?page=4',
      previous: '/api/v2/admin/users/?page=2',
      results: [user],
    });

    expect(resultCount).toBe(26);
  });

  it('omits empty optional filters', () => {
    service.listUsers({ search: ' ', role: '' }).subscribe();

    const request = http.expectOne(req => req.url === `${environment.apiUrlV2}/admin/users/`);
    expect(request.request.params.keys()).toEqual(['page']);
    request.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('uses V2 detail and state-action URLs', () => {
    service.getUser(user.id).subscribe();
    http.expectOne(`${environment.apiUrlV2}/admin/users/${user.id}/`).flush(user);

    service.activate(user.id).subscribe();
    const activate = http.expectOne(`${environment.apiUrlV2}/admin/users/${user.id}/activate/`);
    expect(activate.request.method).toBe('POST');
    expect(activate.request.body).toEqual({});
    activate.flush(user);

    service.deactivate(user.id).subscribe();
    const deactivate = http.expectOne(`${environment.apiUrlV2}/admin/users/${user.id}/deactivate/`);
    expect(deactivate.request.method).toBe('POST');
    deactivate.flush(user);
  });
});
