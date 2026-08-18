import { Component, Input } from '@angular/core';
import { FilaMatrizPoa, Hallazgo } from './poa-matriz.model';

/**
 * Visualizador presentacional de la Matriz de Formulación POA.
 *
 * Presenta las 11 columnas que resultan de fusionar el Cuadro 1
 * "Articulación POA – PEI" con el Cuadro 2 "Programación de Acciones a Corto
 * Plazo" del RE-SPO, con el mismo lenguaje visual de las matrices PEI y PAD.
 */
@Component({
  selector: 'app-poa-matriz-viewer',
  standalone: false,
  template: `
    <div class="matriz-vista card">
      <div class="matriz-tabs">
        <button class="btn" [class.btn-primary]="vista === 'matriz'" (click)="vista = 'matriz'">
          MATRIZ POA — ARTICULACIÓN Y PROGRAMACIÓN
        </button>
      </div>

      <div *ngIf="vista === 'matriz'" class="matriz-scroll">
        <h3>Formulación POA gestión {{ gestion }} — Cuadros 1 y 2 fusionados</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="4" class="g-pei">ARTICULACIÓN POA – PEI (fuente: PEI)</th>
              <th colspan="3" class="g-acp">ACCIÓN DE CORTO PLAZO</th>
              <th colspan="4" class="g-categoria">CATEGORÍA PROGRAMÁTICA</th>
              <th colspan="1" class="g-acp">PRESUPUESTO</th>
              <th colspan="3" class="g-programacion">PROGRAMACIÓN DE LA ACCIÓN</th>
            </tr>
            <tr class="columna">
              <th class="g-pei">CÓDIGO PEI</th>
              <th class="g-pei">ACCIÓN INSTITUCIONAL ESPECÍFICA</th>
              <th class="g-pei">INDICADOR DE PROCESO</th>
              <th class="g-pei">ÁREA O UNIDAD RESPONSABLE</th>
              <th class="g-acp">CÓDIGO ACCIÓN DE CORTO PLAZO</th>
              <th class="g-acp">ACCIÓN DE CORTO PLAZO {{ gestion }}</th>
              <th class="g-acp">RESULTADO ESPERADO {{ gestion }}</th>
              <th class="g-categoria">PROGRAMA</th>
              <th class="g-categoria">PROYECTO</th>
              <th class="g-categoria">ACTIVIDAD</th>
              <th class="g-categoria">CATEGORÍA PROGRAMÁTICA</th>
              <th class="g-acp">PRESUPUESTO PROGRAMADO {{ gestion }}</th>
              <th class="g-programacion">CARGO DEL REACP</th>
              <th class="g-programacion">FECHA PREVISTA DE INICIO</th>
              <th class="g-programacion">FECHA PREVISTA DE FINALIZACIÓN</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filas">
              <td class="codigo destacado">{{ fila.codigoPei || '-' }}</td>
              <td class="celda-larga">{{ fila.accionInstitucionalEspecifica || '-' }}</td>
              <td class="celda-larga">{{ fila.indicadorProceso || '-' }}</td>
              <td class="celda-larga">{{ fila.areaResponsable || '-' }}</td>
              <td class="codigo">{{ fila.codigoAccion || '-' }}</td>
              <td class="celda-larga">{{ fila.accionCortoPlazo || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoEsperado || '-' }}</td>
              <td class="codigo seg">{{ fila.programa || '-' }}</td>
              <td class="codigo seg">{{ fila.proyecto || '-' }}</td>
              <td class="codigo seg">{{ fila.actividad || '-' }}</td>
              <td class="codigo cat">{{ fila.categoriaProgramatica || '-' }}</td>
              <td class="num total">{{ moneda(fila.presupuestoProgramado) }}</td>
              <td class="celda-larga">{{ fila.cargoReacp || '-' }}</td>
              <td class="fecha">{{ fila.fechaInicio || '-' }}</td>
              <td class="fecha">{{ fila.fechaFin || '-' }}</td>
            </tr>
            <tr *ngIf="!filas.length">
              <td colspan="15" class="vacio">
                Avance por el asistente para ver la matriz tomar forma fila por fila.
              </td>
            </tr>
            <tr class="fila-total" *ngIf="filas.length">
              <td colspan="11">TOTAL PRESUPUESTO PROGRAMADO GESTIÓN {{ gestion }}</td>
              <td class="num total">{{ moneda(total) }}</td>
              <td colspan="3"></td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          Desde el código PEI hasta el presupuesto programado, los campos tienen fuente PEI:
          se heredan de la acción institucional específica seleccionada. El cargo del REACP y
          las fechas previstas los define la entidad al programar la gestión, y los establece
          el REACP en coordinación con sus unidades ejecutoras.
          La categoría programática no se escribe: es la concatenación de programa,
          proyecto y actividad del clasificador presupuestario.
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
    .mz { border-collapse: collapse; font-size: 0.6875rem; width: 100%; }
    .mz th { color: #fff; padding: 0.35rem 0.45rem; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.25); font-weight: 700; vertical-align: middle; }
    .mz tr.columna th { font-size: 0.5625rem; min-width: 92px; }
    .mz td { padding: 0.3rem 0.45rem; border: 1px solid var(--border); vertical-align: top; }

    /* Un color por bloque de la fusión */
    .g-pei { background: #1F3864; }
    .g-acp { background: #2E7D32; }
    .g-categoria { background: #6B1A16; }
    .g-programacion { background: #8A5A1A; }

    .mz tbody tr:hover td { background: #F0F7F3; }
    .fila-total td { background: #E8F5E9; font-weight: 700; text-align: right; }
    .codigo { font-family: 'Courier New', monospace; font-weight: 700; white-space: nowrap; }
    .destacado { color: var(--primary-dark, #1B5E20); }
    .celda-larga { max-width: 220px; }
    .num { text-align: right; white-space: nowrap; }
    .fecha { white-space: nowrap; font-family: 'Courier New', monospace; }
    .seg { text-align: center; }
    .cat { text-align: center; letter-spacing: 0.06em; background: #F3F7F4; font-weight: 800; }
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
export class PoaMatrizViewerComponent {
  @Input() filas: FilaMatrizPoa[] = [];
  @Input() hallazgos: Hallazgo[] = [];
  @Input() gestion = 2026;
  @Input() total = 0;

  vista: 'matriz' = 'matriz';

  moneda(valor: number | null): string {
    return valor ? Number(valor).toLocaleString('es-BO') : '-';
  }
}
