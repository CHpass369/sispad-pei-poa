import { Component, Input } from '@angular/core';
import { GESTIONES_PEI } from './pei-catalogos';
import { FilaMatrizPei, Hallazgo, ProgramacionAnual } from './pei-matriz.model';

/**
 * Visualizador presentacional de la Matriz de Planificación PEI.
 *
 * Reproduce el formato oficial de 46 columnas agrupadas en ocho secciones
 * (Guía Metodológica PEI §3.7) y una vista del puente de articulación con el
 * resultado territorial del PAD.
 */
@Component({
  selector: 'app-pei-matriz-viewer',
  standalone: false,
  template: `
    <div class="matriz-vista card">
      <div class="matriz-tabs">
        <button class="btn" [class.btn-primary]="vista === 'matriz'" (click)="vista = 'matriz'">
          MATRIZ PEI 2026-2030
        </button>
        <button class="btn" [class.btn-primary]="vista === 'articulacion'" (click)="vista = 'articulacion'">
          ARTICULACIÓN PAD → PEI
        </button>
      </div>

      <!-- MATRIZ OFICIAL (46 columnas) -->
      <div *ngIf="vista === 'matriz'" class="matriz-scroll">
        <h3>Matriz de planificación PEI — Entidades Territoriales Autónomas</h3>
        <table class="mz">
          <thead>
            <tr class="grupo">
              <th colspan="4" class="g-nacional">PLANIFICACIÓN NACIONAL</th>
              <th colspan="4" class="g-acuerdos">ACUERDOS INTERNACIONALES</th>
              <th colspan="2" class="g-sector">IDENTIFICACIÓN DEL SECTOR</th>
              <th colspan="2" class="g-sectorial">ARTICULACIÓN SECTORIAL</th>
              <th colspan="1" class="g-territorial">ARTICULACIÓN TERRITORIAL</th>
              <th colspan="9" class="g-institucional">PLANIFICACIÓN INSTITUCIONAL</th>
              <th colspan="6" class="g-indicador">INDICADOR</th>
              <th colspan="5" class="g-fisica">PROGRAMACIÓN FÍSICA</th>
              <th rowspan="2" class="g-total">PRESUPUESTO QUINQUENAL TOTAL</th>
              <th colspan="6" class="g-financiera">PROGRAMACIÓN FINANCIERA GASTO DE INVERSIÓN</th>
              <th colspan="6" class="g-financiera">PROGRAMACIÓN FINANCIERA GASTO CORRIENTE</th>
            </tr>
            <tr class="columna">
              <th class="g-nacional">COD EJE PGDESA (Impacto)</th>
              <th class="g-nacional">OBJETIVO DE IMPACTO</th>
              <th class="g-nacional">COD COMPONENTE PDESA (Efecto)</th>
              <th class="g-nacional">OBJETIVO DE EFECTO</th>
              <th class="g-acuerdos">COD ODS</th>
              <th class="g-acuerdos">COD NDC</th>
              <th class="g-acuerdos">COD NDT</th>
              <th class="g-acuerdos">COD META 30x30</th>
              <th class="g-sector">COD SECTOR</th>
              <th class="g-sector">SECTOR</th>
              <th class="g-sectorial">COD RESULTADO SECTORIAL PES</th>
              <th class="g-sectorial">RESULTADO SECTORIAL</th>
              <th class="g-territorial">COD RESULTADO TERRITORIAL</th>
              <th class="g-institucional">COD ENTIDAD</th>
              <th class="g-institucional">ENTIDAD</th>
              <th class="g-institucional">COD OEI</th>
              <th class="g-institucional">COD RESULTADO PEI</th>
              <th class="g-institucional">RESULTADO INSTITUCIONAL</th>
              <th class="g-institucional">COD PROGRAMA PRESUPUESTARIO</th>
              <th class="g-institucional">DESCRIPCIÓN PROGRAMA PRESUPUESTARIO</th>
              <th class="g-institucional">COD PRODUCTO</th>
              <th class="g-institucional">NOMBRE PRODUCTO</th>
              <th class="g-indicador">INDICADOR</th>
              <th class="g-indicador">TIPO DE INDICADOR</th>
              <th class="g-indicador">UNIDAD DE MEDIDA</th>
              <th class="g-indicador">FÓRMULA</th>
              <th class="g-indicador">LÍNEA BASE</th>
              <th class="g-indicador">META 2030</th>
              <th class="g-fisica" *ngFor="let anio of gestiones">{{ anio }}</th>
              <th class="g-financiera">PRESUPUESTO QUINQUENAL GASTO DE INVERSIÓN</th>
              <th class="g-financiera" *ngFor="let anio of gestiones">{{ anio }}</th>
              <th class="g-financiera">PRESUPUESTO QUINQUENAL GASTO CORRIENTE</th>
              <th class="g-financiera" *ngFor="let anio of gestiones">{{ anio }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filas" [class.fila-resultado]="fila.nivel === 'resultado'">
              <td>{{ fila.codEjePgdesa || '-' }}</td>
              <td class="celda-larga">{{ fila.objetivoImpacto || '-' }}</td>
              <td>{{ fila.codComponentePdesa || '-' }}</td>
              <td class="celda-larga">{{ fila.objetivoEfecto || '-' }}</td>
              <td>{{ fila.codOds || '-' }}</td>
              <td>{{ fila.codNdc || '-' }}</td>
              <td>{{ fila.codNdt || '-' }}</td>
              <td>{{ fila.codMeta3030 || '-' }}</td>
              <td>{{ fila.codSector || '-' }}</td>
              <td>{{ fila.sector || '-' }}</td>
              <td>{{ fila.codResultadoSectorial || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoSectorial || '-' }}</td>
              <td class="codigo destacado">{{ fila.codResultadoTerritorial || '-' }}</td>
              <td>{{ fila.codEntidad || '-' }}</td>
              <td>{{ fila.entidad || '-' }}</td>
              <td>{{ fila.codOei || '-' }}</td>
              <td class="codigo">{{ fila.codResultadoPei || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoInstitucional || '-' }}</td>
              <td>{{ fila.codProgramaPresup || '-' }}</td>
              <td class="celda-larga">{{ fila.programaPresup || '-' }}</td>
              <td class="codigo">{{ fila.codProducto || '-' }}</td>
              <td class="celda-larga">{{ fila.nombreProducto || '-' }}</td>
              <td class="celda-larga">{{ fila.indicador || '-' }}</td>
              <td>{{ fila.tipoIndicador || '-' }}</td>
              <td>{{ fila.unidadMedida || '-' }}</td>
              <td>{{ fila.formula || '-' }}</td>
              <td class="num">{{ fila.lineaBase ?? '-' }}</td>
              <td class="num">{{ fila.meta2030 ?? '-' }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ valor(fila.fisica, anio) }}</td>
              <td class="num total">{{ moneda(fila.presupuestoTotal) }}</td>
              <td class="num total">{{ moneda(fila.inversionTotal) }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ moneda(valorNumero(fila.inversion, anio)) }}</td>
              <td class="num total">{{ moneda(fila.corrienteTotal) }}</td>
              <td class="num" *ngFor="let anio of gestiones">{{ moneda(valorNumero(fila.corriente, anio)) }}</td>
            </tr>
            <tr *ngIf="!filas.length">
              <td colspan="46" class="vacio">
                Avance por el asistente para ver la matriz tomar forma fila por fila.
              </td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          La primera fila corresponde al resultado institucional (programa y producto en
          <strong>NO APLICA</strong>); las siguientes, a cada producto institucional que lo compone.
        </p>
      </div>

      <!-- PUENTE DE ARTICULACIÓN PAD → PEI -->
      <div *ngIf="vista === 'articulacion'" class="matriz-scroll">
        <h3>Puente de articulación: resultado territorial del PAD → resultado institucional del PEI</h3>
        <table class="mz">
          <thead>
            <tr class="columna">
              <th class="g-territorial">COD RESULTADO TERRITORIAL (PAD)</th>
              <th class="g-institucional">COD RESULTADO PEI</th>
              <th class="g-institucional">RESULTADO INSTITUCIONAL</th>
              <th class="g-institucional">COD PRODUCTO PEI</th>
              <th class="g-institucional">NOMBRE PRODUCTO</th>
              <th class="g-indicador">INDICADOR</th>
              <th class="g-indicador">TIPO</th>
              <th class="g-total">PRESUPUESTO QUINQUENAL</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let fila of filas" [class.fila-resultado]="fila.nivel === 'resultado'">
              <td class="codigo destacado">{{ fila.codResultadoTerritorial || 'SIN VINCULAR' }}</td>
              <td class="codigo">{{ fila.codResultadoPei || '-' }}</td>
              <td class="celda-larga">{{ fila.resultadoInstitucional || '-' }}</td>
              <td class="codigo">{{ fila.codProducto || '-' }}</td>
              <td class="celda-larga">{{ fila.nombreProducto || '-' }}</td>
              <td class="celda-larga">{{ fila.indicador || '-' }}</td>
              <td>{{ fila.tipoIndicador || '-' }}</td>
              <td class="num total">{{ moneda(fila.presupuestoTotal) }}</td>
            </tr>
            <tr *ngIf="!filas.length">
              <td colspan="8" class="vacio">Todavía no hay filas que articular.</td>
            </tr>
          </tbody>
        </table>
        <p class="leyenda">
          La guía exige registrar en el PEI el <strong>código de resultado territorial del PAD</strong>
          al que contribuyen el resultado institucional y sus productos. Esa columna es la bisagra
          con la que después se cruzan ambas matrices.
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

    /* Paleta por sección del formato oficial */
    .g-nacional { background: #A6291F; }
    .g-acuerdos { background: #4B7BB5; }
    .g-sector { background: #6B1A16; }
    .g-sectorial { background: #A8701C; }
    .g-territorial { background: #2E7D32; }
    .g-institucional { background: #1F3864; }
    .g-indicador { background: #1565C0; }
    .g-fisica { background: #1565C0; }
    .g-total { background: #7B4B12; }
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
export class PeiMatrizViewerComponent {
  @Input() filas: FilaMatrizPei[] = [];
  @Input() hallazgos: Hallazgo[] = [];

  vista: 'matriz' | 'articulacion' = 'matriz';
  gestiones = GESTIONES_PEI;

  valor(programacion: ProgramacionAnual, anio: string): string {
    const dato = programacion?.[anio];
    return dato === null || dato === undefined || dato === ('' as unknown) ? '-' : String(dato);
  }

  valorNumero(programacion: ProgramacionAnual, anio: string): number {
    return Number(programacion?.[anio]) || 0;
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '-';
  }
}
