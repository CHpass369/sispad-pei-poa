import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';


/**
 * Página genérica para módulos del plan maestro aún en desarrollo.
 * Muestra el nombre del módulo y su estado en el roadmap de PIP-GAMS.
 */
@Component({
  standalone: true,
  imports: [RouterModule],
  selector: 'app-modulo-pendiente',
  template: `
    <div class="pendiente">
      <div class="page-header">
        <h2>{{ modulo }}</h2>
        <p class="text-secondary">{{ sistema }} — módulo del plan maestro</p>
      </div>
      <div class="card">
        <div class="icono">🛠️</div>
        <h3>Módulo en desarrollo</h3>
        <p>
          Este módulo está definido en el plan maestro de PIP-GAMS
          ({{ referencia }}) y su implementación V2 está pendiente.
        </p>
        <a [routerLink]="volver" class="btn btn-primary">Volver al {{ sistema }}</a>
      </div>
    </div>
  `,
  styles: [`
    .pendiente { padding: 1rem; max-width: 720px; }
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 2rem; text-align: center;
    }
    .icono { font-size: 2.5rem; }
    .card h3 { margin: 0.75rem 0 0.5rem; }
    .card p { color: var(--text-secondary); font-size: 0.875rem; line-height: 1.5; margin-bottom: 1.25rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
  `],
})
export class ModuloPendienteComponent implements OnInit {
  modulo = 'Módulo';
  sistema = 'SIS';
  referencia = 'plan maestro §18.1';
  volver = '/sistemas';

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    this.modulo = this.route.snapshot.data['modulo'] ?? 'Módulo';
    this.sistema = this.route.snapshot.data['sistema'] ?? 'SIS';
    const ruta = this.route.snapshot.data['volver'] ?? '/sistemas';
    this.volver = ruta;
  }
}
