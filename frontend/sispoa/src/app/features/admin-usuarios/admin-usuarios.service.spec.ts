import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import {
  AdminAssignmentsPayload,
  AdminRole,
  AdminUser,
  AdminUsuariosService,
} from './admin-usuarios.service';

describe('AdminUsuariosService', () => {
  let service: AdminUsuariosService;
  let http: HttpTestingController;

  const user: AdminUser = {
    id: 'user-1',
    first_name: 'Ana',
    last_name: 'Planificadora',
    email: 'ana@gob.bo',
    cargo: 'Especialista',
    telefono: '4455667',
    estado: 'ACTIVO',
    activo: true,
    is_active: true,
    last_login: null,
    roles: [],
    alcances: [],
    sistemas: ['sis_pe'],
  };

  const role: AdminRole = {
    id: 'role-1',
    codigo: 'CUSTOM_PE',
    nombre: 'Rol PE',
    descripcion: '',
    activo: true,
    es_sistema: false,
    deprecated: false,
    orden: 1,
    sistemas: ['sis_pe'],
    capacidades: [],
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
    let detailPhone = '';
    service.getUser(user.id).subscribe(result => detailPhone = result.telefono);
    http.expectOne(`${environment.apiUrlV2}/admin/users/${user.id}/`).flush(user);
    expect(detailPhone).toBe('4455667');

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

  it('patches only the provided personal fields', () => {
    service.patchUser(user.id, {
      first_name: 'Ana María',
      cargo: 'Jefa de unidad',
      telefono: '70000001',
    }).subscribe();

    const request = http.expectOne(`${environment.apiUrlV2}/admin/users/${user.id}/`);
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toEqual({
      first_name: 'Ana María',
      cargo: 'Jefa de unidad',
      telefono: '70000001',
    });
    expect(request.request.body.roles).toBeUndefined();
    expect(request.request.body.assignments).toBeUndefined();
    request.flush(user);
  });

  it('uses the assignments GET and atomic PUT contracts', () => {
    const payload: AdminAssignmentsPayload = {
      assignments: [{
        role_code: role.codigo,
        organizational_unit_id: 'unit-1',
        scope_type: 'DESCENDANTS',
        fiscal_year_id: null,
      }],
    };

    service.getAssignments(user.id).subscribe();
    const getRequest = http.expectOne(
      `${environment.apiUrlV2}/admin/users/${user.id}/assignments/`,
    );
    expect(getRequest.request.method).toBe('GET');
    getRequest.flush(user);

    service.putAssignments(user.id, payload).subscribe();
    const putRequest = http.expectOne(
      `${environment.apiUrlV2}/admin/users/${user.id}/assignments/`,
    );
    expect(putRequest.request.method).toBe('PUT');
    expect(putRequest.request.body).toEqual(payload);
    putRequest.flush(user);
  });

  it('loads every active role page from the V2 backend', () => {
    let roles: AdminRole[] = [];
    service.listRoles().subscribe(result => roles = result);

    const first = http.expectOne(req => req.url === `${environment.apiUrlV2}/admin/roles/`);
    expect(first.request.params.get('active')).toBe('true');
    first.flush({
      count: 2,
      next: `${environment.apiUrlV2}/admin/roles/?active=true&page=2`,
      previous: null,
      results: [role],
    });
    const second = http.expectOne(
      `${environment.apiUrlV2}/admin/roles/?active=true&page=2`,
    );
    second.flush({
      count: 2,
      next: null,
      previous: `${environment.apiUrlV2}/admin/roles/?active=true`,
      results: [{ ...role, id: 'role-2', codigo: 'CUSTOM_POA', sistemas: ['sis_poa'] }],
    });

    expect(roles.map(item => item.codigo)).toEqual(['CUSTOM_PE', 'CUSTOM_POA']);
  });
});
