import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { PageEvent } from '@angular/material/paginator';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import {
  AdminCatalogFilters,
  AdminRole,
  AdminUsuariosService,
} from './admin-usuarios.service';
import { RoleCapabilitiesDialogComponent } from './role-capabilities-dialog.component';
import { RoleFormDialogComponent } from './role-form-dialog.component';

@Component({
  standalone: false,
  selector: 'app-roles-admin-tab',
  templateUrl: './roles-admin-tab.component.html',
  styleUrl: './roles-admin-tab.component.scss',
})
export class RolesAdminTabComponent implements OnInit {
  readonly displayedColumns = [
    'codigo', 'nombre', 'sistemas', 'capacidades', 'estado', 'tipo', 'acciones',
  ];
  readonly pageSize = 25;

  filters: AdminCatalogFilters = {};
  roles: AdminRole[] = [];
  totalRoles = 0;
  pageIndex = 0;
  loading = false;
  error = '';

  constructor(
    private readonly adminUsers: AdminUsuariosService,
    private readonly capabilities: CapabilitiesService,
    private readonly dialog: MatDialog,
  ) {}

  ngOnInit(): void {
    this.loadRoles();
  }

  get canCreate(): boolean {
    return this.capabilities.tiene('accounts.rol.create');
  }

  get canEdit(): boolean {
    return this.capabilities.tiene('accounts.rol.edit');
  }

  get canAssignCapabilities(): boolean {
    return this.capabilities.tiene('accounts.capacidad.assign');
  }

  applyFilters(): void {
    this.pageIndex = 0;
    this.loadRoles();
  }

  clearFilters(): void {
    this.filters = {};
    this.pageIndex = 0;
    this.loadRoles();
  }

  changePage(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.loadRoles();
  }

  loadRoles(): void {
    this.loading = true;
    this.error = '';
    this.adminUsers.listRolesPage(this.filters, this.pageIndex + 1).subscribe({
      next: page => {
        this.roles = page.results;
        this.totalRoles = page.count;
        this.loading = false;
      },
      error: () => {
        this.roles = [];
        this.totalRoles = 0;
        this.error = 'No se pudo cargar el catálogo de roles.';
        this.loading = false;
      },
    });
  }

  openCreate(): void {
    if (!this.canCreate) {
      return;
    }
    this.dialog.open(RoleFormDialogComponent, {
      data: { mode: 'create' },
      width: '38rem',
      maxWidth: '96vw',
      autoFocus: 'first-header',
      restoreFocus: true,
      ariaLabelledBy: 'role-form-title',
      ariaDescribedBy: 'role-form-description',
    }).afterClosed().subscribe((role: AdminRole | undefined) => {
      if (role) {
        this.pageIndex = 0;
        this.loadRoles();
      }
    });
  }

  openEdit(role: AdminRole): void {
    if (!this.canEdit || role.es_sistema) {
      return;
    }
    this.dialog.open(RoleFormDialogComponent, {
      data: { mode: 'edit', role },
      width: '38rem',
      maxWidth: '96vw',
      autoFocus: 'first-header',
      restoreFocus: true,
      ariaLabelledBy: 'role-form-title',
      ariaDescribedBy: 'role-form-description',
    }).afterClosed().subscribe((updated: AdminRole | undefined) => {
      if (updated) {
        this.updateRole(updated);
      }
    });
  }

  openCapabilities(role: AdminRole): void {
    if (!this.canAssignCapabilities || role.es_sistema) {
      return;
    }
    this.dialog.open(RoleCapabilitiesDialogComponent, {
      data: { role },
      width: '58rem',
      maxWidth: '96vw',
      maxHeight: '94vh',
      autoFocus: 'first-header',
      restoreFocus: true,
      ariaLabelledBy: 'role-capabilities-title',
      ariaDescribedBy: 'role-capabilities-description',
    }).afterClosed().subscribe((updated: AdminRole | undefined) => {
      if (updated) {
        this.updateRole(updated);
      }
    });
  }

  systemLabel(system: string): string {
    if (system === 'sis_pe') {
      return 'SIS-PE';
    }
    if (system === 'sis_poa') {
      return 'SIS-POA';
    }
    return system === 'accounts' ? 'Accounts' : system.toUpperCase();
  }

  capabilitySummary(role: AdminRole): string[] {
    return role.capacidades.slice(0, 2).map(capability => capability.codigo);
  }

  trackRole(_index: number, role: AdminRole): string {
    return role.id;
  }

  private updateRole(updated: AdminRole): void {
    this.roles = this.roles.map(role => role.id === updated.id ? updated : role);
  }
}
