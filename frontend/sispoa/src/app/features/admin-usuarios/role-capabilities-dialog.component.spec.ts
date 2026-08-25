import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { AdminCapability, AdminRole, AdminUsuariosService } from './admin-usuarios.service';
import {
  RoleCapabilitiesDialogComponent,
  RoleCapabilitiesDialogData,
} from './role-capabilities-dialog.component';

describe('RoleCapabilitiesDialogComponent', () => {
  let fixture: ComponentFixture<RoleCapabilitiesDialogComponent>;
  let component: RoleCapabilitiesDialogComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let dialogRef: jasmine.SpyObj<MatDialogRef<RoleCapabilitiesDialogComponent>>;
  let data: RoleCapabilitiesDialogData;

  const peCapability: AdminCapability = {
    id: 'cap-pe',
    codigo: 'sis_pe.pad.view',
    nombre: 'Ver PAD',
    descripcion: 'Consulta PAD',
    sistema: 'sis_pe',
    activo: true,
    orden: 1,
  };
  const poaCapability: AdminCapability = {
    ...peCapability,
    id: 'cap-poa',
    codigo: 'sis_poa.poau.edit',
    nombre: 'Editar POAU',
    sistema: 'sis_poa',
  };
  const accountsCapability: AdminCapability = {
    ...peCapability,
    id: 'cap-accounts',
    codigo: 'accounts.usuario.view',
    nombre: 'Ver usuarios',
    sistema: 'accounts',
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
    capacidades: [peCapability],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService', ['listAllCapabilities', 'replaceRoleCapabilities'],
    );
    dialogRef = jasmine.createSpyObj<MatDialogRef<RoleCapabilitiesDialogComponent>>(
      'MatDialogRef', ['close'],
    );
    data = { role };
    adminUsers.listAllCapabilities.and.returnValue(of([
      peCapability, poaCapability, accountsCapability,
      {
        ...peCapability,
        id: 'cap-pro',
        codigo: 'sis_pro.project.view',
        sistema: 'sis_pro',
      } as unknown as AdminCapability,
    ]));
    adminUsers.replaceRoleCapabilities.and.returnValue(of(role));

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useFactory: () => data },
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: AdminUsuariosService, useValue: adminUsers },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RoleCapabilitiesDialogComponent);
    component = fixture.componentInstance;
  });

  it('loads and groups real SIS-PE, SIS-POA and accounts capabilities without SIS-PRO', () => {
    fixture.detectChanges();

    expect(component.groups.map(group => group.system)).toEqual([
      'sis_pe', 'sis_poa', 'accounts',
    ]);
    expect(component.capabilities.some(item => item.codigo.startsWith('sis_pro.'))).toBeFalse();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('SIS-PE');
    expect(text).toContain('SIS-POA');
    expect(text).toContain('Accounts');
    expect(text).not.toContain('sis_pro.project.view');
  });

  it('filters the assignable catalog by real capability data', () => {
    fixture.detectChanges();

    component.search = 'usuarios';

    expect(component.groups.length).toBe(1);
    expect(component.groups[0].system).toBe('accounts');
    expect(component.groups[0].capabilities.map(item => item.codigo)).toEqual([
      'accounts.usuario.view',
    ]);
  });

  it('replaces capability codes atomically with the current selection', () => {
    fixture.detectChanges();
    component.toggle(peCapability.codigo, false);
    component.toggle(poaCapability.codigo, true);
    component.toggle(accountsCapability.codigo, true);

    component.save();

    expect(adminUsers.replaceRoleCapabilities).toHaveBeenCalledOnceWith(role.id, {
      capability_codes: ['accounts.usuario.view', 'sis_poa.poau.edit'],
    });
    expect(dialogRef.close).toHaveBeenCalledWith(role);
  });

  it('keeps the selection and dialog open when the atomic PUT fails', () => {
    fixture.detectChanges();
    component.toggle(poaCapability.codigo, true);
    const before = [...component.selectedCodes].sort();
    adminUsers.replaceRoleCapabilities.and.returnValue(throwError(() => ({
      status: 400,
      error: { capability_codes: ['No puede asignar capacidades fuera de su sistema.'] },
    })));

    component.save();
    fixture.detectChanges();

    expect([...component.selectedCodes].sort()).toEqual(before);
    expect(component.saveError).toContain('No puede asignar capacidades');
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('does not load or mutate a system role', () => {
    data.role = { ...role, es_sistema: true };
    adminUsers.listAllCapabilities.calls.reset();
    adminUsers.replaceRoleCapabilities.calls.reset();
    fixture = TestBed.createComponent(RoleCapabilitiesDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.save();

    expect(adminUsers.listAllCapabilities).not.toHaveBeenCalled();
    expect(adminUsers.replaceRoleCapabilities).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('roles del sistema son inmutables');
  });
});
