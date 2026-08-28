import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { AdminUsuariosModule } from './admin-usuarios.module';
import { AdminRole, AdminUsuariosService } from './admin-usuarios.service';
import { RoleFormDialogComponent, RoleFormDialogData } from './role-form-dialog.component';

describe('RoleFormDialogComponent', () => {
  let fixture: ComponentFixture<RoleFormDialogComponent>;
  let component: RoleFormDialogComponent;
  let adminUsers: jasmine.SpyObj<AdminUsuariosService>;
  let dialogRef: jasmine.SpyObj<MatDialogRef<RoleFormDialogComponent>>;
  let data: RoleFormDialogData;

  const role: AdminRole = {
    id: 'role-1',
    codigo: 'CUSTOM_PE',
    nombre: 'Rol PE',
    descripcion: 'Descripción',
    activo: true,
    es_sistema: false,
    deprecated: false,
    orden: 4,
    sistemas: ['sis_pe'],
    capacidades: [],
  };

  beforeEach(async () => {
    adminUsers = jasmine.createSpyObj<AdminUsuariosService>(
      'AdminUsuariosService', ['createRole', 'patchRole'],
    );
    dialogRef = jasmine.createSpyObj<MatDialogRef<RoleFormDialogComponent>>(
      'MatDialogRef', ['close'],
    );
    data = { mode: 'create' };
    adminUsers.createRole.and.returnValue(of(role));
    adminUsers.patchRole.and.returnValue(of(role));

    await TestBed.configureTestingModule({
      imports: [AdminUsuariosModule, NoopAnimationsModule],
      providers: [
        { provide: MAT_DIALOG_DATA, useFactory: () => data },
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: AdminUsuariosService, useValue: adminUsers },
      ],
    }).compileComponents();

    createComponent();
  });

  it('normalizes uppercase code and sends only the custom-role create payload', () => {
    component.normalizeCode('custom_role');
    component.name = '  Rol nuevo ';
    component.description = '  Descripción nueva ';
    component.active = true;

    component.submit();

    expect(adminUsers.createRole).toHaveBeenCalledOnceWith({
      codigo: 'CUSTOM_ROLE',
      nombre: 'Rol nuevo',
      descripcion: 'Descripción nueva',
      activo: true,
    });
    expect(dialogRef.close).toHaveBeenCalledWith(role);
  });

  it('keeps the dialog open and shows the backend 403 without inferring superuser', () => {
    adminUsers.createRole.and.returnValue(throwError(() => ({
      status: 403,
      error: { detail: 'Solo un superusuario puede crear roles personalizados.' },
    })));
    component.code = 'CUSTOM_ROLE';
    component.name = 'Rol nuevo';

    component.submit();
    fixture.detectChanges();

    expect(component.error).toContain('Solo un superusuario');
    expect(fixture.nativeElement.textContent).toContain('Solo un superusuario');
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('sends only editable custom-role fields on PATCH', () => {
    data.mode = 'edit';
    data.role = role;
    createComponent();
    component.name = ' Rol actualizado ';
    component.description = ' Nueva descripción ';
    component.active = false;
    component.order = 12;

    component.submit();

    expect(adminUsers.patchRole).toHaveBeenCalledOnceWith(role.id, {
      nombre: 'Rol actualizado',
      descripcion: 'Nueva descripción',
      activo: false,
      orden: 12,
    });
  });

  it('edits a system role through the existing PATCH form', () => {
    data.mode = 'edit';
    data.role = { ...role, codigo: 'SUPER_ADMIN', es_sistema: true };
    createComponent();

    component.submit();

    expect(adminUsers.patchRole).toHaveBeenCalledOnceWith(data.role.id, jasmine.any(Object));
  });

  function createComponent(): void {
    fixture = TestBed.createComponent(RoleFormDialogComponent);
    component = fixture.componentInstance;
  }
});
