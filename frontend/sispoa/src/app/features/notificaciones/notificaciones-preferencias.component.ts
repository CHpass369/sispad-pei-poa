import { Component, OnInit } from '@angular/core';
import { NotificacionesService, PreferenciaNotificacion } from './notificaciones.service';

@Component({
  standalone: false,
  selector: 'app-notificaciones-preferencias',
  template: `
    <div class="page-header">
      <h2>Preferencias de Notificaciones</h2>
      <p class="text-secondary">Configura cómo y cuándo recibir notificaciones</p>
    </div>
    
    @if (!cargando) {
      <div class="preferencias-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Evento</th>
              <th class="col-center">Email</th>
              <th class="col-center">En la App</th>
              <th class="col-center">Push</th>
            </tr>
          </thead>
          <tbody>
            @for (pref of preferencias; track pref) {
              <tr>
                <td class="evento-cell">
                  <strong>{{ formatearEvento(pref.evento) }}</strong>
                </td>
                <td class="col-center">
                  <label class="toggle-switch">
                    <input type="checkbox" [checked]="pref.email_habilitado"
                      (change)="toggle(pref, 'email_habilitado')">
                      <span class="toggle-slider"></span>
                    </label>
                  </td>
                  <td class="col-center">
                    <label class="toggle-switch">
                      <input type="checkbox" [checked]="pref.in_app_habilitado"
                        (change)="toggle(pref, 'in_app_habilitado')">
                        <span class="toggle-slider"></span>
                      </label>
                    </td>
                    <td class="col-center">
                      <label class="toggle-switch">
                        <input type="checkbox" [checked]="pref.push_habilitado"
                          (change)="toggle(pref, 'push_habilitado')">
                          <span class="toggle-slider"></span>
                        </label>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
              @if (preferencias.length === 0) {
                <div class="empty">No hay eventos de notificación disponibles</div>
              }
            </div>
          }
    
          @if (cargando) {
            <div class="loading">Cargando preferencias...</div>
          }
          @if (exito) {
            <div class="alert alert-success">{{ exito }}</div>
          }
          @if (error) {
            <div class="alert alert-error">{{ error }}</div>
          }
    `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .preferencias-container { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; }

    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .col-center { text-align: center; }
    .evento-cell { min-width: 200px; }
    .toggle-switch { position: relative; display: inline-block; width: 44px; height: 24px; cursor: pointer; }
    .toggle-switch input { opacity: 0; width: 0; height: 0; }
    .toggle-slider { position: absolute; inset: 0; background: #ccc; border-radius: 24px; transition: 0.3s; }
    .toggle-slider::before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s; }
    .toggle-switch input:checked + .toggle-slider { background: var(--primary); }
    .toggle-switch input:checked + .toggle-slider::before { transform: translateX(20px); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class NotificacionesPreferenciasComponent implements OnInit {
  preferencias: PreferenciaNotificacion[] = [];
  cargando = true;
  error = '';
  exito = '';

  constructor(private notificacionesService: NotificacionesService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.notificacionesService.obtenerPreferencias().subscribe({
      next: (data: any) => {
        this.preferencias = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar preferencias';
        this.cargando = false;
      },
    });
  }

  toggle(pref: PreferenciaNotificacion, campo: string): void {
    if (!pref.id) return;
    this.exito = '';
    this.error = '';
    const data: Partial<PreferenciaNotificacion> = {};
    (data as any)[campo] = !(pref as any)[campo];
    this.notificacionesService.actualizarPreferencia(pref.id, data).subscribe({
      next: (updated) => {
        Object.assign(pref, updated);
        this.exito = 'Preferencia actualizada';
        setTimeout(() => this.exito = '', 3000);
      },
      error: () => {
        this.error = 'Error al actualizar preferencia';
      },
    });
  }

  formatearEvento(evento?: string): string {
    if (!evento) return 'Desconocido';
    return evento.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}
