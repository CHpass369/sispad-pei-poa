import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import {
  AdminRole,
  AdminRoleCreate,
  AdminRolePatch,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { adminApiErrorMessage } from './admin-api-error';

export interface RoleFormDialogData {
  mode: 'create' | 'edit';
  role?: AdminRole;
}

@Component({
  standalone: false,
  selector: 'app-role-form-dialog',
  templateUrl: './role-form-dialog.component.html',
  styleUrl: './role-form-dialog.component.scss',
})
export class RoleFormDialogComponent {
  code = '';
  name = '';
  description = '';
  active = true;
  order = 0;
  saving = false;
  error = '';

  constructor(
    @Inject(MAT_DIALOG_DATA) public readonly data: RoleFormDialogData,
    private readonly dialogRef: MatDialogRef<RoleFormDialogComponent, AdminRole>,
    private readonly adminUsers: AdminUsuariosService,
  ) {
    if (data.role) {
      this.code = data.role.codigo;
      this.name = data.role.nombre;
      this.description = data.role.descripcion;
      this.active = data.role.activo;
      this.order = data.role.orden;
    }
  }

  get isCreate(): boolean {
    return this.data.mode === 'create';
  }

  get isSystemRole(): boolean {
    return Boolean(this.data.role?.es_sistema);
  }

  normalizeCode(value: string): void {
    this.code = value.toUpperCase().replace(/[^A-Z0-9_]/g, '');
  }

  submit(): void {
    if (this.saving || this.isSystemRole) {
      return;
    }
    this.error = '';
    this.saving = true;
    const request = this.isCreate
      ? this.adminUsers.createRole(this.createPayload())
      : this.adminUsers.patchRole(this.data.role!.id, this.patchPayload());
    request.subscribe({
      next: role => this.dialogRef.close(role),
      error: error => {
        this.error = adminApiErrorMessage(
          error,
          this.isCreate
            ? 'No se pudo crear el rol personalizado.'
            : 'No se pudo actualizar el rol personalizado.',
        );
        this.saving = false;
      },
    });
  }

  close(): void {
    this.dialogRef.close();
  }

  private createPayload(): AdminRoleCreate {
    return {
      codigo: this.code.trim().toUpperCase(),
      nombre: this.name.trim(),
      descripcion: this.description.trim(),
      activo: this.active,
    };
  }

  private patchPayload(): AdminRolePatch {
    return {
      nombre: this.name.trim(),
      descripcion: this.description.trim(),
      activo: this.active,
      orden: this.order,
    };
  }
}
