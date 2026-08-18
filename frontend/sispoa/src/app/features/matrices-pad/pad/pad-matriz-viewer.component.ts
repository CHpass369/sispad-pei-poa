import { Component, Input } from '@angular/core';
import { GESTIONES_PAD } from './pad-catalogos';
import {
  FilaMatrizA,
  FilaMatrizB,
  Hallazgo,
  ProgramacionAnual,
} from './pad-matriz.model';

/**
 * Visualizador presentacional de las Matrices de Planificación PAD.
 *
 * Reproduce el formato oficial de la Matriz "A" (27 columnas) y la Matriz "B"
 * (33 columnas en cuatro bloques de articulación), con el mismo lenguaje
 * visual del visualizador de la Matriz PEI.
 */
@Component({
  selector: 'app-pad-matriz-viewer',
  standalone: false,
  template: `
    <div class="matriz-vista card">
      <div class="matriz-tabs">
        <button class="btn" [class.btn-primary]="vista === 'a'" (click)="vista = 'a'">
          MATRIZ A
        </button>
        <button class="btn" [class.btn-primary]="vista === 'b'" (click)="vista = 'b'">
          MATRIZ B — ARTICULACIÓN SIPEB
        </button>
      </div>

      <!-- MATRIZ A (27 columnas) -->
      <div *ngIf="vista === 'a'" class="matriz-scroll">
        <h3>Matriz de planificación "A" — propuesta de desarrollo del territorio</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="7" class="g-territorial">PLANIFICACIÓN TERRITORIAL</th>
              <th colspan="4" class="g-producto">PRODUCTO TERRITORIAL</th>
              <th colspan="4" class="g-indicador">INDICADOR</th>
              <th colspan="5" class="g-fisica">PROGRAMACIÓN FÍSICA</th>
              <th colspan="7" class="g-financiera">PROGRAMACIÓN FINANCIERA</th>
            </tr>
            <tr class="columna">
              <th class="g-territorial">SECTOR</th>
              <th class="g-territorial">CÓD. GEOGRÁFICO</th>
              <th class="g-territorial">POLÍTICA</th>
              <th class="g-territorial">CÓD. LINEAMIENTO</th>
              <th class="g-territorial">LINEAMIENTO ESTRATÉGICO</th>
              <th class="g-territorial">CÓD. RESULTADO TERRITORIAL</th>
              <th class="g-territorial">RESULTADO TERRITORIAL PAD</th>
              <th class="g-producto">CÓD. PRODUCTO</th>
              <th class="g-producto">PRODUCTO (PROYECTO/PROGRAMA)</th>
              <th class="g-producto">TERRITORIALIZACIÓN</th>
              <th class="g-producto">RESPONSABLE</th>
              <th class="g-indicador">INDICADOR</th>
              <th class="g-indicador">FÓRMULA</th>
              <th class="g-indicador">LÍNEA BASE</th>
              <th class="g-indicador">META 2030</th>
              <th class="g-fisica" *ngFor="let anio of gestiones">{{ anio }}</th>
              <th class="g-financiera">CUENTA CON FINANCIAMIENTO</th>
              <th class="g-financiera">PRESUPUESTO TOTAL PAD (Bs.)</th>
              <th class="g-financiera" *ngFor="let anio of gestiones">{{ anio }} (Bs.)</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filasA" [class.fila-resultado]="fila.nivel === 'resultado'">
              <td>{{ fila.sector || '-' }}</td>
              <td>{{ fila.codGeografico || '-' }}</td>
              <td class="celda-larga">{{ fila.politica || '-' }}</td>
              <td>{{ fila.codLineamiento || '-' }}</td>
              <td class="celda-larga">{{ fila.lineamiento || '-' }}</td>
              <td class="codigo destacado">{{ fila.codResultadoTerritorial || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoTerritorial || '-' }}</td>
              <td class="codigo">{{ fila.codProducto || '-' }}</td>
              <td class="celda-larga">{{ fila.producto || '-' }}</td>
              <td class="celda-larga">{{ fila.territorializacion || '-' }}</td>
              <td class="celda-larga">{{ fila.responsable || '-' }}</td>
              <td class="celda-larga">{{ fila.indicador || '-' }}</td>
              <td class="celda-larga">{{ fila.formula || '-' }}</td>
              <td class="num">{{ fila.lineaBase ?? '-' }}</td>
              <td class="num">{{ fila.meta2030 ?? '-' }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ valor(fila.fisica, anio) }}</td>
              <td>{{ fila.cuentaConFinanciamiento }}</td>
              <td class="num total">{{ moneda(fila.presupuestoTotal) }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ moneda(numero(fila.presupuesto, anio)) }}</td>
            </tr>
            <tr *ngIf="!filasA.length">
              <td colspan="27" class="vacio">
                Avance por el asistente para ver la Matriz A tomar forma fila por fila.
              </td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          Cada resultado territorial abre una fila propia; debajo van las filas de sus
          productos (proyectos o programas) que lo hacen operativo.
        </p>
      </div>

      <!-- MATRIZ B (33 columnas) -->
      <div *ngIf="vista === 'b'" class="matriz-scroll">
        <h3>Matriz de planificación "B" — articulación con los instrumentos del SIPEB</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="4" class="g-nacional">PLANIFICACIÓN NACIONAL</th>
              <th colspan="4" class="g-acuerdos">ACUERDOS INTERNACIONALES</th>
              <th colspan="4" class="g-sector">PLANIFICACIÓN SECTORIAL</th>
              <th colspan="21" class="g-territorial">PLANIFICACIÓN TERRITORIAL</th>
            </tr>
            <tr class="columna">
              <th class="g-nacional">CÓD. EJE PGDESA (IMPACTO)</th>
              <th class="g-nacional">OBJETIVO DE IMPACTO</th>
              <th class="g-nacional">CÓD. COMPONENTE PDESA (EFECTO)</th>
              <th class="g-nacional">OBJETIVO DE EFECTO</th>
              <th class="g-acuerdos">CÓD. ODS</th>
              <th class="g-acuerdos">CÓD. META NDC</th>
              <th class="g-acuerdos">CÓD. PRINCIPIOS NDT</th>
              <th class="g-acuerdos">COMPROMISOS 30/30</th>
              <th class="g-sector">CÓD. SECTOR</th>
              <th class="g-sector">SECTOR</th>
              <th class="g-sector">CÓD. RESULTADO SECTORIAL</th>
              <th class="g-sector">RESULTADO SECTORIAL</th>
              <th class="g-territorial">CÓD. GEOGRÁFICO</th>
              <th class="g-territorial">DENOMINACIÓN DE LA ETA</th>
              <th class="g-territorial">CÓD. LINEAMIENTO</th>
              <th class="g-territorial">LINEAMIENTO ESTRATÉGICO</th>
              <th class="g-territorial">CÓD. RESULTADO TERRITORIAL</th>
              <th class="g-territorial">RESULTADO TERRITORIAL</th>
              <th class="g-indicador">INDICADOR</th>
              <th class="g-indicador">FÓRMULA</th>
              <th class="g-indicador">LÍNEA BASE</th>
              <th class="g-indicador">META 2030</th>
              <th class="g-fisica" *ngFor="let anio of gestiones">{{ anio }}</th>
              <th class="g-financiera">PRESUPUESTO REFERENCIAL PAD</th>
              <th class="g-financiera" *ngFor="let anio of gestiones">{{ anio }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filasB" class="fila-resultado">
              <td>{{ fila.codEjePgdesa || '-' }}</td>
              <td class="celda-larga">{{ fila.objetivoImpacto || '-' }}</td>
              <td>{{ fila.codComponentePdesa || '-' }}</td>
              <td class="celda-larga">{{ fila.objetivoEfecto || '-' }}</td>
              <td>{{ fila.codOds || '-' }}</td>
              <td>{{ fila.codNdc || '-' }}</td>
              <td>{{ fila.codNdt || '-' }}</td>
              <td>{{ fila.compromiso3030 || '-' }}</td>
              <td>{{ fila.codSector || '-' }}</td>
              <td>{{ fila.sector || '-' }}</td>
              <td>{{ fila.codResultadoSectorial || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoSectorial || '-' }}</td>
              <td>{{ fila.codGeografico || '-' }}</td>
              <td class="celda-larga">{{ fila.eta || '-' }}</td>
              <td>{{ fila.codLineamiento || '-' }}</td>
              <td class="celda-larga">{{ fila.lineamiento || '-' }}</td>
              <td class="codigo destacado">{{ fila.codResultadoTerritorial || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoTerritorial || '-' }}</td>
              <td class="celda-larga">{{ fila.indicador || '-' }}</td>
              <td class="celda-larga">{{ fila.formula || '-' }}</td>
              <td class="num">{{ fila.lineaBase ?? '-' }}</td>
              <td class="num">{{ fila.meta2030 ?? '-' }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ valor(fila.fisica, anio) }}</td>
              <td class="num total">{{ moneda(fila.presupuestoReferencial) }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ moneda(numero(fila.presupuesto, anio)) }}</td>
            </tr>
            <tr *ngIf="!filasB.length">
              <td colspan="33" class="vacio">
                La Matriz B se arma con los resultados de la Matriz A más la articulación nacional.
              </td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          La Matriz B trabaja a nivel de resultado: copia el contenido de la "A" y le antepone
          el impacto del PGDESA, el efecto del PDESA, los acuerdos internacionales y el
          resultado sectorial del PDS.
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
    .mz tr.grupo th { font-size: 0.625rem; letter-spacing: 0.02em; }
    .mz tr.columna th { font-size: 0.5625rem; min-width: 78px; }
    .mz td { padding: 0.25rem 0.4rem; border: 1px solid var(--border); vertical-align: top; }

    /* Paleta por bloque del formato oficial */
    .g-nacional { background: #A6291F; }
    .g-acuerdos { background: #4B7BB5; }
    .g-sector { background: #6B1A16; }
    .g-territorial { background: #2E7D32; }
    .g-producto { background: #1F3864; }
    .g-indicador { background: #1565C0; }
    .g-fisica { background: #1565C0; }
    .g-financiera { background: #8A5A1A; }

    .fila-resultado td { background: #E8F5E9; font-weight: 600; }
    .mz tbody tr:hover td { background: #F0F7F3; }
    .codigo { font-family: 'Courier New', monospace; font-weight: 700; white-space: nowrap; }
    .destacado { color: var(--primary-dark, #1B5E20); }
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
export class PadMatrizViewerComponent {
  @Input() filasA: FilaMatrizA[] = [];
  @Input() filasB: FilaMatrizB[] = [];
  @Input() hallazgos: Hallazgo[] = [];

  vista: 'a' | 'b' = 'a';
  gestiones = GESTIONES_PAD;

  valor(programacion: ProgramacionAnual, anio: string): string {
    const dato = programacion?.[anio];
    return dato === null || dato === undefined || (dato as unknown) === '' ? '-' : String(dato);
  }

  numero(programacion: ProgramacionAnual, anio: string): number {
    return Number(programacion?.[anio]) || 0;
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '-';
  }
}
