import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-poau-lista',
  standalone: false,
  template: `
    <div class="poau-page">
      <div class="page-header">
        <h2>POAU — Plan Operativo Anual por Unidad</h2>
        <p class="text-secondary">Elaboración de POAUs por unidad organizacional</p>
        <div class="toolbar">
          <a routerLink="/poau/nuevo" class="btn btn-primary">+ Nuevo POAU</a>
        </div>
      </div>

      <div class="card">
        <table>
          <thead>
            <tr><th>Código</th><th>Nombre</th><th>Unidad</th><th>Gestión</th><th>Estado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of poaus">
              <td><strong>{{ p.codigo }}</strong></td>
              <td>{{ p.nombre | slice:0:60 }}</td>
              <td>{{ p.unidad_nombre || '—' }}</td>
              <td>{{ p.gestion }}</td>
              <td><span class="badge" [class.badge-success]="p.estado==='aprobado'" 
                        [class.badge-warning]="p.estado==='enviado'"
                        [class.badge-info]="p.estado==='borrador'">{{ p.estado }}</span></td>
              <td>
                <a [routerLink]="['/poau', p.id]" class="btn btn-outline btn-sm">Editar</a>
                <button *ngIf="p.estado==='borrador'" class="btn btn-primary btn-sm" 
                        (click)="enviar(p)">Enviar</button>
              </td>
            </tr>
            <tr *ngIf="poaus.length===0"><td colspan="6" class="empty-cell">No hay POAUs. Cree uno nuevo.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .poau-page { padding-bottom:2rem; }
    .page-header { margin-bottom:1rem; }
    .page-header h2 { font-size:1.25rem; }
    .toolbar { margin-top:0.75rem; }
    table { width:100%; }
    th, td { padding:0.5rem 0.75rem; text-align:left; border-bottom:1px solid var(--border); font-size:0.8125rem; }
    th { font-size:0.75rem; color:var(--text-secondary); text-transform:uppercase; }
    .empty-cell { text-align:center; color:var(--text-secondary); padding:2rem; }
    .btn-sm { font-size:0.75rem; padding:0.25rem 0.5rem; }
  `]
})
export class PoauListaComponent implements OnInit {
  poaus: any[] = [];
  constructor(private api: ApiService) {}
  ngOnInit(): void { this.cargar(); }
  cargar(): void {
    this.api.get<any>('/poau/poaus/').subscribe({
      next: (r: any) => this.poaus = r.results || r,
    });
  }
  enviar(p: any): void {
    this.api.post('/poau/poaus/' + p.id + '/enviar/', {}).subscribe({
      next: () => { p.estado = 'enviado'; },
    });
  }
}
