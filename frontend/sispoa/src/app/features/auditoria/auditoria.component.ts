import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-auditoria',
  template: `
    <div class="page-header">
      <h2>Auditoría del Sistema</h2>
      <p class="text-secondary">Trazabilidad completa de eventos</p>
    </div>
    <div class="filtros">
      <div class="field">
        <label>Acción</label>
        <select [(ngModel)]="filtroAccion" (change)="cargar()" class="form-control">
          <option value="">Todas</option>
          <option *ngFor="let a of acciones" [value]="a">{{ a }}</option>
        </select>
      </div>
      <div class="field">
        <label>Entidad</label>
        <input [(ngModel)]="filtroEntidad" (keyup.enter)="cargar()" class="form-control" placeholder="Buscar entidad...">
      </div>
    </div>
    <div class="timeline">
      <div *ngFor="let e of eventos" class="evento">
        <div class="evento-dot" [class.login]="e.accion==='login'" [class.aprobar]="e.accion==='aprobar'"
             [class.crear]="e.accion==='crear'" [class.modificar]="e.accion==='modificar'"></div>
        <div class="evento-content card">
          <div class="evento-header">
            <strong>{{ e.usuario_email || e.usuario || 'Sistema' }}</strong>
            <span class="badge badge-info">{{ e.accion }}</span>
            <span class="evento-fecha">{{ e.creado_en | date:'dd/MM/yyyy HH:mm' }}</span>
          </div>
          <div class="evento-body">
            <span class="entidad">{{ e.entidad }} #{{ e.entidad_id }}</span>
            <p *ngIf="e.resumen">{{ e.resumen }}</p>
          </div>
        </div>
      </div>
      <div *ngIf="eventos.length === 0" class="empty">
        No hay eventos de auditoría
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .filtros { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .filtros .field { flex: 1; max-width: 300px; }
    .filtros label { display: block; font-size: 0.75rem; margin-bottom: 0.25rem; }
    .timeline { position: relative; }
    .timeline::before {
      content: ''; position: absolute; left: 15px; top: 0; bottom: 0;
      width: 2px; background: var(--border);
    }
    .evento { display: flex; gap: 1rem; margin-bottom: 1rem; position: relative; }
    .evento-dot {
      width: 32px; height: 32px; border-radius: 50%; background: var(--border);
      flex-shrink: 0; z-index: 1; border: 3px solid white;
    }
    .evento-dot.login { background: var(--info); }
    .evento-dot.aprobar { background: var(--success); }
    .evento-dot.crear { background: var(--primary); }
    .evento-dot.modificar { background: var(--accent); }
    .evento-content { flex: 1; padding: 0.75rem 1rem; }
    .evento-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .evento-fecha { margin-left: auto; font-size: 0.75rem; color: var(--text-secondary); }
    .entidad { font-size: 0.8125rem; color: var(--text-secondary); }
    .evento-body p { margin-top: 0.375rem; font-size: 0.875rem; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
  `]
})
export class AuditoriaComponent implements OnInit {
  eventos: any[] = [];
  filtroAccion = '';
  filtroEntidad = '';
  acciones = ['login','logout','crear','modificar','anular','enviar','devolver','aprobar','consolidar'];

  constructor(private api: ApiService) {}

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    const params: any = {};
    if (this.filtroAccion) params.accion = this.filtroAccion;
    if (this.filtroEntidad) params.search = this.filtroEntidad;
    this.api.get<any[]>('/eventos/', params).subscribe({
      next: (r: any) => this.eventos = r.results || r,
    });
  }
}
