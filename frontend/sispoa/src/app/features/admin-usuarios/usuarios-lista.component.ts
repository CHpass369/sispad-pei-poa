import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { PageEvent } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { Observable, takeUntil } from 'rxjs';
import { PublicOrganizationalUnit } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import {
  AdminSystem,
  AdminUser,
  AdminUserFilters,
  AdminUserState,
  AdminUsuariosService,
} from './admin-usuarios.service';
import {
  UsuarioEdicionDialogComponent,
  UsuarioEdicionDialogData,
  UsuarioEdicionDialogResult,
} from './usuario-edicion-dialog.component';

@Component({
  standalone: false,
  selector: 'app-usuarios-lista',
  templateUrl: './usuarios-lista.component.html',
  styleUrl: './usuarios-lista.component.scss',
})
export class UsuariosListaComponent implements OnInit {
  @ViewChild('detalleTitulo') private detailHeading?: ElementRef<HTMLHeadingElement>;

  readonly displayedColumns = [
    'usuario',
    'cargo',
    'unidad',
    'rol',
    'sistema',
    'estado',
    'ultimoAcceso',
    'acciones',
  ];
  readonly pageSize = 25;

  filters: AdminUserFilters = {};
  users: AdminUser[] = [];
  organizationalUnits: PublicOrganizationalUnit[] = [];
  totalUsers = 0;
  pageIndex = 0;
  loading = false;
  error = '';
  catalogError = '';
  actionError = '';
  selectedUser: AdminUser | null = null;
  detailLoading = false;
  detailError = '';
  stateChangeUserId: string | null = null;
  selectedTabIndex = 0;

  constructor(
    private readonly adminUsers: AdminUsuariosService,
    private readonly auth: AuthService,
    private readonly capabilities: CapabilitiesService,
    private readonly dialog: MatDialog,
  ) {}

  ngOnInit(): void {
    if (this.canViewUsers) {
      this.loadOrganizationalUnits();
      this.loadUsers();
    }
  }

  get canViewUsers(): boolean {
    return this.capabilities.tiene('accounts.usuario.view');
  }

  get canViewRoles(): boolean {
    return this.capabilities.tiene('accounts.rol.view');
  }

  get canViewCapabilities(): boolean {
    return this.capabilities.tiene('accounts.capacidad.view');
  }

  get canViewRequests(): boolean {
    return this.capabilities.tiene('accounts.solicitud.view');
  }

  get canChangeUserState(): boolean {
    return this.capabilities.tiene('accounts.usuario.activate');
  }

  get canEditUser(): boolean {
    return this.capabilities.tiene('accounts.usuario.edit');
  }

  get canViewAssignments(): boolean {
    return this.capabilities.tiene('accounts.alcance.view');
  }

  get canAssign(): boolean {
    return this.capabilities.tiene('accounts.alcance.assign');
  }

  get canOpenEditor(): boolean {
    return this.canEditUser || this.canViewAssignments;
  }

  applyFilters(): void {
    this.pageIndex = 0;
    this.loadUsers();
  }

  clearFilters(): void {
    this.filters = {};
    this.pageIndex = 0;
    this.loadUsers();
  }

  changePage(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.loadUsers();
  }

  loadUsers(): void {
    if (!this.canViewUsers) {
      return;
    }
    this.loading = true;
    this.error = '';
    this.actionError = '';
    this.adminUsers.listUsers(this.filters, this.pageIndex + 1).subscribe({
      next: page => {
        this.users = page.results;
        this.totalUsers = page.count;
        this.loading = false;
      },
      error: () => {
        this.users = [];
        this.totalUsers = 0;
        this.error = 'No se pudo cargar la lista de usuarios. Verifique su conexión e inténtelo nuevamente.';
        this.loading = false;
      },
    });
  }

  openDetail(user: AdminUser): void {
    this.selectedUser = null;
    this.detailLoading = true;
    this.detailError = '';
    this.adminUsers.getUser(user.id).subscribe({
      next: detail => {
        this.selectedUser = detail;
        this.detailLoading = false;
        setTimeout(() => this.detailHeading?.nativeElement.focus());
      },
      error: () => {
        this.selectedUser = user;
        this.detailLoading = false;
        this.detailError = 'No se pudo cargar el detalle actualizado. Inténtelo nuevamente.';
      },
    });
  }

