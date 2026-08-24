import { Component, Input } from '@angular/core';
import {
  FilaMatrizRecursos,
  Hallazgo,
  MESES,
  ProgramacionMensual,
} from './poau-recursos.model';

/**
 * Visualizador presentacional de la Matriz de Programación Presupuestaria POAU.
 */
@Component({
  selector: 'app-poau-recursos-viewer',
  standalone: false,
  template: `
    <div class="matriz-vista card">
      <div class="matriz-tabs">
        <button class="btn" [class.btn-primary]="vista === 'matriz'" (click)="vista = 'matriz'">
          MATRIZ PRESUPUESTARIA POAU
        </button>
      </div>

      <div *ngIf="vista === 'matriz'" class="matriz-scroll">
        <h3>Programación presupuestaria POAU gestión {{ gestion }}</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="4" class="g-cabecera">CATEGORÍA Y RESPONSABLE</th>
              <th colspan="6" class="g-clasificador">CLASIFICACIÓN PRESUPUESTARIA</th>
              <th rowspan="2" class="g-monto">PRESUPUESTO PROGRAMADO {{ gestion }}</th>
              <th colspan="12" class="g-mensual">PRESUPUESTO PROGRAMADO MENSUAL</th>
              <th rowspan="2" class="g-monto">TOTAL ANUAL</th>
              <th rowspan="2" class="g-verificacion">MEDIO DE VERIFICACIÓN</th>
            </tr>
            <tr class="columna">
              <th class="g-cabecera">CAT. PROGRAMÁTICA</th>
              <th class="g-cabecera">DENOMINACIÓN</th>
              <th class="g-cabecera">CARGO DEL REACP</th>
              <th class="g-cabecera">FECHA REQUERIDA</th>
              <th class="g-clasificador">DA</th>
              <th class="g-clasificador">UE</th>
              <th class="g-clasificador">FTE</th>
              <th class="g-clasificador">ORG</th>
              <th class="g-clasificador">COD. PARTIDA</th>
              <th class="g-clasificador">BIEN O SERVICIO DEMANDADO</th>
              <th class="g-mensual" *ngFor="let mes of meses">{{ mes | slice:0:3 | uppercase }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filas">
              <td class="codigo cat">{{ fila.categoriaProgramatica || '-' }}</td>
              <td class="celda-larga">{{ fila.denominacionCategoria || '-' }}</td>
              <td class="celda-larga">{{ fila.cargoReacp || '-' }}</td>
              <td>{{ fila.fechaRequerimiento || '-' }}</td>
              <td class="codigo">{{ fila.da || '-' }}</td>
              <td class="codigo">{{ fila.ue || '-' }}</td>
              <td class="codigo">{{ fila.fuenteFinanciamiento || '-' }}</td>
              <td class="codigo">{{ fila.organismoFinanciador || '-' }}</td>
              <td class="codigo">{{ fila.codPartida || '-' }}</td>
              <td class="celda-larga">{{ fila.bienServicio || '-' }}</td>
              <td class="num total">{{ moneda(fila.presupuestoProgramado) }}</td>
              <td class="num" *ngFor="let mes of meses">{{ moneda(valor(fila.programacion, mes)) }}</td>
              <td class="num total">{{ moneda(fila.totalAnual) }}</td>
              <td class="celda-larga">{{ fila.medioVerificacion || '-' }}</td>
            </tr>
            <tr *ngIf="!filas.length">
              <td colspan="25" class="vacio">
                Avance por el asistente para ver la matriz tomar forma fila por fila.
              </td>
            </tr>
            <tr class="fila-total" *ngIf="filas.length">
              <td colspan="10">TOTAL REQUERIMIENTOS GESTIÓN {{ gestion }}</td>
              <td class="num total">{{ moneda(total) }}</td>
              <td class="num" *ngFor="let mes of meses">{{ moneda(totalMes(mes)) }}</td>
              <td class="num total">{{ moneda(total) }}</td>
              <td></td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          Cada fila es un bien o servicio demandado con su partida de gasto, su fuente y el
          mes en que se requiere el pago. Esta matriz es la contraparte financiera de la
          programación física del POAU.
        </p>
      </div>

    </div>
  `,
  styles: [`
    .matriz-vista { margin-top: 1.5rem; padding: 1.25rem; border: 2px solid var(--primary); }
    .matriz-vista h3 { font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--primary); }
    .matriz-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .matriz-tabs .btn { font-size: 0.75rem; padding: 0.375rem 0.75rem; }
    .pill { background: var(--warn); color: #fff; border-radius: 10px; padding: 0 0.4rem; margin-left: 0.35rem; font-size: 0.625rem; }

    .matriz-scroll { overflow-x: auto; }
    .mz { border-collapse: collapse; font-size: 0.625rem; width: 100%; }
    .mz th { color: #fff; padding: 0.3rem 0.4rem; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.25); font-weight: 700; vertical-align: middle; }
    .mz tr.columna th { font-size: 0.5625rem; min-width: 66px; }
    .mz td { padding: 0.25rem 0.4rem; border: 1px solid var(--border); vertical-align: top; }

    .g-cabecera { background: #1F3864; }
    .g-clasificador { background: #6B1A16; }
    .g-monto { background: #7B4B12; }
    .g-mensual { background: #8A5A1A; }
    .g-verificacion { background: #2E7D32; }

    .mz tbody tr:hover td { background: #F0F7F3; }
    .fila-total td { background: #E8F5E9; font-weight: 700; }
    .fila-total td:first-child { text-align: right; }
    .codigo { font-family: 'Courier New', monospace; font-weight: 700; white-space: nowrap; }
    .cat { text-align: center; letter-spacing: 0.06em; }
    .celda-larga { max-width: 200px; }
    .num { text-align: right; white-space: nowrap; }
    .total { font-weight: 700; }
    .vacio { text-align: center; color: var(--text-secondary); padding: 1.5rem; font-size: 0.8125rem; }
    .leyenda { margin-top: 0.6rem; font-size: 0.6875rem; color: var(--text-secondary); }

    .control { font-size: 0.8125rem; }
    .sin-hallazgos { background: #E8F5E9; color: var(--success); padding: 0.75rem; border-radius: 6px; }
    .lista-hallazgos { list-style: none; padding: 0; margin: 0; }
    .lista-hallazgos li { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.45rem 0.6rem; border-radius: 6px; margin-bottom: 0.35rem; }
    .lista-hallazgos li.error { background: #FFEBEE; color: var(--warn); }
    .lista-hallazgos li.aviso { background: #FFF8E1; color: #8A6100; }
    .etiqueta { font-weight: 700; white-space: nowrap; font-size: 0.6875rem; text-transform: uppercase; }
    .texto { font-size: 0.75rem; }
  `],
})
export class PoauRecursosViewerComponent {
  @Input() filas: FilaMatrizRecursos[] = [];
  @Input() hallazgos: Hallazgo[] = [];
  @Input() gestion = 2027;
  @Input() total = 0;

  vista: 'matriz' = 'matriz';
  meses = MESES;

  valor(programacion: ProgramacionMensual, mes: string): number {
    return Number(programacion?.[mes]) || 0;
  }

  totalMes(mes: string): number {
    return this.filas.reduce((t, f) => t + (Number(f.programacion?.[mes]) || 0), 0);
  }

  moneda(valor: number | null): string {
    return valor ? Number(valor).toLocaleString('es-BO') : '-';
  }
}
