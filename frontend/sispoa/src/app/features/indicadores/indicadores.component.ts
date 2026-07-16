import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-indicadores',
  template: `
    <div class="page-header">
      <h2>Matriz de Indicadores</h2>
      <p class="text-secondary">{{ gestion }}</p>
    </div>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Indicador</th>
            <th>Fórmula</th>
            <th>Línea Base</th>
            <th>Meta Anual</th>
            <th>Unidad</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let ind of indicadores">
            <td><strong>{{ ind.codigo }}</strong></td>
            <td>{{ ind.nombre }}</td>
            <td class="formula">{{ ind.formula || '—' }}</td>
            <td>{{ ind.linea_base || '—' }}</td>
            <td>{{ ind.meta_anual || '—' }}</td>
            <td>{{ ind.unidad_medida_denom || '—' }}</td>
            <td><span class="badge" [class.badge-success]="ind.activo">{{ ind.activo ? 'Activo' : 'Inactivo' }}</span></td>
          </tr>
          <tr *ngIf="indicadores.length === 0">
            <td colspan="7" class="empty">No hay indicadores registrados</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .formula { font-family: monospace; font-size: 0.8125rem; }
    table { width: 100%; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .empty { text-align: center; color: var(--text-secondary); padding: 2rem; }
  `]
})
export class IndicadoresComponent implements OnInit {
  gestion = 2026;
  indicadores: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<any[]>('/indicadores/').subscribe({
      next: (r: any) => this.indicadores = r.results || r,
    });
  }
}
