import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import {
  AdminCapability,
  AdminRole,
  AdminRoleSystem,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { adminApiErrorMessage } from './admin-api-error';

export interface RoleCapabilitiesDialogData {
  role: AdminRole;
}

interface CapabilityGroup {
  system: AdminRoleSystem;
  label: string;
  capabilities: AdminCapability[];
}

@Component({
  standalone: false,
  selector: 'app-role-capabilities-dialog',
  templateUrl: './role-capabilities-dialog.component.html',
  styleUrl: './role-capabilities-dialog.component.scss',
})
export class RoleCapabilitiesDialogComponent implements OnInit {
  capabilities: AdminCapability[] = [];
  selectedCodes = new Set<string>();
  unsupportedAssignedCount = 0;
  search = '';
  loading = false;
  saving = false;
  loadError = '';
  saveError = '';

  constructor(
    @Inject(MAT_DIALOG_DATA) public readonly data: RoleCapabilitiesDialogData,
    private readonly dialogRef: MatDialogRef<RoleCapabilitiesDialogComponent, AdminRole>,
    private readonly adminUsers: AdminUsuariosService,
  ) {
    this.unsupportedAssignedCount = data.role.capacidades.filter(
      capability => !this.isSupported(capability),
    ).length;
    this.selectedCodes = new Set(
      data.role.capacidades
        .filter(capability => this.isSupported(capability))
        .map(capability => capability.codigo),
    );
  }

  ngOnInit(): void {
    this.loadCapabilities();
  }

  get groups(): CapabilityGroup[] {
    const query = this.search.trim().toLowerCase();
    const filtered = this.capabilities.filter(capability => {
      if (!query) {
        return true;
      }
      return capability.codigo.toLowerCase().includes(query)
        || capability.nombre.toLowerCase().includes(query)
        || capability.descripcion.toLowerCase().includes(query);
    });
    const groups: CapabilityGroup[] = [
      { system: 'sis_pe', label: 'SIS-PE', capabilities: [] },
      { system: 'sis_poa', label: 'SIS-POA', capabilities: [] },
      { system: 'accounts', label: 'Accounts', capabilities: [] },
    ];
    return groups.map(group => ({
      ...group,
      capabilities: filtered.filter(item => item.sistema === group.system),
    })).filter(group => group.capabilities.length > 0);
  }

  get selectedCount(): number {
    return this.selectedCodes.size;
  }

  loadCapabilities(): void {
    this.loading = true;
    this.loadError = '';
    this.adminUsers.listAllCapabilities().subscribe({
      next: capabilities => {
        this.capabilities = capabilities.filter(item => this.isSupported(item));
        this.loading = false;
      },
      error: error => {
        this.loadError = adminApiErrorMessage(
          error,
          'No se pudo cargar el catálogo de permisos.',
        );
        this.loading = false;
      },
    });
  }

  isSelected(code: string): boolean {
    return this.selectedCodes.has(code);
  }

  toggle(code: string, selected: boolean): void {
    const next = new Set(this.selectedCodes);
    if (selected) {
      next.add(code);
    } else {
      next.delete(code);
    }
    this.selectedCodes = next;
    this.saveError = '';
  }

  save(): void {
    if (this.saving) {
      return;
    }
    this.saving = true;
    this.saveError = '';
    const capabilityCodes = [...this.selectedCodes].sort();
    this.adminUsers.replaceRoleCapabilities(this.data.role.id, {
      capability_codes: capabilityCodes,
    }).subscribe({
      next: role => this.dialogRef.close(role),
      error: error => {
        this.saveError = adminApiErrorMessage(
          error,
          'No se pudieron reemplazar los permisos del rol.',
        );
        this.saving = false;
      },
    });
  }

  close(): void {
    this.dialogRef.close();
  }

  trackCapability(_index: number, capability: AdminCapability): string {
    return capability.id;
  }

  private isSupported(capability: AdminCapability): boolean {
    return ['sis_pe', 'sis_poa', 'accounts'].includes(capability.sistema)
      && !capability.codigo.startsWith('sis_pro.')
      && !capability.codigo.startsWith('sis-pro.');
  }
}