  retryDetail(): void {
    if (this.selectedUser) {
      this.openDetail(this.selectedUser);
    }
  }

  closeDetail(): void {
    this.selectedUser = null;
    this.detailError = '';
  }

  openEditor(user: AdminUser): void {
    if (!this.canOpenEditor) {
      return;
    }
    const data: UsuarioEdicionDialogData = {
      user,
      organizationalUnits: this.organizationalUnits,
      canEditPersonal: this.canEditUser,
      canViewAssignments: this.canViewAssignments,
      canAssign: this.canViewAssignments && this.canAssign,
      canViewRequests: this.canViewRequests,
    };
    const dialogRef = this.dialog.open<
      UsuarioEdicionDialogComponent,
      UsuarioEdicionDialogData,
      UsuarioEdicionDialogResult
    >(UsuarioEdicionDialogComponent, {
      data,
      width: '64rem',
      maxWidth: '96vw',
      maxHeight: '94vh',
      autoFocus: 'first-header',
      restoreFocus: true,
      ariaLabelledBy: 'user-edit-title',
      ariaDescribedBy: 'user-edit-description',
      closePredicate: (_result, _config, component) => {
        const instance = component as UsuarioEdicionDialogComponent | null;
        return !instance?.hasUnsavedChanges()
          || instance.confirmDiscard();
      },
    });
    const closed$ = dialogRef.afterClosed();
    dialogRef.componentInstance.userSaved.pipe(takeUntil(closed$)).subscribe(
      updated => this.updateUser(updated),
    );
    closed$.subscribe(result => {
      if (result?.navigateToRequests) {
        this.selectedTabIndex = this.requestsTabIndex();
      }
    });
  }

  toggleUserState(user: AdminUser): void {
    if (!this.canChangeUserState || this.stateChangeUserId) {
      return;
    }
    const activating = !user.is_active;
    const action = activating ? 'activar' : 'desactivar';
    const name = this.fullName(user);
    if (!window.confirm(`¿Desea ${action} la cuenta de ${name}?`)) {
      return;
    }

    this.stateChangeUserId = user.id;
    this.actionError = '';
    const request: Observable<AdminUser> = activating
      ? this.adminUsers.activate(user.id)
      : this.adminUsers.deactivate(user.id);
    request.subscribe({
      next: updated => {
        this.users = this.users.map(item => item.id === updated.id ? updated : item);
        if (this.selectedUser?.id === updated.id) {
          this.selectedUser = updated;
        }
        this.stateChangeUserId = null;
      },
      error: () => {
        this.actionError = `No se pudo ${action} la cuenta. Revise sus permisos e inténtelo nuevamente.`;
        this.stateChangeUserId = null;
      },
    });
  }

  fullName(user: AdminUser): string {
    return `${user.first_name} ${user.last_name}`.trim() || user.email;
  }

  organizationalUnitNames(user: AdminUser): string[] {
    return [...new Set(user.alcances.map(scope => scope.unidad.nombre))];
  }

  stateLabel(state: AdminUserState): string {
    const labels: Record<AdminUserState, string> = {
      PENDIENTE: 'Pendiente',
      ACTIVO: 'Activo',
      INACTIVO: 'Inactivo',
    };
    return labels[state];
  }

  systemLabel(system: AdminSystem): string {
    return system === 'sis_pe' ? 'SIS-PE' : 'SIS-POA';
  }

  trackUser(_index: number, user: AdminUser): string {
    return user.id;
  }

  refreshUsersAfterApproval(requestId: string): void {
    if (this.selectedUser?.id === requestId) {
      this.closeDetail();
    }
    if (this.canViewUsers) {
      this.loadUsers();
    }
  }

  private updateUser(updated: AdminUser): void {
    this.users = this.users.map(user => user.id === updated.id ? updated : user);
    if (this.selectedUser?.id === updated.id) {
      this.selectedUser = updated;
    }
  }

  private requestsTabIndex(): number {
    return [this.canViewUsers, this.canViewRoles, this.canViewCapabilities]
      .filter(Boolean).length;
  }

  private loadOrganizationalUnits(): void {
    this.auth.listPublicOrganizationalUnits().subscribe({
      next: units => {
        this.organizationalUnits = units;
        this.catalogError = '';
      },
      error: () => {
        this.organizationalUnits = [];
        this.catalogError = 'No se pudo cargar el catálogo de unidades.';
      },
    });
  }
}
