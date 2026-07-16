import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-proyecto-lista',
  template: `
    <div class="page-header">
      <h2>Proyectos de Inversión</h2>
      <p class="text-secondary">Registro de proyectos con código SISIN</p>
    </div>
    <div class="filtros">
      <label>Prioridad:</label>
      <select [(ngModel)]="filtroPrioridad" (change)="cargar()" class="form-control filtro-select">
        <option value="">Todas</option>
        <option value="1">Continuidad</option>
        <option value="2">Financiamiento asegurado</option>
        <option value="3">Nuevo estratégico</option>
        <option value="4">Otro nuevo</option>
      </select>
      <label>Etapa:</label>
      <select [(ngModel)]="filtroEtapa" (change)="cargar()" class="form-control filtro-select">
        <option value="">Todas</option>
        <option value="preinversion">Preinversión</option>
        <option value="inversion">Inversión</option>
        <option value="cierre">Cierre</option>
      </select>
    </div>
    <div class="card" style="margin-top:1rem;">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>SISIN</th>
            <th>Prioridad</th>
            <th>Etapa</th>
            <th>Costo Total</th>
            <th>Ejecutado</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let p of proyectos">
            <td><strong>{{ p.codigo_interno }}</strong></td>
            <td>{{ p.nombre }}</td>
            <td><code>{{ p.codigo_sisin || '—' }}</code></td>
            <td>{{ prioridadLabel(p.prioridad) }}</td>
            <td>{{ etapaLabel(p.etapa) }}</td>
            <td>Bs {{ p.costo_total | number:'1.2-2' }}</td>
            <td>Bs {{ p.ejecucion_acumulada | number:'1.2-2' }}</td>
            <td><span class="badge" [class.badge-success]="p.activo">{{ p.activo ? 'Activo' : 'Inactivo' }}</span></td>
          </tr>
          <tr *ngIf="proyectos.length === 0">
            <td colspan="8" class="empty">No hay proyectos registrados</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .filtros { display: flex; gap: 0.75rem; align-items: center; }
    .filtro-select { width: auto; min-width: 160px; padding: 0.375rem 0.5rem; }
    table { width: 100%; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    code { font-size: 0.8125rem; background: var(--bg); padding: 0.125rem 0.375rem; border-radius: 3px; }
    .empty { text-align: center; color: var(--text-secondary); padding: 2rem; }
  `]
})
export class ProyectoListaComponent implements OnInit {
  proyectos: any[] = [];
  filtroPrioridad = '';
  filtroEtapa = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    const params: any = {};
    if (this.filtroPrioridad) params.prioridad = this.filtroPrioridad;
    if (this.filtroEtapa) params.etapa = this.filtroEtapa;
    this.api.get<any[]>('/proyectos-inversion/', params).subscribe({
      next: (r: any) => this.proyectos = r.results || r,
    });
  }

  prioridadLabel(v: number): string {
    return ['','Continuidad','Financ. asegurado','Nuevo estratégico','Otro nuevo'][v] || '—';
  }
  etapaLabel(v: string): string {
    return {preinversion:'Preinversión', inversion:'Inversión', cierre:'Cierre'}[v] || v;
  }
}
