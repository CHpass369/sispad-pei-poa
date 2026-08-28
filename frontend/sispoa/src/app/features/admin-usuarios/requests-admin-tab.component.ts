import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { PageEvent } from '@angular/material/paginator';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import {
  AdminRegistrationRequest,
  AdminUsuariosService,
} from './admin-usuarios.service';
import {
  RequestApprovalDialogComponent,
  RequestApprovalDialogData,
  RequestApprovalDialogResult,
} from './request-approval-dialog.component';

@Component({
  standalone: false,
  selector: 'app-requests-admin-tab',
  templateUrl: './requests-admin-tab.component.html',
  styleUrl: './requests-admin-tab.component.scss',
})
export class RequestsAdminTabComponent implements OnInit {
  @Output() readonly requestApproved = new EventEmitter<string>();

  readonly displayedColumns = [
    'usuario', 'cargo', 'unidad', 'encargatura', 'fecha', 'estado', 'acciones',
  ];
  readonly pageSize = 25;

  requests: AdminRegistrationRequest[] = [];
  totalRequests = 0;
  pageIndex = 0;
  loading = false;
  error = '';

  constructor(
    private readonly adminUsers: AdminUsuariosService,
    private readonly capabilities: CapabilitiesService,
    private readonly dialog: MatDialog,
  ) {}

  ngOnInit(): void {
    this.loadRequests();
  }

  get canApprove(): boolean {
    return this.capabilities.tiene('accounts.solicitud.approve');
  }

  loadRequests(): void {
    this.loading = true;
    this.error = '';
    this.adminUsers.listRequests(this.pageIndex + 1).subscribe({
      next: page => {
        this.requests = page.results.filter(
          request => !request.estado || request.estado === 'PENDIENTE',
        );
        this.totalRequests = page.count;
        this.loading = false;
      },
      error: () => {
        this.requests = [];
        this.totalRequests = 0;
        this.error = 'No se pudo cargar la bandeja de solicitudes.';
        this.loading = false;
      },
    });
  }

  refresh(): void {
    this.pageIndex = 0;
    this.loadRequests();
  }

  changePage(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.loadRequests();
  }

  openApproval(request: AdminRegistrationRequest): void {
    if (!this.canApprove) {
      return;
    }
    const data: RequestApprovalDialogData = { request };
    this.dialog.open<
      RequestApprovalDialogComponent,
      RequestApprovalDialogData,
      RequestApprovalDialogResult
    >(RequestApprovalDialogComponent, {
      data,
      width: '44rem',
      maxWidth: '96vw',
      maxHeight: '94vh',
      autoFocus: 'first-header',
      restoreFocus: true,
      ariaLabelledBy: 'request-approval-title',
      ariaDescribedBy: 'request-approval-description',
      closePredicate: (_result, _config, component) => {
        const instance = component as RequestApprovalDialogComponent | null;
        return !instance?.saving;
      },
    }).afterClosed().subscribe(result => {
      if (!result?.approved) {
        return;
      }
      this.requests = this.requests.filter(item => item.id !== result.requestId);
      this.totalRequests = Math.max(0, this.totalRequests - 1);
      if (!this.requests.length && this.pageIndex > 0) {
        this.pageIndex -= 1;
      }
      this.requestApproved.emit(result.requestId);
      this.loadRequests();
    });
  }

  fullName(request: AdminRegistrationRequest): string {
    return `${request.first_name} ${request.last_name}`.trim() || request.email;
  }

  requestedUnit(request: AdminRegistrationRequest): string {
    return request.unidad_solicitada?.nombre ?? 'Sin unidad solicitada';
  }

  declaredLeadership(request: AdminRegistrationRequest): string {
    return request.solicita_encargado_unidad
      ? 'Declara ser encargado'
      : 'No declara encargatura';
  }

  trackRequest(_index: number, request: AdminRegistrationRequest): string {
    return request.id;
  }
}
