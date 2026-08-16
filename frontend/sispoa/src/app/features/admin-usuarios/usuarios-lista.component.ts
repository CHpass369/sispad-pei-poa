import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AdminUsuariosService, AdminUsuario } from './admin-usuarios.service';

@Component({
  standalone: false,
  selector: 'app-usuarios-lista',
  template: `
    <div class="page-header">
      <h2>Gestión de Usuarios</h2>
      <p class="text-secondary">Administración de usuarios y roles del sistema</p>
    </div>
    
    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
          placeholder="Buscar por email o nombre...">
        </div>
        <button class="btn btn-primary" (click)="nuevo()">+ Nuevo Usuario</button>
      </div>
    
      @if (!cargando) {
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Nombre</th>
                <th>Roles</th>
                <th>Estado</th>
                <th>Registro</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (u of usuarios; track u) {
                <tr>
                  <td>{{ u.email }}</td>
                  <td>{{ u.first_name }} {{ u.last_name }}</td>
                  <td>
                    @for (r of u.rol_nombre; track r) {
                      <span class="badge badge-info">{{ r }}</span>
                    }
                  </td>
                  <td>
                    <span class="badge" [class.badge-success]="u.is_active" [class.badge-danger]="!u.is_active">
                      {{ u.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td>{{ u.date_joined | date:'dd/MM/yyyy' }}</td>
                  <td>
                    <button class="btn btn-sm btn-outline" (click)="editar(u)">Editar</button>
                    <button class="btn btn-sm btn-danger" (click)="eliminar(u)">Eliminar</button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
          @if (usuarios.length === 0) {
            <div class="empty">No se encontraron usuarios</div>
          }
        </div>
      }
    
      @if (cargando) {
        <div class="loading">Cargando...</div>
      }
    
      @if (error) {
        <div class="alert alert-error">{{ error }}</div>
      }
    `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-right: 0.25rem; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark, #303F9F); }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .btn-danger { background: var(--mdc-red-800); color: white; }
    .btn-danger:hover { background: #B71C1C; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class UsuariosListaComponent implements OnInit {
  usuarios: AdminUsuario[] = [];
  busqueda = '';
  cargando = true;
  error = '';

  constructor(
    private adminService: AdminUsuariosService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    const params: any = {};
    if (this.busqueda) params.search = this.busqueda;
    this.adminService.listarUsuarios(params).subscribe({
      next: (data: any) => {
        this.usuarios = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar usuarios';
        this.cargando = false;
      },
    });
  }

  nuevo(): void {
    this.router.navigate(['admin-usuarios/nuevo']);
  }

  editar(u: AdminUsuario): void {
    this.router.navigate(['admin-usuarios', u.id]);
  }

  eliminar(u: AdminUsuario): void {
    if (!confirm(`¿Eliminar usuario ${u.email}?`)) return;
    this.adminService.eliminarUsuario(u.id!).subscribe({
      next: () => this.cargar(),
      error: () => { this.error = 'Error al eliminar usuario'; },
    });
  }
}
