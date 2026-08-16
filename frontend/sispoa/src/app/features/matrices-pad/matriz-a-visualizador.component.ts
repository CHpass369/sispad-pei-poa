import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MatricesPadService } from './matrices-pad.service';

@Component({
  selector: 'app-matriz-a-visualizador',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <div>
          <h2>Matriz A — PAD (27 columnas)</h2>
          <p class="text-secondary">
            Estructura real de las matrices: cada resultado territorial PAD genera 1 fila
            + 1 fila por cada producto (todos conviven en la misma matriz). Lectura en vivo:
            desde los modelos si el borrador está materializado, o desde las secciones
            persistidas del wizard en caso contrario.
          </p>
        </div>
        <div class="header-actions">
          <span class="badge" [class.badge-success]="materializada"
            [class.badge-warning]="!materializada">
            {{ materializada ? 'Materializada' : 'Borrador' }}
          </span>
          @if (!cargando && filas.length) {
            <span class="badge badge-info">
              {{ filas.length }} fila(s)
            </span>
          }
          <a routerLink="/matrices-pad" class="btn btn-sm btn-outline">← Volver</a>
        </div>
      </div>
    
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card table-card">
        <div class="table-scroll">
          <table class="matriz-table">
            <thead>
              <tr>
                <th class="sticky-col">Sector</th>
                <th>CGEO</th>
                <th>Política</th>
                <th>Lineamiento</th>
                <th>Código Resultado</th>
                <th>Resultado</th>
                <th>Código Producto</th>
                <th>Producto</th>
                <th>Territorialización</th>
                <th>Responsable</th>
                <th>Indicador</th>
                <th>Fórmula</th>
                <th>Unidad</th>
                <th>Línea Base</th>
                <th>Meta 2030</th>
                @for (y of quinquenio; track y) {
                  <th class="pf-col">Prog. Física {{ y }}</th>
                }
                <th>¿Financ.?</th>
                <th>Presupuesto Total</th>
                @for (y of quinquenio; track y) {
                  <th class="pf-col">Ppto. {{ y }}</th>
                }
              </tr>
            </thead>
            <tbody>
              @for (f of filas; track f) {
                <tr
                  [class.fila-producto]="f.tipo_fila === 'producto'">
                  <td class="sticky-col">{{ f.sector || '—' }}</td>
                  <td><span class="codigo">{{ f.cod_geografico || '—' }}</span></td>
                  <td class="cell-desc">{{ f.politica || '—' }}</td>
                  <td><span class="codigo">{{ f.cod_lineamiento_pad || '—' }}</span></td>
                  <td><span class="codigo">{{ f.codigo_resultado_pad || '—' }}</span></td>
                  <td class="cell-desc">{{ f.resultado_pad || '—' }}</td>
                  <td><span class="codigo">{{ f.codigo_producto_pad || '—' }}</span></td>
                  <td class="cell-desc">{{ f.producto_pad || '—' }}</td>
                  <td class="cell-desc">{{ f.territorializacion || '—' }}</td>
                  <td class="cell-desc">{{ f.responsable_pad || '—' }}</td>
                  <td class="cell-desc">{{ f.indicador || '—' }}</td>
                  <td class="cell-desc">{{ f.formula || '—' }}</td>
                  <td>{{ f.unidad_medida || '—' }}</td>
                  <td class="num">{{ f.linea_base !== '' ? f.linea_base : '—' }}</td>
                  <td class="num">{{ f.meta_2030 !== '' ? f.meta_2030 : '—' }}</td>
                  @for (y of quinquenio; track y) {
                    <td class="num">{{ f['pf_' + y] !== '' ? f['pf_' + y] : '—' }}</td>
                  }
                  <td>
                    <span class="badge" [class.badge-success]="f.cuenta_con_financiamiento"
                      [class.badge-muted]="!f.cuenta_con_financiamiento">
                      {{ f.cuenta_con_financiamiento ? 'SÍ' : 'NO' }}
                    </span>
                  </td>
                  <td class="num">{{ f.presupuesto_total !== '' ? f.presupuesto_total : '—' }}</td>
                  @for (y of quinquenio; track y) {
                    <td class="num">{{ f['presupuesto_' + y] !== '' ? f['presupuesto_' + y] : '—' }}</td>
                  }
                </tr>
              }
              @if (cargando) {
                <tr>
                  <td colspan="27" class="empty-cell">Cargando Matriz A...</td>
                </tr>
              }
              @if (!cargando && filas.length === 0) {
                <tr>
                  <td colspan="27" class="empty-cell">
                    Sin datos para mostrar. Complete el wizard o materialice la matriz.
                  </td>
                </tr>
              }
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
    .sticky-col { position: sticky; left: 0; background: #fff; z-index: 1; min-width: 130px; }
    .matriz-table th.sticky-col { z-index: 3; }
    .fila-producto { background: #FAFBFC; }
    .cell-desc { min-width: 180px; max-width: 280px; }
    .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; }
    .pf-col { min-width: 90px; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 1.5rem; }

    .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #8D6E2F; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-muted { background: #F1F1F1; color: #757575; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .page-header { flex-direction: column; }
    }
  `],
})
export class MatrizAVisualizadorComponent implements OnInit {
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
    this.service.matrizA(id).subscribe({
      next: (filas) => {
        this.filas = filas || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando Matriz A', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la Matriz A.';
        this.cdr.detectChanges();
      },
    });
  }
}
