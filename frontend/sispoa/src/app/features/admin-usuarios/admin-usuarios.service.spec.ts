import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import {
  AdminApprovalPayload,
  AdminCapability,
  AdminAccessPreviewResponse,
  AdminAssignmentInput,
  AdminAssignmentsPayload,
  AdminRegistrationRequest,
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

  const capability: AdminCapability = {
    id: 'capability-1',
    codigo: 'sis_pe.pad.view',
    nombre: 'Ver PAD',
    descripcion: 'Consulta del PAD',
    sistema: 'sis_pe',
    activo: true,
    orden: 1,
  };

  const registrationRequest: AdminRegistrationRequest = {
    id: 'request-1',
    email: 'pending@gob.bo',
    first_name: 'Elena',
    last_name: 'Pendiente',
    cargo: 'Analista',
    date_joined: '2026-08-25T10:00:00Z',
    unidad_solicitada: { id: 'unit-1', nombre: 'Planificación' },
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

  it('lists a backend role page with search, system, active and page filters', () => {
    service.listRolesPage({
      search: '  custom ',
      system: 'accounts',
      active: false,
    }, 2).subscribe();

    const request = http.expectOne(req => req.url === `${environment.apiUrlV2}/admin/roles/`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('search')).toBe('custom');
    expect(request.request.params.get('system')).toBe('accounts');
    expect(request.request.params.get('active')).toBe('false');
    expect(request.request.params.get('page')).toBe('2');
    request.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('uses strict role create, detail, patch and atomic capability URLs', () => {
    service.createRole({
      codigo: 'CUSTOM_CREATED',
      nombre: 'Rol creado',
      descripcion: 'Descripción',
      activo: true,
    }).subscribe();
    const create = http.expectOne(`${environment.apiUrlV2}/admin/roles/`);
    expect(create.request.method).toBe('POST');
    expect(create.request.body).toEqual({
      codigo: 'CUSTOM_CREATED',
      nombre: 'Rol creado',
      descripcion: 'Descripción',
      activo: true,
    });
    create.flush(role);

    service.getRole(role.id).subscribe();
    http.expectOne(`${environment.apiUrlV2}/admin/roles/${role.id}/`).flush(role);

    service.patchRole(role.id, {
      nombre: 'Actualizado', descripcion: '', activo: false, orden: 8,
    }).subscribe();
    const patch = http.expectOne(`${environment.apiUrlV2}/admin/roles/${role.id}/`);
    expect(patch.request.method).toBe('PATCH');
    expect(patch.request.body).toEqual({
      nombre: 'Actualizado', descripcion: '', activo: false, orden: 8,
    });
    patch.flush(role);

    service.deleteRole(role.id).subscribe();
    const remove = http.expectOne(`${environment.apiUrlV2}/admin/roles/${role.id}/`);
    expect(remove.request.method).toBe('DELETE');
    expect(remove.request.body).toBeNull();
    remove.flush(null);

    service.replaceRoleCapabilities(role.id, {
      capability_codes: [capability.codigo],
    }).subscribe();
    const replace = http.expectOne(
      `${environment.apiUrlV2}/admin/roles/${role.id}/capabilities/`,
    );
    expect(replace.request.method).toBe('PUT');
    expect(replace.request.body).toEqual({ capability_codes: [capability.codigo] });
    replace.flush({ ...role, capacidades: [capability] });
  });

  it('lists a paginated read-only capability catalog with backend filters', () => {
    service.listCapabilities({
      search: '  pad ', system: 'sis_pe', active: true,
    }, 3).subscribe();

    const request = http.expectOne(
      req => req.url === `${environment.apiUrlV2}/admin/capabilities/`,
    );
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('search')).toBe('pad');
    expect(request.request.params.get('system')).toBe('sis_pe');
    expect(request.request.params.get('active')).toBe('true');
    expect(request.request.params.get('page')).toBe('3');
    request.flush({ count: 1, next: null, previous: null, results: [capability] });
  });

  it('lists the selected requests page from the V2 backend', () => {
    service.listRequests(4).subscribe(page => {
      expect(page.count).toBe(26);
      expect(page.results).toEqual([registrationRequest]);
    });

    const request = http.expectOne(
      req => req.url === `${environment.apiUrlV2}/admin/solicitudes/`,
    );
    expect(request.request.method).toBe('GET');
    expect(request.request.params.keys()).toEqual(['page']);
    expect(request.request.params.get('page')).toBe('4');
    request.flush({
      count: 26,
      next: `${environment.apiUrlV2}/admin/solicitudes/?page=5`,
      previous: `${environment.apiUrlV2}/admin/solicitudes/?page=3`,
      results: [registrationRequest],
    });
  });

  it('posts the exact approval payload without privilege fields', () => {
    const payload: AdminApprovalPayload = {
      unidad_organizacional_id: 'unit-1',
      rol_codigo: 'CUSTOM_PE',
      scope_type: 'DESCENDANTS',
      sistema: 'sis_pe',
      fiscal_year_id: null,
    };
    service.approveRequest(registrationRequest.id, payload).subscribe();

    const request = http.expectOne(
      `${environment.apiUrlV2}/admin/users/${registrationRequest.id}/approve/`,
    );
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(payload);
    expect(request.request.body.password).toBeUndefined();
    expect(request.request.body.roles).toBeUndefined();
    expect(request.request.body.is_staff).toBeUndefined();
    request.flush({
      id: registrationRequest.id,
      email: registrationRequest.email,
      first_name: registrationRequest.first_name,
      last_name: registrationRequest.last_name,
      estado: 'ACTIVO',
      activo: true,
      roles: ['CUSTOM_PE'],
    });
  });

  it('loads every capability page for atomic role assignment', () => {
    let capabilities: AdminCapability[] = [];
    service.listAllCapabilities().subscribe(result => capabilities = result);

    const first = http.expectOne(
      req => req.url === `${environment.apiUrlV2}/admin/capabilities/`,
    );
    first.flush({
      count: 2,
      next: `${environment.apiUrlV2}/admin/capabilities/?page=2`,
      previous: null,
      results: [capability],
    });
    http.expectOne(`${environment.apiUrlV2}/admin/capabilities/?page=2`).flush({
      count: 2,
      next: null,
      previous: `${environment.apiUrlV2}/admin/capabilities/`,
      results: [{ ...capability, id: 'capability-2', codigo: 'accounts.rol.view', sistema: 'accounts' }],
    });

    expect(capabilities.map(item => item.codigo)).toEqual([
      'sis_pe.pad.view', 'accounts.rol.view',
    ]);
  });

  it('requests the typed unpaginated access preview with production assignments', () => {
    const assignments: AdminAssignmentInput[] = [{
      role_code: 'FORMULADOR_POAU',
      organizational_unit_id: 'unit-1',
      scope_type: 'SELF',
      fiscal_year_id: 'year-2026',
    }];
    const response: AdminAccessPreviewResponse = {
      capabilities: [{
        codigo: 'sis_poa.poau.view',
        nombre: 'Ver POAU',
        sistema: 'sis_poa',
        modulo: 'poau',
      }],
      effective_uos: [{ id: 'unit-1', codigo: 'UO-1', nombre: 'Unidad 1' }],
      modules: [{ codigo: 'poau', sistema: 'sis_poa', visible: true }],
    };
      let preview: AdminAccessPreviewResponse | undefined;
    service.previewAccess({ user_id: user.id, assignments }).subscribe(result => preview = result);

    const request = http.expectOne(req =>
      req.url === `${environment.apiUrlV2}/admin/preview-access/`,
    );
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('user_id')).toBe(user.id);
    expect(JSON.parse(request.request.params.get('assignments') ?? '')).toEqual(assignments);
    request.flush(response);

    expect(preview).toEqual(response);
    expect(Object.keys(preview ?? {})).toEqual(['capabilities', 'effective_uos', 'modules']);
    expect(preview?.capabilities[0]).toEqual(response.capabilities[0]);
    expect(preview?.effective_uos[0]).toEqual(response.effective_uos[0]);
    expect(preview?.modules[0]).toEqual(response.modules[0]);
  });

  it('omits assignments when previewing the current access', () => {
    service.previewAccess({ user_id: user.id }).subscribe();

    const request = http.expectOne(req =>
      req.url === `${environment.apiUrlV2}/admin/preview-access/`,
    );
    expect(request.request.params.keys()).toEqual(['user_id']);
    request.flush({ capabilities: [], effective_uos: [], modules: [] });
  });

});
