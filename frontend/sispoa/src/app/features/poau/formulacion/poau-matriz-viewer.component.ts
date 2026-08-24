import { Component, Input } from '@angular/core';
import {
  FilaMatrizPoau,
  Hallazgo,
  MESES,
  ProgramacionMensual,
} from './poau-matriz.model';

/**
 * Visualizador presentacional de la Matriz de Formulación POAU.
 *
 * Solo programación física: la desagregación operativa con su meta repartida
 * mes a mes. La programación financiera no forma parte de esta matriz.
 */
@Component({
  selector: 'app-poau-matriz-viewer',
  standalone: false,
  template: `
    <div class="matriz-vista card">
      <div class="matriz-tabs">
        <button class="btn" [class.btn-primary]="vista === 'matriz'" (click)="vista = 'matriz'">
          MATRIZ POAU — PROGRAMACIÓN FÍSICA
        </button>
      </div>

      <div *ngIf="vista === 'matriz'" class="matriz-scroll">
        <h3>Formulación POAU gestión {{ gestion }} — operaciones, actividades y tareas</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="7" class="g-articulacion">ARTICULACIÓN POA – PEI</th>
              <th colspan="5" class="g-operativa">DESAGREGACIÓN OPERATIVA</th>
              <th colspan="5" class="g-indicador">INDICADOR</th>
              <th colspan="3" class="g-temporal">TEMPORALIZACIÓN</th>
              <th colspan="12" class="g-fisica">PROGRAMACIÓN FÍSICA MENSUAL</th>
              <th rowspan="2" class="g-total">TOTAL ANUAL</th>
            </tr>
            <tr class="columna">
              <th class="g-articulacion">CÓD. PRODUCTO PEI</th>
              <th class="g-articulacion">ACCIÓN INSTITUCIONAL ESPECÍFICA</th>
              <th class="g-articulacion">INDICADOR DE PROCESO</th>
              <th class="g-articulacion">CÓD. ACCIÓN DE CORTO PLAZO</th>
              <th class="g-articulacion">ACCIÓN DE CORTO PLAZO {{ gestion }}</th>
              <th class="g-articulacion">CATEGORÍA PROGRAMÁTICA</th>
              <th class="g-articulacion">DENOMINACIÓN CATEGORÍA</th>
              <th class="g-operativa">CÓDIGO</th>
              <th class="g-operativa">OPERACIÓN</th>
              <th class="g-operativa">ACTIVIDAD</th>
              <th class="g-operativa">TAREA ESPECÍFICA</th>
              <th class="g-operativa">UNIDAD EJECUTORA</th>
              <th class="g-indicador">PRODUCTO INTERMEDIO</th>
              <th class="g-indicador">INDICADOR</th>
              <th class="g-indicador">FÓRMULA</th>
              <th class="g-indicador">UNIDAD DE MEDIDA</th>
              <th class="g-indicador">META</th>
              <th class="g-temporal">INICIO</th>
              <th class="g-temporal">FINAL</th>
              <th class="g-temporal">% PONDERACIÓN</th>
              <th class="g-fisica" *ngFor="let mes of meses">{{ mes | uppercase }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filas"
                [class.fila-operacion]="fila.nivel === 'operacion'"
                [class.fila-tarea]="fila.nivel === 'tarea'">
              <td class="codigo">{{ fila.codigoProductoPei || '-' }}</td>
              <td class="celda-larga">{{ fila.accionInstitucionalEspecifica || '-' }}</td>
              <td class="celda-larga">{{ fila.indicadorProceso || '-' }}</td>
              <td class="codigo">{{ fila.codigoAccionCortoPlazo || '-' }}</td>
              <td class="celda-larga">{{ fila.accionCortoPlazo || '-' }}</td>
              <td class="codigo cat">{{ fila.categoriaProgramatica || '-' }}</td>
              <td class="celda-larga">{{ fila.denominacionCategoria || '-' }}</td>
              <td class="codigo destacado">{{ fila.codigo || '-' }}</td>
              <td class="celda-larga">{{ fila.operacion || '-' }}</td>
              <td class="celda-larga">{{ fila.actividad || '-' }}</td>
              <td class="celda-larga">{{ fila.tarea || '-' }}</td>
              <td class="celda-larga">{{ fila.unidadEjecutora || '-' }}</td>
              <td class="celda-larga">{{ fila.productoIntermedio || '-' }}</td>
              <td class="celda-larga">{{ fila.indicador || '-' }}</td>
              <td class="celda-larga">{{ fila.formula || '-' }}</td>
              <td>{{ fila.unidadMedida || '-' }}</td>
              <td class="num">{{ fila.meta ?? '-' }}</td>
              <td class="fecha">{{ fila.fechaInicio || '-' }}</td>
              <td class="fecha">{{ fila.fechaFin || '-' }}</td>
              <td class="num">{{ fila.ponderacion !== null ? fila.ponderacion + '%' : '-' }}</td>
              <td class="num" *ngFor="let mes of meses">{{ valor(fila.programacion, mes) }}</td>
              <td class="num total">{{ fila.totalAnual || '-' }}</td>
            </tr>
            <tr *ngIf="!filas.length">
              <td colspan="33" class="vacio">
                Avance por el asistente para ver la matriz tomar forma fila por fila.
              </td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          Las filas verdes son operaciones; debajo cuelgan sus actividades y, más abajo,
          las tareas específicas. Esta matriz lleva <strong>solo programación física</strong>:
          los requerimientos y su presupuesto se determinan por separado.
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
    .mz tr.columna th { font-size: 0.5625rem; min-width: 74px; }
    .mz td { padding: 0.25rem 0.4rem; border: 1px solid var(--border); vertical-align: top; }

    .g-articulacion { background: #1F3864; }
    .g-operativa { background: #2E7D32; }
    .g-indicador { background: #1565C0; }
    .g-temporal { background: #6B1A16; }
    .g-fisica { background: #8A5A1A; }
    .g-total { background: #7B4B12; }

    .fila-operacion td { background: #E8F5E9; font-weight: 600; }
    .fila-tarea td { background: #FAFAFA; font-style: italic; color: var(--text-secondary); }
    .mz tbody tr:hover td { background: #F0F7F3; }
    .codigo { font-family: 'Courier New', monospace; font-weight: 700; white-space: nowrap; }
    .cat { text-align: center; letter-spacing: 0.06em; }
    .destacado { color: var(--primary-dark, #1B5E20); }
    .celda-larga { max-width: 190px; }
    .num { text-align: right; white-space: nowrap; }
    .fecha { white-space: nowrap; font-family: 'Courier New', monospace; }
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
export class PoauMatrizViewerComponent {
  @Input() filas: FilaMatrizPoau[] = [];
  @Input() hallazgos: Hallazgo[] = [];
  /** La gestión llega del contenedor, que la toma del candado (ADR-007).
   *  El default era un año literal y sobrevivía si el padre no la pasaba. */
  @Input() gestion = 0;

  vista: 'matriz' = 'matriz';
  meses = MESES;

  valor(programacion: ProgramacionMensual, mes: string): string {
    const dato = programacion?.[mes];
    return dato === null || dato === undefined || (dato as unknown) === '' ? '-' : String(dato);
  }
}
