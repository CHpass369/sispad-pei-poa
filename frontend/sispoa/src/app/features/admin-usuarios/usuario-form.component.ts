import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AdminUsuariosService, Usuario, Rol } from './admin-usuarios.service';

@Component({
  standalone: false,
  selector: 'app-usuario-form',
  template: `
    <div class="page-header">
      <h2>{{ esEdicion ? 'Editar Usuario' : 'Nuevo Usuario' }}</h2>
      <p class="text-secondary">{{ esEdicion ? 'Actualizar datos y roles del usuario' : 'Crear un nuevo usuario en el sistema' }}</p>
    </div>

    <div class="form-card" *ngIf="!cargando">
      <form (ngSubmit)="guardar()">
        <div class="form-grid">
          <div class="field">
            <label>Email *</label>
            <input type="email" [(ngModel)]="usuario.email" name="email" class="form-control" required>
          </div>
          <div class="field">
            <label>Nombre</label>
            <input [(ngModel)]="usuario.first_name" name="first_name" class="form-control">
          </div>
          <div class="field">
            <label>Apellido</label>
            <input [(ngModel)]="usuario.last_name" name="last_name" class="form-control">
          </div>
          <div class="field">
            <label>Estado</label>
            <select [(ngModel)]="usuario.is_active" name="is_active" class="form-control">
              <option [ngValue]="true">Activo</option>
              <option [ngValue]="false">Inactivo</option>
            </select>
          </div>
        </div>

        <div class="field field-full">
          <label>Roles</label>
          <div class="roles-grid">
            <label *ngFor="let rol of rolesDisponibles" class="checkbox-label">
              <input type="checkbox" [checked]="isSelected(rol.id)"
                     (change)="toggleRol(rol.id)"/>
              <span>{{ rol.name }}</span>
            </label>
          </div>
          <div *ngIf="rolesDisponibles.length === 0" class="text-secondary">
            No hay roles disponibles
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="cancelar()">Cancelar</button>
          <button type="submit" class="btn btn-primary" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </div>

    <div class="loading" *ngIf="cargando">Cargando datos...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .field { display: flex; flex-direction: column; margin-bottom: 1rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { font-size: 0.8125rem; font-weight: 600; margin-bottom: 0.375rem; color: var(--text-primary); }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .form-control:focus { outline: none; border-color: var(--primary); }
    .roles-grid { display: flex; flex-wrap: wrap; gap: 0.75rem; }
    .checkbox-label { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 0.875rem; }
    .checkbox-label:hover { border-color: var(--primary); }
    .form-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class UsuarioFormComponent implements OnInit {
  usuario: Partial<Usuario> = { email: '', first_name: '', last_name: '', is_active: true, roles: [] };
  rolesDisponibles: Rol[] = [];
  esEdicion = false;
  cargando = true;
  guardando = false;
  error = '';
  private usuarioId = 0;

  constructor(
    private adminService: AdminUsuariosService,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.esEdicion = true;
      this.usuarioId = +id;
    }
    this.cargarRoles();
  }

  cargarRoles(): void {
    this.adminService.listarRoles().subscribe({
      next: (roles: any) => {
        this.rolesDisponibles = roles.results || roles;
        if (this.esEdicion) {
          this.cargarUsuario();
        } else {
          this.cargando = false;
        }
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  cargarUsuario(): void {
    this.adminService.obtenerUsuario(this.usuarioId).subscribe({
      next: (u) => {
        this.usuario = { ...u };
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar usuario';
        this.cargando = false;
      },
    });
  }

  isSelected(rolId: number): boolean {
    return (this.usuario.roles || []).includes(rolId);
  }

  toggleRol(rolId: number): void {
    if (!this.usuario.roles) this.usuario.roles = [];
    const idx = this.usuario.roles.indexOf(rolId);
    if (idx >= 0) {
      this.usuario.roles.splice(idx, 1);
    } else {
      this.usuario.roles.push(rolId);
    }
  }

  guardar(): void {
    if (!this.usuario.email) {
      this.error = 'El email es obligatorio';
      return;
    }
    this.guardando = true;
    this.error = '';
    const req$ = this.esEdicion
      ? this.adminService.actualizarUsuario(this.usuarioId, this.usuario)
      : this.adminService.crearUsuario(this.usuario);
    req$.subscribe({
      next: () => {
        this.router.navigate(['admin-usuarios']);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al guardar usuario';
        this.guardando = false;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['admin-usuarios']);
  }
}
