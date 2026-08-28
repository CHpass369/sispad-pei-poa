import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { AdminUsuariosModule } from './admin-usuarios.module';
import {
  AdminRegistrationRequest,
  AdminRole,
  AdminUsuariosService,
} from './admin-usuarios.service';
import {
  RequestApprovalDialogComponent,
  RequestApprovalDialogData,
} from './request-approval-dialog.component';

describe('RequestApprovalDialogComponent', () => {
  let component: RequestApprovalDialogComponent;
  let fixture: ComponentFixture<RequestApprovalDialogComponent>;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let auth: jasmine.SpyObj<AuthService>;
  let dialogRef: jasmine.SpyObj<MatDialogRef<RequestApprovalDialogComponent>>;
  let fiscalManagement: jasmine.SpyObj<GestionHabilitadaService>;

  const requestedUnit: PublicOrganizationalUnit = {
    id: 'unit-requested',
    codigo: 'DPL',
    nombre: 'Dirección de Planificación',
    sigla: 'DPL',
    padre: null,
  };
  const otherUnit: PublicOrganizationalUnit = {
    ...requestedUnit,
    id: 'unit-other',
    codigo: 'DAF',
    nombre: 'Dirección Administrativa',
  };
  const request: AdminRegistrationRequest = {
    id: 'request-1',
    email: 'pending@gob.bo',
    first_name: 'Elena',
    last_name: 'Pendiente',
    cargo: 'Analista',
    date_joined: '2026-08-25T10:00:00Z',
    unidad_solicitada: { id: requestedUnit.id, nombre: requestedUnit.nombre },
    solicita_encargado_unidad: false,
    rol_sugerido: 'VALIDADOR_POAU',
  };
  const baseRole: AdminRole = {
    id: 'role-base',
    codigo: 'JEFE_PE',
    nombre: 'Jefatura PE',
    descripcion: '',
    activo: true,
    es_sistema: true,
    deprecated: false,
    orden: 1,
    sistemas: ['sis_pe'],
    capacidades: [],
  };
  const customMultiRole: AdminRole = {
    ...baseRole,
    id: 'role-custom',
    codigo: 'CUSTOM_MULTI',
    nombre: 'Rol mixto',
    es_sistema: false,
    sistemas: ['accounts', 'sis_pe', 'sis_poa'],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService',
      ['listRoles', 'approveRequest'],
    );
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['listPublicOrganizationalUnits']);
    dialogRef = jasmine.createSpyObj<MatDialogRef<RequestApprovalDialogComponent>>(
      'MatDialogRef',
      ['close'],
    );
    fiscalManagement = jasmine.createSpyObj<GestionHabilitadaService>(
      'GestionHabilitadaService',
      ['gestion'],
    );
    adminUsers.listRoles.and.returnValue(of([baseRole, customMultiRole]));
    auth.listPublicOrganizationalUnits.and.returnValue(of([otherUnit, requestedUnit]));
    fiscalManagement.gestion.and.returnValue({
      id: 'fiscal-2027',
      anio: 2027,
      estado: 'HABILITADA',
      estado_display: 'Habilitada',
      fecha_apertura: null,
      fecha_cierre: null,
    });

    const data: RequestApprovalDialogData = { request };
    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: data },
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: AdminUsuariosService, useValue: adminUsers },
        { provide: AuthService, useValue: auth },
        { provide: GestionHabilitadaService, useValue: fiscalManagement },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RequestApprovalDialogComponent);
    component = fixture.componentInstance;
  });

  it('preselects the requested organizational unit from the real catalog', () => {
    fixture.detectChanges();

    expect(auth.listPublicOrganizationalUnits).toHaveBeenCalled();
    expect(component.unitId).toBe(requestedUnit.id);
    expect(component.organizationalUnits.map(unit => unit.id)).toContain(requestedUnit.id);
  });

  it('derives the single role system and fixed base-role scope', () => {
    fixture.detectChanges();

    expect(component.roleCode).toBe('JEFE_PE');
    expect(component.availableSystems).toEqual(['sis_pe']);
    expect(component.system).toBe('sis_pe');
    expect(component.showSystemSelector).toBeFalse();
    expect(component.fixedScope).toBe('GLOBAL');
    expect(component.approvalPayload().scope_type).toBe('GLOBAL');
  });

  it('preselects the role the applicant declaration points to', () => {
    const validator: AdminRole = {
      ...baseRole,
      id: 'role-validator',
      codigo: 'VALIDADOR_POAU',
      nombre: 'Validador POAU de unidad',
      sistemas: ['sis_poa'],
    };
    adminUsers.listRoles.and.returnValue(of([baseRole, validator]));

    fixture.detectChanges();

    expect(component.roleCode).toBe('VALIDADOR_POAU');
    expect(component.fixedScope).toBe('SELF');
    expect(component.approvalPayload().scope_type).toBe('SELF');
  });

  it('falls back to the first role when the suggestion is not assignable', () => {
    // The suggestion is advisory: an administrator who cannot assign that role
    // must not end up with it preselected.
    fixture.detectChanges();

    expect(component.roleCode).toBe('JEFE_PE');
  });

  it('offers only valid systems and selectable scope for a custom multi-system role', () => {
    fixture.detectChanges();
    component.roleCode = customMultiRole.codigo;
    component.roleChanged();

    expect(component.availableSystems).toEqual(['sis_pe', 'sis_poa']);
    expect(component.showSystemSelector).toBeTrue();
    expect(component.showScopeSelector).toBeTrue();
    component.system = 'sis_poa';
    component.scope = 'DESCENDANTS';
    expect(component.approvalPayload().scope_type).toBe('DESCENDANTS');
    expect(component.approvalPayload().fiscal_year_id).toBe('fiscal-2027');
  });

  it('clears `saving` BEFORE closing, so closePredicate cannot deadlock it', () => {
    // requests-admin-tab abre este diálogo con
    // `closePredicate: () => !instance.saving` para que ni ESC ni el backdrop
    // corten una aprobación en vuelo. Si el camino de éxito cierra con
    // `saving` todavía en true, el predicado rechaza el cierre y `close()`
    // retorna en silencio: el diálogo queda en «Aprobando…» para siempre
    // aunque el backend haya respondido 200.
    fixture.detectChanges();
    let savingAlCerrar: boolean | null = null;
    dialogRef.close.and.callFake(() => {
      savingAlCerrar = component.saving;
    });
    adminUsers.approveRequest.and.returnValue(of({
      id: request.id,
      email: request.email,
      first_name: request.first_name,
      last_name: request.last_name,
      estado: 'ACTIVO',
      activo: true,
      roles: [baseRole.codigo],
    }));

    component.approve();

    expect(dialogRef.close).toHaveBeenCalled();
    expect(savingAlCerrar).toBeFalse();
  });

  it('posts the exact approval payload and never adds privilege fields', () => {
    fixture.detectChanges();
    component.roleCode = customMultiRole.codigo;
    component.roleChanged();
    component.system = 'sis_poa';
    component.scope = 'DESCENDANTS';
    component.unitId = otherUnit.id;
    adminUsers.approveRequest.and.returnValue(of({
      id: request.id,
      email: request.email,
      first_name: request.first_name,
      last_name: request.last_name,
      estado: 'ACTIVO',
      activo: true,
      roles: [customMultiRole.codigo],
    }));

    component.approve();

    expect(adminUsers.approveRequest).toHaveBeenCalledOnceWith(request.id, {
      unidad_organizacional_id: otherUnit.id,
      rol_codigo: customMultiRole.codigo,
      scope_type: 'DESCENDANTS',
      sistema: 'sis_poa',
      fiscal_year_id: 'fiscal-2027',
    });
    const payload = adminUsers.approveRequest.calls.mostRecent().args[1] as unknown as Record<string, unknown>;
    expect(payload['password']).toBeUndefined();
    expect(payload['is_staff']).toBeUndefined();
    expect(payload['roles']).toBeUndefined();
    expect(dialogRef.close).toHaveBeenCalledWith({ approved: true, requestId: request.id });
  });

  it('sends null fiscal year for SIS-PE or when no enabled fiscal year exists', () => {
    fixture.detectChanges();
    expect(component.approvalPayload().fiscal_year_id).toBeNull();

    component.roleCode = customMultiRole.codigo;
    component.roleChanged();
    component.system = 'sis_poa';
    component.fiscalYear = null;
    expect(component.approvalPayload().fiscal_year_id).toBeNull();
  });

  it('prevents closing while approval is in progress', () => {
    component.saving = true;
    component.close();
    expect(dialogRef.close).not.toHaveBeenCalled();

    component.saving = false;
    component.close();
    expect(dialogRef.close).toHaveBeenCalled();
  });

  for (const status of [400, 403]) {
    it(`keeps selections and shows backend error after ${status}`, () => {
      fixture.detectChanges();
      component.roleCode = customMultiRole.codigo;
      component.roleChanged();
      component.system = 'sis_poa';
      component.scope = 'GLOBAL';
      component.unitId = otherUnit.id;
      adminUsers.approveRequest.and.returnValue(throwError(() => new HttpErrorResponse({
        status,
        error: { error: status === 403 ? 'Sin autoridad.' : 'Combinación inválida.' },
      })));

      component.approve();

      expect(component.unitId).toBe(otherUnit.id);
      expect(component.roleCode).toBe(customMultiRole.codigo);
      expect(component.system).toBe('sis_poa');
      expect(component.scope).toBe('GLOBAL');
      expect(component.approvalError).toContain(status === 403 ? 'Sin autoridad' : 'Combinación inválida');
      expect(dialogRef.close).not.toHaveBeenCalled();
    });
  }
});
