import { Component, OnInit } from '@angular/core';
import { PageEvent } from '@angular/material/paginator';
import {
  AdminCapability,
  AdminCatalogFilters,
  AdminUsuariosService,
} from './admin-usuarios.service';

@Component({
  standalone: false,
  selector: 'app-permissions-admin-tab',
  templateUrl: './permissions-admin-tab.component.html',
  styleUrl: './permissions-admin-tab.component.scss',
})
export class PermissionsAdminTabComponent implements OnInit {
  readonly displayedColumns = ['codigo', 'nombre', 'sistema', 'descripcion', 'estado'];
  readonly pageSize = 25;

  filters: AdminCatalogFilters = {};
  capabilities: AdminCapability[] = [];
  totalCapabilities = 0;
  pageIndex = 0;
  loading = false;
  error = '';

  constructor(private readonly adminUsers: AdminUsuariosService) {}

  ngOnInit(): void {
    this.loadCapabilities();
  }

  applyFilters(): void {
    this.pageIndex = 0;
    this.loadCapabilities();
  }

  clearFilters(): void {
    this.filters = {};
    this.pageIndex = 0;
    this.loadCapabilities();
  }

  changePage(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.loadCapabilities();
  }

  loadCapabilities(): void {
    this.loading = true;
    this.error = '';
    this.adminUsers.listCapabilities(this.filters, this.pageIndex + 1).subscribe({
      next: page => {
        this.capabilities = page.results.filter(item => this.isVisible(item));
        this.totalCapabilities = page.count;
        this.loading = false;
      },
      error: () => {
        this.capabilities = [];
        this.totalCapabilities = 0;
        this.error = 'No se pudo cargar el catálogo de permisos.';
        this.loading = false;
      },
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

  trackCapability(_index: number, capability: AdminCapability): string {
    return capability.id;
  }

  private isVisible(capability: AdminCapability): boolean {
    return !capability.codigo.startsWith('sis_pro.')
      && !capability.codigo.startsWith('sis-pro.');
  }
}
