import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MatricesPadService } from './matrices-pad.service';

@Component({
  selector: 'app-matriz-b-visualizador',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <div>
          <h2>Matriz B — PAD (34 columnas)</h2>
          <p class="text-secondary">
            Cadena nacional → acuerdos internacionales → sectorial → territorial →
            resultados/productos PAD con indicadores y programación financiera.
            Mismas filas que la Matriz A (1 por resultado + 1 por producto).
            Lectura en vivo desde el backend.
          </p>
        </div>
        <div class="header-actions">
          <span class="badge" [class.badge-success]="materializada"
                [class.badge-warning]="!materializada">
            {{ materializada ? 'Materializada' : 'Borrador' }}
          </span>
          <span class="badge badge-info" *ngIf="!cargando && filas.length">
            {{ filas.length }} fila(s)
          </span>
          <a routerLink="mapa" class="btn btn-sm btn-primary">🗺 Mapa de conexiones</a>
          <a routerLink="/matrices-pad" class="btn btn-sm btn-outline">← Volver</a>
        </div>
      </div>

      <div class="alert alert-danger" *ngIf="mensajeError">{{ mensajeError }}</div>

      <div class="card table-card">
        <div class="table-scroll">
          <table class="matriz-table">
            <thead>
              <tr>
                <th>Eje PGDESA</th>
                <th>Impacto</th>
                <th>Componente</th>
                <th>Efecto</th>
                <th>ODS</th>
                <th>NDC</th>
                <th>NDT</th>
                <th>30/30</th>
                <th>Cod. Sector</th>
                <th>Sector</th>
                <th>Cod. RS</th>
                <th>Resultado Sectorial</th>
                <th>CGEO</th>
                <th>ETA</th>
                <th>Lineamiento</th>
                <th>Cod. Resultado</th>
                <th>Resultado</th>
                <th>Cod. Producto</th>
                <th>Producto</th>
                <th>Indicador</th>
                <th>Fórmula</th>
                <th>Unidad</th>
                <th>LB</th>
                <th>Meta 2030</th>
                <th *ngFor="let y of quinquenio" class="pf-col">Prog. Física {{ y }}</th>
                <th>Presupuesto Referencial</th>
                <th *ngFor="let y of quinquenio" class="pf-col">Ppto. {{ y }}</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let f of filas"
                  [class.fila-producto]="f.tipo_fila === 'producto'">
                <td><span class="codigo">{{ f.cod_eje_pgdesa || '—' }}</span></td>
                <td class="cell-desc">{{ f.objetivo_impacto || '—' }}</td>
                <td><span class="codigo">{{ f.cod_componente_pdesa || '—' }}</span></td>
                <td class="cell-desc">{{ f.objetivo_efecto || '—' }}</td>
                <td>{{ f.ods || '—' }}</td>
                <td>{{ f.ndc || '—' }}</td>
                <td>{{ f.ndt || '—' }}</td>
                <td>{{ f.compromiso_3030 || '—' }}</td>
                <td><span class="codigo">{{ f.cod_sector || '—' }}</span></td>
                <td class="cell-desc">{{ f.sector || '—' }}</td>
                <td><span class="codigo">{{ f.cod_resultado_pds || '—' }}</span></td>
                <td class="cell-desc">{{ f.resultado_pds || '—' }}</td>
                <td><span class="codigo">{{ f.cod_geografico || '—' }}</span></td>
                <td class="cell-desc">{{ f.eta || '—' }}</td>
                <td><span class="codigo">{{ f.cod_lineamiento_pad || '—' }}</span></td>
                <td><span class="codigo">{{ f.codigo_resultado_pad || '—' }}</span></td>
                <td class="cell-desc">{{ f.resultado_pad || '—' }}</td>
                <td><span class="codigo">{{ f.codigo_producto_pad || '—' }}</span></td>
                <td class="cell-desc">{{ f.producto_pad || '—' }}</td>
                <td class="cell-desc">{{ f.indicador || '—' }}</td>
                <td class="cell-desc">{{ f.formula || '—' }}</td>
                <td>{{ f.unidad_medida || '—' }}</td>
                <td class="num">{{ f.linea_base !== '' ? f.linea_base : '—' }}</td>
                <td class="num">{{ f.meta_2030 !== '' ? f.meta_2030 : '—' }}</td>
                <td class="num" *ngFor="let y of quinquenio">{{ f['pf_' + y] !== '' ? f['pf_' + y] : '—' }}</td>
                <td class="num">{{ f.presupuesto_total !== '' ? f.presupuesto_total : '—' }}</td>
                <td class="num" *ngFor="let y of quinquenio">{{ f['presupuesto_' + y] !== '' ? f['presupuesto_' + y] : '—' }}</td>
              </tr>
              <tr *ngIf="cargando">
                <td colspan="34" class="empty-cell">Cargando Matriz B...</td>
              </tr>
              <tr *ngIf="!cargando && filas.length === 0">
                <td colspan="34" class="empty-cell">
                  Sin datos para mostrar. Complete el wizard o materialice la matriz.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .matriz-page { padding-bottom: 2rem; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }
    .header-actions { display: flex; align-items: center; gap: 0.5rem; white-space: nowrap; }

    .table-card { padding: 0; overflow: hidden; }
    .table-scroll { overflow-x: auto; max-height: 70vh; overflow-y: auto; }
    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; }
    .matriz-table th { position: sticky; top: 0; z-index: 2; text-align: left; padding: 0.5rem 0.625rem; background: var(--bg); color: var(--text-secondary); font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.03em; border-bottom: 1px solid var(--border); white-space: nowrap; }
    .matriz-table td { padding: 0.5rem 0.625rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .fila-producto { background: #FAFBFC; }
    .cell-desc { min-width: 150px; max-width: 240px; }
    .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; }
    .pf-col { min-width: 90px; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 1.5rem; }

    .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-success { background: #E8F5E9; color: #1B5E3B; }
    .badge-warning { background: #FFF8E1; color: #8D6E2F; }
    .badge-info { background: #E3F2FD; color: #1565C0; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-danger { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .page-header { flex-direction: column; }
    }
  `],
})
export class MatrizBVisualizadorComponent implements OnInit {
  filas: any[] = [];
  quinquenio = [2026, 2027, 2028, 2029, 2030];
  cargando = false;
  materializada = false;
  mensajeError = '';

  constructor(
    private service: MatricesPadService,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.mensajeError = 'Falta el identificador del borrador.';
      return;
    }
    this.service.obtener(id).subscribe({
      next: (b) => {
        this.materializada = b.estado === 'COMPLETO';
        this.cdr.detectChanges();
      },
      error: () => { /* se ignora: la matriz puede no requerir el detalle */ },
    });
    this.service.matrizB(id).subscribe({
      next: (filas) => {
        this.filas = filas || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando Matriz B', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la Matriz B.';
        this.cdr.detectChanges();
      },
    });
  }
}
