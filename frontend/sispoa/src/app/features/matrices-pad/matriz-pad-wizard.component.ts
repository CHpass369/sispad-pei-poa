import { Component, OnInit, OnDestroy, ChangeDetectorRef, ElementRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { MatricesPadService } from './matrices-pad.service';
import {
  IndicadorDraft,
  ProductoDraft,
  ResultadoDraft,
} from './tabla-jerarquica.component';

/**
 * Wizard de Matriz PAD (11 pasos, sin articulación PEI).
 *
 * Estructura REAL de las matrices: el borrador contiene VARIOS resultados
 * territoriales PAD, cada uno con VARIOS productos; todas las filas
 * conviven en la misma Matriz A y Matriz B (formato del Excel de la guía).
 *
 * Guardado INCREMENTAL por sección (PATCH seccion+valores). La sección
 * ``resultados`` se envía SIEMPRE como la LISTA COMPLETA: el wizard la
 * mantiene en memoria y la reemplaza al agregar/editar resultado o
 * producto. Pasos 6-10 escriben la misma sección ``resultados`` (cada paso
 * enriquece la colección); el paso 11 materializa en una transacción.
 */
@Component({
  selector: 'app-matriz-pad-wizard',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>{{ borradorId ? 'Editar' : 'Nueva' }} Matriz PAD</h2>
        <p class="text-secondary">
          Secuencia metodológica de la guía PAD: nacional → acuerdos → sectorial
          → territorial → lineamiento → resultados y productos → indicadores →
          programación → revisión. Un borrador puede contener VARIOS resultados,
          cada uno con VARIOS productos (todas las filas conviven en la misma
          Matriz A / Matriz B).
        </p>
      </div>

      <!-- Barra de progreso -->
      <div class="stepper">
        <div class="step" *ngFor="let s of pasos; let i = index"
             [class.active]="pasoActual === i + 1"
             [class.completed]="pasoActual > i + 1"
             (click)="irAPaso(i + 1)">
          <div class="step-circle">{{ pasoActual > i + 1 ? '✓' : i + 1 }}</div>
          <div class="step-label">{{ s }}</div>
        </div>
      </div>

      <!-- Mensajes -->
      <div class="alert alert-success" *ngIf="mensajeExito">{{ mensajeExito }}</div>
      <div class="alert alert-danger" *ngIf="mensajeError">{{ mensajeError }}</div>

      <div class="card form-card">
        <!-- ======= PASO 1: Planificación Nacional ======= -->
        <div *ngIf="pasoActual === 1">
          <h3 class="step-title">Paso 1: Planificación Nacional</h3>
          <p class="field-hint">Matriz B — bloques A-D: Eje PGDESA (impacto) → Componente PDESA (efecto).</p>
          <div class="form-grid">
            <div class="field">
              <label>Eje PGDESA</label>
              <select [(ngModel)]="form.eje" class="form-control" (change)="onEjeChange()">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let eje of catalogoEjes" [ngValue]="eje">
                  {{ eje.codigo }} - {{ eje.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Objetivo de Impacto</label>
              <textarea #taImpacto [(ngModel)]="form.objetivo_impacto" readonly class="form-control textarea-auto"
                rows="2" placeholder="Objetivo de impacto del PGDESA (autollenado al elegir el eje)"
                (input)="autoAjustarTextarea($event)" (change)="autoAjustarTextarea($event)"></textarea>
            </div>
            <div class="field">
              <label>Componente PDESA</label>
              <select [(ngModel)]="form.componente" class="form-control" (change)="onComponenteChange()">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let comp of componentesFiltrados" [ngValue]="comp">
                  {{ comp.codigo }} - {{ comp.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Objetivo de Efecto</label>
              <textarea #taEfecto [(ngModel)]="form.objetivo_efecto" readonly class="form-control textarea-auto"
                rows="2" placeholder="Efecto esperado del PDESA (autollenado al elegir el componente)"
                (input)="autoAjustarTextarea($event)" (change)="autoAjustarTextarea($event)"></textarea>
            </div>
          </div>
        </div>

        <!-- ======= PASO 2: Acuerdos Internacionales ======= -->
        <div *ngIf="pasoActual === 2">
          <h3 class="step-title">Paso 2: Acuerdos Internacionales</h3>
          <p class="field-hint">Matriz B — bloques E-H: ODS → NDC → NDT → Compromisos 30/30 (KMGBF).</p>
          <div class="form-grid">
            <div class="field">
              <label>ODS (Objetivos de Desarrollo Sostenible)</label>
              <select [(ngModel)]="form.ods" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option [ngValue]="'N/A'">No aplica</option>
                <option *ngFor="let ods of catalogoODS" [ngValue]="ods">
                  ODS {{ ods.codigo }} - {{ ods.denominacion || ods.nombre }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>NDC (Contribución Nacional Determinada)</label>
              <select [(ngModel)]="form.ndc" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option [ngValue]="'N/A'">No aplica</option>
                <option *ngFor="let ndc of catalogoNDC" [ngValue]="ndc">
                  {{ ndc.codigo }} - {{ ndc.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>NDT (Principios de Navegación para el Desarrollo)</label>
              <select [(ngModel)]="form.ndt" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option [ngValue]="'N/A'">No aplica</option>
                <option *ngFor="let ndt of catalogoNDT" [ngValue]="ndt">
                  {{ ndt.codigo }} - {{ ndt.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Compromisos 30/30 (KMGBF)</label>
              <select [(ngModel)]="form.kmgbf" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option [ngValue]="'N/A'">No aplica</option>
                <option *ngFor="let kmgbf of catalogo3030" [ngValue]="kmgbf">
                  {{ kmgbf.codigo }} - {{ kmgbf.denominacion }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- ======= PASO 3: Planificación Sectorial ======= -->
        <div *ngIf="pasoActual === 3">
          <h3 class="step-title">Paso 3: Planificación Sectorial</h3>
          <p class="field-hint">Matriz B — bloques I-L: sector del clasificador presupuestario → resultado sectorial del PDS.</p>
          <div class="form-grid">
            <div class="field">
              <label>Sector (economía plural)</label>
              <select [(ngModel)]="form.sector" class="form-control" (change)="onSectorChange()">
                <option [ngValue]="null">Seleccionar sector...</option>
                <option *ngFor="let sec of catalogoSectores" [ngValue]="sec">
                  {{ sec.codigo }} - {{ sec.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Resultado Sectorial (PDS)</label>
              <select [(ngModel)]="form.resultado_sectorial" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let rs of resultadosSectorialesFiltrados" [ngValue]="rs">
                  {{ rs.codigo }} - {{ rs.denominacion }}
                </option>
              </select>
            </div>
            <div class="field-full text-secondary" *ngIf="resultadosSectorialesFiltrados.length === 0">
              No hay resultados sectoriales para este sector; puede continuar sin seleccionar.
            </div>
          </div>
        </div>

        <!-- ======= PASO 4: Contexto Territorial ======= -->
        <div *ngIf="pasoActual === 4">
          <h3 class="step-title">Paso 4: Contexto Territorial</h3>
          <p class="field-hint">Matriz A — columnas B-C / Matriz B M-N: código geográfico (clasificador CGEO INE) + ETA + política.</p>
          <div class="form-grid">
            <div class="field">
              <label>Código Geográfico (CGEO)</label>
              <select [(ngModel)]="form.cgeo" class="form-control" (change)="onCgeoChange()">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let e of catalogoEntidadesTerritoriales" [ngValue]="e">
                  {{ e.codigo }} - {{ e.denominacion }} ({{ e.nivel }})
                </option>
              </select>
            </div>
            <div class="field">
              <label>ETA (Estructura Territorial de Apoyo)</label>
              <input [(ngModel)]="form.eta" class="form-control" placeholder="Denominación de la ETA">
            </div>
            <div class="field-full">
              <label>Política (directriz territorial)</label>
              <textarea [(ngModel)]="form.politica" class="form-control" rows="2"
                        placeholder="Directriz territorial (columna C de la Matriz A)"></textarea>
            </div>
          </div>
        </div>

        <!-- ======= PASO 5: Lineamiento Estratégico PAD ======= -->
        <div *ngIf="pasoActual === 5">
          <h3 class="step-title">Paso 5: Lineamiento Estratégico PAD</h3>
          <p class="field-hint">Matriz A — columnas D-E; guía 4.3: el lineamiento es el primer elemento a registrar.</p>
          <div class="form-grid">
            <div class="field-full">
              <label>Lineamiento Estratégico (cascada: componente PDESA del paso 1)</label>
              <select [(ngModel)]="form.lineamiento" class="form-control" (change)="onLineamientoChange()">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let ll of lineamientosFiltrados" [ngValue]="ll">
                  {{ ll.codigo }} - {{ ll.denominacion }}
                </option>
              </select>
              <span class="text-secondary" *ngIf="!form.componente">Primero seleccione el componente PDESA en el paso 1.</span>
            </div>
          </div>
        </div>

        <!-- ======= PASO 6: Resultados y Productos PAD (tabla jerárquica) ======= -->
        <div *ngIf="pasoActual === 6">
          <h3 class="step-title">Paso 6: Resultados y Productos PAD</h3>
          <p class="field-hint">
            Matriz A — columnas F-K y U: cada resultado (código
            <span class="codigo">CGEO.lineamiento.correlativo</span>) puede tener
            VARIOS productos (código
            <span class="codigo">CGEO.lineamiento.resultado.correlativo</span>).
            Edición inline tipo Excel: los códigos se autogeneran en vivo y cada
            cambio se guarda automáticamente (sección "resultados", lista completa).
          </p>

          <app-tabla-jerarquica
            [resultados]="form.resultados"
            [cgeo]="form.cgeo"
            [lineamiento]="form.lineamiento"
            [correlativoBase]="correlativoBase()"
            (cambio)="onColeccionCambio()">
          </app-tabla-jerarquica>
        </div>

        <!-- ======= PASO 7: Códigos autogenerados (resumen) ======= -->
        <div *ngIf="pasoActual === 7">
          <h3 class="step-title">Paso 7: Códigos PAD autogenerados</h3>
          <p class="field-hint">
            Los códigos compuestos se generan por el sistema: resultado
            <span class="codigo">CGEO.lineamiento.correlativo</span> y producto
            <span class="codigo">CGEO.lineamiento.resultado.correlativo</span>.
            Revise la colección antes de completar los indicadores.
          </p>
          <div class="resumen-card" *ngIf="form.resultados.length === 0">
            <p>No hay resultados cargados. Regrese al paso 6 y agregue al menos un resultado con sus productos.</p>
          </div>
          <div class="resumen-card" *ngFor="let res of form.resultados; let i = index">
            <h4>Resultado {{ i + 1 }} <span class="codigo">{{ codigoResultado(i) || '—' }}</span></h4>
            <p class="resumen-desc">{{ res.denominacion || 'Sin denominación' }}</p>
            <table class="mini-table" *ngIf="res.productos.length">
              <thead>
                <tr><th>Código</th><th>Producto</th><th>Responsable</th><th>Financ.</th></tr>
              </thead>
              <tbody>
                <tr *ngFor="let prod of res.productos; let j = index">
                  <td><span class="codigo">{{ codigoProducto(i, j) || '—' }}</span></td>
                  <td>{{ prod.denominacion || '—' }}</td>
                  <td>{{ prod.responsable || '—' }}</td>
                  <td>{{ prod.cuenta_con_financiamiento ? 'SÍ' : 'NO' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ======= PASO 8: Indicadores por Resultado ======= -->
        <div *ngIf="pasoActual === 8">
          <h3 class="step-title">Paso 8: Indicadores por Resultado PAD</h3>
          <p class="field-hint">Matriz A — columnas L-T (fila de resultado): indicador, fórmula, unidad, línea base, meta 2030 y programación física 2026-2030.</p>
          <div class="resumen-card" *ngFor="let res of form.resultados; let i = index">
            <h4>Resultado {{ i + 1 }} <span class="codigo">{{ codigoResultado(i) || '—' }}</span>
              <span class="resumen-desc">— {{ res.denominacion || 'Sin denominación' }}</span>
            </h4>
            <div class="form-grid">
              <div class="field-full">
                <label>Indicador</label>
                <textarea [(ngModel)]="res.indicador.indicador" class="form-control" rows="1"
                          placeholder="Variable de medición del resultado PAD"></textarea>
              </div>
              <div class="field-full">
                <label>Fórmula</label>
                <input [(ngModel)]="res.indicador.formula" class="form-control"
                       placeholder="Ej: TCSEE = (N° viviendas con energía / total viviendas) * 100">
              </div>
              <div class="field">
                <label>Unidad de Medida</label>
                <select [(ngModel)]="res.indicador.unidad_medida" class="form-control">
                  <option value="">Seleccionar...</option>
                  <option *ngFor="let um of catalogoUnidades" [value]="um.denominacion">
                    {{ um.denominacion }}
                  </option>
                </select>
              </div>
              <div class="field">
                <label>Línea Base</label>
                <input type="number" step="0.01" [(ngModel)]="res.indicador.linea_base"
                       class="form-control" placeholder="Valor línea base">
              </div>
              <div class="field">
                <label>Meta 2030</label>
                <input type="number" step="0.01" [(ngModel)]="res.indicador.meta_2030"
                       class="form-control" placeholder="Meta al 2030">
              </div>
            </div>
            <h5 class="section-subtitle">Programación Física 2026-2030</h5>
            <div class="quinquenio-grid">
              <div class="field" *ngFor="let year of quinquenio">
                <label>{{ year }}</label>
                <input type="number" step="0.01"
                       [(ngModel)]="res.programacion_fisica[year]"
                       class="form-control" [placeholder]="'Meta ' + year"
                       (input)="onProgramacionFisicaChange()">
              </div>
            </div>
            <div class="total-auto">
              <strong>Total programación física (quinquenio):</strong>
              <span class="total-valor">{{ sumaAnual(res.programacion_fisica) }}</span>
            </div>
          </div>
        </div>

        <!-- ======= PASO 9: Indicadores por Producto ======= -->
        <div *ngIf="pasoActual === 9">
          <h3 class="step-title">Paso 9: Indicadores por Producto PAD</h3>
          <p class="field-hint">Matriz A — columnas L-T (fila de producto): cada producto tiene su propio indicador, fórmula, unidad, línea base, meta 2030 y programación física 2026-2030.</p>
          <div class="resumen-card" *ngFor="let res of form.resultados; let i = index">
            <h4>Resultado {{ i + 1 }} <span class="codigo">{{ codigoResultado(i) || '—' }}</span></h4>
            <div class="producto-card" *ngFor="let prod of res.productos; let j = index">
              <h5>Producto {{ j + 1 }} <span class="codigo">{{ codigoProducto(i, j) || '—' }}</span>
                <span class="resumen-desc">— {{ prod.denominacion || 'Sin denominación' }}</span>
              </h5>
              <div class="form-grid">
                <div class="field-full">
                  <label>Indicador</label>
                  <textarea [(ngModel)]="prod.indicador.indicador" class="form-control" rows="1"
                            placeholder="Variable de medición del producto PAD"></textarea>
                </div>
                <div class="field-full">
                  <label>Fórmula</label>
                  <input [(ngModel)]="prod.indicador.formula" class="form-control"
                         placeholder="Ej: NV = N° de viviendas conectadas">
                </div>
                <div class="field">
                  <label>Unidad de Medida</label>
                  <select [(ngModel)]="prod.indicador.unidad_medida" class="form-control">
                    <option value="">Seleccionar...</option>
                    <option *ngFor="let um of catalogoUnidades" [value]="um.denominacion">
                      {{ um.denominacion }}
                    </option>
                  </select>
                </div>
                <div class="field">
                  <label>Línea Base</label>
                  <input type="number" step="0.01" [(ngModel)]="prod.indicador.linea_base"
                         class="form-control" placeholder="Valor línea base">
                </div>
                <div class="field">
                  <label>Meta 2030</label>
                  <input type="number" step="0.01" [(ngModel)]="prod.indicador.meta_2030"
                         class="form-control" placeholder="Meta al 2030">
                </div>
              </div>
              <h5 class="section-subtitle">Programación Física 2026-2030</h5>
              <div class="quinquenio-grid">
                <div class="field" *ngFor="let year of quinquenio">
                  <label>{{ year }}</label>
                  <input type="number" step="0.01"
                         [(ngModel)]="prod.programacion_fisica[year]"
                         class="form-control" [placeholder]="'Meta ' + year"
                         (input)="onProgramacionFisicaChange()">
                </div>
              </div>
              <div class="total-auto">
                <strong>Total programación física (quinquenio):</strong>
                <span class="total-valor">{{ sumaAnual(prod.programacion_fisica) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ======= PASO 10: Programación Financiera ======= -->
        <div *ngIf="pasoActual === 10">
          <h3 class="step-title">Paso 10: Programación Financiera</h3>
          <p class="field-hint">
            Matriz A — columnas V-AA / Matriz B AB-AG: presupuesto total PAD (referencial) y anual 2026-2030,
            en bolivianos SIN decimales, POR RESULTADO y POR PRODUCTO.
          </p>
          <div class="resumen-card" *ngFor="let res of form.resultados; let i = index">
            <h4>Resultado {{ i + 1 }} <span class="codigo">{{ codigoResultado(i) || '—' }}</span></h4>
            <div class="form-grid">
              <div class="field">
                <label>Presupuesto Total Resultado (Bs.) — autosuma</label>
                <input type="number" step="1" min="0" readonly
                       [value]="sumaAnual(res.presupuesto_anual)"
                       class="form-control total-readonly" placeholder="Se calcula automáticamente">
              </div>
            </div>
            <div class="quinquenio-grid">
              <div class="field" *ngFor="let year of quinquenio">
                <label>Resultado {{ year }} (Bs.)</label>
                <input type="number" step="1" min="0"
                       [(ngModel)]="res.presupuesto_anual[year]"
                       class="form-control" [placeholder]="'Bs. ' + year"
                       (input)="onPresupuestoChange()">
              </div>
            </div>
            <div class="total-auto">
              <strong>Total resultado (quinquenio):</strong>
              <span class="total-valor">Bs {{ sumaAnual(res.presupuesto_anual) }}</span>
            </div>
            <div class="producto-card" *ngFor="let prod of res.productos; let j = index">
              <h5>Producto {{ j + 1 }} <span class="codigo">{{ codigoProducto(i, j) || '—' }}</span></h5>
              <div class="form-grid">
                <div class="field">
                  <label>Presupuesto Total Producto (Bs.) — autosuma</label>
                  <input type="number" step="1" min="0" readonly
                         [value]="sumaAnual(prod.presupuesto_anual)"
                         class="form-control total-readonly" placeholder="Se calcula automáticamente">
                </div>
              </div>
              <div class="quinquenio-grid">
                <div class="field" *ngFor="let year of quinquenio">
                  <label>Producto {{ year }} (Bs.)</label>
                  <input type="number" step="1" min="0"
                         [(ngModel)]="prod.presupuesto_anual[year]"
                         class="form-control" [placeholder]="'Bs. ' + year"
                         (input)="onPresupuestoChange()">
                </div>
              </div>
              <div class="total-auto">
                <strong>Total producto (quinquenio):</strong>
                <span class="total-valor">Bs {{ sumaAnual(prod.presupuesto_anual) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ======= PASO 11: Revisión y Guardado ======= -->
        <div *ngIf="pasoActual === 11">
          <h3 class="step-title">Paso 11: Revisión y Guardado</h3>
          <div class="resumen-card">
            <p>
              Revise los datos antes de materializar. La operación crea, en una sola
              transacción atómica, UN Resultado PAD por cada resultado de la colección
              y UN Producto PAD por cada producto, cada uno con su indicador.
            </p>
            <div class="resumen-grid">
              <div class="resumen-item"><strong>Eje PGDESA:</strong> {{ form.eje ? form.eje.codigo + ' - ' + form.eje.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>Componente PDESA:</strong> {{ form.componente ? form.componente.codigo + ' - ' + form.componente.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>ODS:</strong> {{ form.ods ? 'ODS ' + form.ods.codigo : '—' }}</div>
              <div class="resumen-item"><strong>NDC:</strong> {{ form.ndc ? form.ndc.codigo : '—' }}</div>
              <div class="resumen-item"><strong>NDT:</strong> {{ form.ndt ? form.ndt.codigo : '—' }}</div>
              <div class="resumen-item"><strong>30/30:</strong> {{ form.kmgbf ? form.kmgbf.codigo : '—' }}</div>
              <div class="resumen-item"><strong>Sector:</strong> {{ form.sector ? form.sector.codigo + ' - ' + form.sector.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>Resultado Sectorial:</strong> {{ form.resultado_sectorial ? form.resultado_sectorial.codigo + ' - ' + form.resultado_sectorial.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>CGEO:</strong> {{ form.cgeo ? form.cgeo.codigo + ' - ' + form.cgeo.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>ETA:</strong> {{ form.eta || '—' }}</div>
              <div class="resumen-item"><strong>Política:</strong> {{ form.politica || '—' }}</div>
              <div class="resumen-item"><strong>Lineamiento PAD:</strong> {{ form.lineamiento ? form.lineamiento.codigo + ' - ' + form.lineamiento.denominacion : '—' }}</div>
              <div class="resumen-item"><strong>Resultados:</strong> {{ form.resultados.length }} ({{ totalProductos() }} productos, {{ totalFilas() }} filas en la matriz)</div>
              <div class="resumen-item" *ngFor="let res of form.resultados; let i = index">
                <strong>R{{ i + 1 }} {{ codigoResultado(i) }}:</strong> {{ res.denominacion || '—' }}
                <span class="text-secondary">({{ res.productos.length }} producto(s))</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Navegación -->
        <div class="form-nav">
          <button class="btn btn-outline" (click)="pasoAnterior()" [disabled]="pasoActual === 1">
            ← Anterior
          </button>
          <span class="step-counter">Paso {{ pasoActual }} de 11</span>
          <button class="btn btn-primary" (click)="pasoSiguiente()" *ngIf="pasoActual < 11" [disabled]="guardandoSeccion">
            {{ guardandoSeccion ? 'Guardando...' : 'Siguiente →' }}
          </button>
          <button class="btn btn-primary btn-guardar" (click)="materializar()" *ngIf="pasoActual === 11" [disabled]="materializando">
            {{ materializando ? 'Materializando...' : '💾 Materializar Matriz PAD' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .form-page { padding-bottom: 2rem; max-width: 1280px; margin: 0 auto; }
    .page-header { margin-bottom: 1.25rem; }
    .page-header h2 { font-size: 1.5rem; color: var(--primary); margin-bottom: 0.375rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.9375rem; }

    .stepper { display: flex; gap: 0.375rem; margin-bottom: 1.75rem; overflow-x: auto; padding: 0.5rem 0; }
    .step { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; padding: 0.375rem 0.75rem; border-radius: 8px; font-size: 0.8125rem; white-space: nowrap; opacity: 0.5; }
    .step.active { opacity: 1; background: #E8F5E9; }
    .step.completed { opacity: 0.8; color: var(--primary); }
    .step-circle { width: 28px; height: 28px; border-radius: 50%; background: var(--border); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8125rem; color: var(--text-secondary); }
    .step.active .step-circle { background: var(--primary); color: white; }
    .step.completed .step-circle { background: var(--success); color: white; }
    .step-label { font-weight: 500; }

    .form-card { padding: 2rem; }
    .step-title { font-size: 1.375rem; color: var(--primary); margin-bottom: 1.25rem; padding-bottom: 0.625rem; border-bottom: 2px solid var(--border); }
    .section-subtitle { font-size: 1rem; color: var(--primary-dark); margin: 1rem 0 0.625rem; padding-top: 0.625rem; border-top: 1px solid var(--border); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.375rem; }
    .field-hint { font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem; }
    .field { min-width: 0; }
    .form-control { font-size: 0.9375rem; padding: 0.625rem 0.75rem; }

    /* Textarea de objetivos del paso 1: autoajuste al contenido, solo lectura. */
    .textarea-auto {
      min-height: calc(2 * 1.5em + 0.75rem + 2px); /* mínimo 2 líneas */
      max-height: calc(10 * 1.5em + 0.75rem + 2px); /* ~10 líneas, luego scroll */
      overflow-y: hidden;
      resize: none;
      line-height: 1.5;
      white-space: pre-wrap;
      background: var(--bg);
      cursor: default;
    }
    .textarea-auto:focus { outline: none; box-shadow: none; }

    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; }

    .quinquenio-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; }

    .total-auto {
      grid-column: 1 / -1;
      display: flex; align-items: center; gap: 0.625rem;
      margin-top: 0.625rem; padding: 0.625rem 0.875rem;
      background: var(--bg); border: 1px dashed var(--border);
      border-radius: 8px; font-size: 0.9375rem;
    }
    .total-valor {
      font-weight: 700; color: var(--primary); font-family: 'Courier New', monospace;
    }
    .total-readonly {
      background: var(--bg); color: var(--primary-dark);
      font-weight: 700; font-family: 'Courier New', monospace;
      cursor: default;
    }

    .resultados-list { display: flex; flex-direction: column; gap: 1.25rem; }
    .resultado-card, .producto-card { border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; background: #fff; }
    .producto-card { background: #FAFBFC; margin-top: 1rem; }
    .card-header-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; }
    .card-header-row h4, .card-header-row h5 { margin: 0; color: var(--primary-dark); }
    .card-header-row h4 { font-size: 1.0625rem; }
    .card-header-row h5 { font-size: 0.9375rem; }
    .btn-outline-danger { color: #C62828; border-color: #EF9A9A; background: #fff; }
    .btn-outline-danger:hover { background: #FFEBEE; }
    .btn-sm { font-size: 0.875rem; padding: 0.375rem 0.75rem; }
    .resultado-actions { display: flex; align-items: center; gap: 1.25rem; margin-top: 1.25rem; flex-wrap: wrap; }

    .resumen-card { background: var(--bg); padding: 1.25rem; border-radius: 10px; margin-bottom: 1.25rem; }
    .resumen-card p { font-size: 0.9375rem; color: var(--text-secondary); margin-bottom: 0.625rem; }
    .resumen-card h4 { margin: 0 0 0.375rem; color: var(--primary-dark); font-size: 1.0625rem; }
    .resumen-card h5 { margin: 0.875rem 0 0.375rem; color: var(--primary-dark); font-size: 0.9375rem; }
    .resumen-desc { font-weight: 400; color: var(--text-secondary); }
    .resumen-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .resumen-item { font-size: 0.875rem; padding: 0.375rem 0; }
    .resumen-item strong { color: var(--primary-dark); }

    .mini-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; margin-top: 0.625rem; }
    .mini-table th { text-align: left; padding: 0.5rem 0.625rem; background: var(--border); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.03em; }
    .mini-table td { padding: 0.5rem 0.625rem; border-bottom: 1px solid var(--border); }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.75rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
    .step-counter { font-size: 0.875rem; color: var(--text-secondary); font-weight: 500; }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: #1B5E3B; }

    .alert { padding: 0.875rem 1.25rem; border-radius: 8px; font-size: 0.9375rem; margin-bottom: 1.25rem; }
    .alert-success { background: #E8F5E9; color: #1B5E3B; border: 1px solid #A5D6A7; }
    .alert-danger { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
      .stepper { gap: 0; }
      .step-label { display: none; }
    }
  `],
})
export class MatrizPadWizardComponent implements OnInit {
  pasos = [
    'Planif. Nacional', 'Acuerdos Intl.', 'Planif. Sectorial', 'Contexto Territorial',
    'Lineamiento PAD', 'Resultados y Productos', 'Códigos PAD', 'Indicador Resultado',
    'Indicador Producto', 'Programación Fin.', 'Revisión / Guardar',
  ];
  pasoActual = 1;
  guardandoSeccion = false;
  materializando = false;
  mensajeExito = '';
  mensajeError = '';
  quinquenio = [2026, 2027, 2028, 2029, 2030];

  /** Timer de guardado debounceado de la colección "resultados" (paso 6). */
  private timerColeccion: any = null;

  /** Borrador persistido en backend (guardado incremental). */
  borradorId: string | null = null;
  gestion = 2026;

  /** Textareas autoajustables del paso 1 (objetivos de impacto/efecto). */
  @ViewChild('taImpacto') taImpacto?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('taEfecto') taEfecto?: ElementRef<HTMLTextAreaElement>;

  catalogoODS: any[] = [];
  catalogoEjes: any[] = [];
  catalogoComponentes: any[] = [];
  catalogoLineamientos: any[] = [];
  catalogoSectores: any[] = [];
  catalogoUnidades: any[] = [];
  catalogoNDC: any[] = [];
  catalogoNDT: any[] = [];
  catalogo3030: any[] = [];
  catalogoEntidadesTerritoriales: any[] = [];
  catalogoResultadosSectoriales: any[] = [];
  cargandoCatalogos = false;

  /** Registros existentes para calcular correlativos de códigos compuestos. */
  existentesResultados: any[] = [];
  existentesProductos: any[] = [];

  /** Filtros en cascada: eje → componente → lineamiento */
  get componentesFiltrados(): any[] {
    if (!this.form.eje) return [];
    return this.catalogoComponentes.filter(c => c.eje_codigo === this.form.eje.codigo);
  }
  get lineamientosFiltrados(): any[] {
    if (!this.form.componente) return [];
    return this.catalogoLineamientos.filter(l => l.componente_codigo === this.form.componente.codigo);
  }
  /** Resultados sectoriales del PDS, filtrados por sector; si no hay relación, se muestran libres. */
  get resultadosSectorialesFiltrados(): any[] {
    if (!this.form.sector) return this.catalogoResultadosSectoriales;
    const filtrados = this.catalogoResultadosSectoriales.filter(
      r => r.sector_codigo === this.form.sector.codigo,
    );
    return filtrados.length ? filtrados : this.catalogoResultadosSectoriales;
  }

  /** Correlativo base del resultado dentro del lineamiento (siguiente libre). */
  correlativoBase(): number {
    if (!this.form.lineamiento) return 1;
    const lid = this.form.lineamiento.id;
    return this.existentesResultados.filter(
      r => r.lineamiento_pad_catalogo === lid && r.vigencia_desde === this.gestion,
    ).length + 1;
  }

  /** Código compuesto del resultado i: CGEO.lineamiento.(base + i). */
  codigoResultado(i: number): string {
    if (!this.form.cgeo || !this.form.lineamiento) return '';
    return `${this.form.cgeo.codigo}.${this.form.lineamiento.codigo}.${this.correlativoBase() + i}`;
  }
  /** Código compuesto del producto j del resultado i: CGEO.lineamiento.resultado.(j+1). */
  codigoProducto(i: number, j: number): string {
    const base = this.codigoResultado(i);
    return base ? `${base}.${j + 1}` : '';
  }

  form: any = {
    eje: null,
    objetivo_impacto: '',
    componente: null,
    objetivo_efecto: '',
    ods: null,
    ndc: null,
    ndt: null,
    kmgbf: null,
    sector: null,
    resultado_sectorial: null,
    cgeo: null,
    eta: '',
    politica: '',
    lineamiento: null,
    resultados: [],
  };

  constructor(
    private api: ApiService,
    private service: MatricesPadService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.cargarCatalogos();
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      // Continuar borrador existente: cargar datos persistidos
      this.service.obtener(id).subscribe({
        next: (b) => {
          this.borradorId = b.id;
          this.gestion = b.gestion;
          this.hidratarFormulario(b.datos || {});
          this.cargarExistentes();
          this.cdr.detectChanges();
          this.autoAjustarTextareas();
        },
        error: (err) => {
          console.error('Error cargando borrador', err);
          this.mensajeError = 'No se pudo cargar el borrador.';
          this.cdr.detectChanges();
        },
      });
    } else {
      // Nuevo borrador: crear al inicio (guardado incremental por paso)
      this.service.crear({ gestion: this.gestion }).subscribe({
        next: (b) => {
          this.borradorId = b.id;
          this.agregarResultado(); // la colección inicia con 1 resultado + 1 producto
          this.cargarExistentes();
          this.cdr.detectChanges();
        },
        error: (err) => {
          console.error('Error creando borrador', err);
          this.mensajeError = 'No se pudo iniciar el borrador de Matriz PAD.';
          this.cdr.detectChanges();
        },
      });
    }
  }

  ngOnDestroy(): void {
    if (this.timerColeccion) {
      clearTimeout(this.timerColeccion);
      this.timerColeccion = null;
    }
  }

  private cargarCatalogos(): void {
    this.cargandoCatalogos = true;
    this.api.get<any>('/articulacion/matrices/catalogos_articulacion/', { gestion: 2026 }).subscribe({
      next: (r) => {
        this.catalogoEjes = r.ejes || [];
        this.catalogoComponentes = r.componentes || [];
        this.catalogoLineamientos = r.lineamientos || [];
        this.catalogoSectores = r.sectores || [];
        this.catalogoUnidades = r.unidades_medida || [];
        this.catalogoEntidadesTerritoriales = r.entidades_territoriales || [];
        this.catalogoResultadosSectoriales = r.resultados_sectoriales || [];
        this.cargandoCatalogos = false;
        this.cdr.detectChanges();
      },
      error: () => { this.cargandoCatalogos = false; this.cdr.detectChanges(); },
    });
    this.api.get<any>('/articulacion/metas-acuerdo/', { tipo_acuerdo: 'NDC' }).subscribe({
      next: (r) => { this.catalogoNDC = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.catalogoNDC = []; },
    });
    this.api.get<any>('/articulacion/metas-acuerdo/', { tipo_acuerdo: 'NDT' }).subscribe({
      next: (r) => { this.catalogoNDT = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.catalogoNDT = []; },
    });
    this.api.get<any>('/articulacion/metas-acuerdo/', { tipo_acuerdo: 'KMGBF' }).subscribe({
      next: (r) => { this.catalogo3030 = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.catalogo3030 = []; },
    });
    this.api.get<any>('/articulacion/acuerdos/', { tipo_acuerdo: 'ODS' }).subscribe({
      next: (r) => { this.catalogoODS = r.results || r || []; this.cdr.detectChanges(); },
      error: () => {
        this.catalogoODS = [
          { id: 1, codigo: 'ODS 1', nombre: 'Fin de la Pobreza' },
          { id: 2, codigo: 'ODS 2', nombre: 'Hambre Cero' },
          { id: 3, codigo: 'ODS 3', nombre: 'Salud y Bienestar' },
          { id: 4, codigo: 'ODS 4', nombre: 'Educación de Calidad' },
          { id: 5, codigo: 'ODS 5', nombre: 'Igualdad de Género' },
          { id: 6, codigo: 'ODS 6', nombre: 'Agua Limpia y Saneamiento' },
          { id: 7, codigo: 'ODS 7', nombre: 'Energía Asequible y No Contaminante' },
          { id: 8, codigo: 'ODS 8', nombre: 'Trabajo Decente y Crecimiento Económico' },
          { id: 9, codigo: 'ODS 9', nombre: 'Industria, Innovación e Infraestructura' },
          { id: 10, codigo: 'ODS 10', nombre: 'Reducción de las Desigualdades' },
          { id: 11, codigo: 'ODS 11', nombre: 'Ciudades y Comunidades Sostenibles' },
          { id: 12, codigo: 'ODS 12', nombre: 'Producción y Consumo Responsables' },
          { id: 13, codigo: 'ODS 13', nombre: 'Acción por el Clima' },
          { id: 14, codigo: 'ODS 14', nombre: 'Vida Submarina' },
          { id: 15, codigo: 'ODS 15', nombre: 'Vida de Ecosistemas Terrestres' },
          { id: 16, codigo: 'ODS 16', nombre: 'Paz, Justicia e Instituciones Sólidas' },
          { id: 17, codigo: 'ODS 17', nombre: 'Alianzas para Lograr los Objetivos' },
        ];
      },
    });
  }

  private cargarExistentes(): void {
    this.api.get<any>('/articulacion/resultados-pad/').subscribe({
      next: (r) => { this.existentesResultados = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.existentesResultados = []; },
    });
    this.api.get<any>('/articulacion/productos-pad/').subscribe({
      next: (r) => { this.existentesProductos = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.existentesProductos = []; },
    });
  }

  // -------------------------------------------------------------------------
  // Colección de resultados (pasos 6-10)
  // -------------------------------------------------------------------------

  private nuevoIndicador(): IndicadorDraft {
    return { indicador: '', formula: '', unidad_medida: '', linea_base: null, meta_2030: null };
  }
  private nuevoProgramacionFisica(): Record<string, number | null> {
    return this.quinquenio.reduce((acc, y) => { acc[String(y)] = null; return acc; }, {} as Record<string, number | null>);
  }
  private nuevoPresupuestoAnual(): Record<string, number | null> {
    return this.quinquenio.reduce((acc, y) => { acc[String(y)] = null; return acc; }, {} as Record<string, number | null>);
  }

  private nuevoProducto(): ProductoDraft {
    return {
      denominacion: '',
      territorializacion: '',
      responsable: '',
      cuenta_con_financiamiento: false,
      indicador: this.nuevoIndicador(),
      programacion_fisica: this.nuevoProgramacionFisica(),
      presupuesto_total: null,
      presupuesto_anual: this.nuevoPresupuestoAnual(),
    };
  }

  private nuevoResultado(): ResultadoDraft {
    return {
      denominacion: '',
      territorializacion: '',
      responsable: '',
      cuenta_con_financiamiento: false,
      indicador: this.nuevoIndicador(),
      programacion_fisica: this.nuevoProgramacionFisica(),
      presupuesto_total: null,
      presupuesto_anual: this.nuevoPresupuestoAnual(),
      productos: [this.nuevoProducto()],
    };
  }

  agregarResultado(): void {
    this.form.resultados.push(this.nuevoResultado());
    this.cdr.detectChanges();
  }

  /**
   * La tabla jerárquica emite este evento ante CUALQUIER cambio (edición de
   * campo, agregar, eliminar, duplicar). El guardado es incremental y
   * debounceado: PATCH de la sección "resultados" con la lista completa.
   * Si la colección aún tiene denominaciones vacías, se omite el PATCH
   * (el backend las rechaza con 400) y se reintenta con el siguiente cambio.
   */
  onColeccionCambio(): void {
    this.cdr.detectChanges();
    if (this.timerColeccion) {
      clearTimeout(this.timerColeccion);
    }
    this.timerColeccion = setTimeout(() => {
      this.timerColeccion = null;
      if (this.coleccionValida()) {
        this.guardarSeccion(6);
      }
    }, 600);
  }

  /** La colección es persistible solo si todas las denominaciones están completas. */
  private coleccionValida(): boolean {
    return this.form.resultados.length > 0 && this.form.resultados.every(
      (r: ResultadoDraft) => !!r.denominacion.trim() &&
        r.productos.every((p: ProductoDraft) => !!p.denominacion.trim()),
    );
  }

  totalProductos(): number {
    return this.form.resultados.reduce(
      (acc: number, r: ResultadoDraft) => acc + r.productos.length, 0,
    );
  }

  totalFilas(): number {
    return this.form.resultados.length + this.totalProductos();
  }

  /** Suma los 5 valores anuales del quinquenio (programación física o financiera). */
  sumaAnual(datos: Record<string, number | null> | undefined): string {
    if (!datos) return '0';
    const total = this.quinquenio.reduce((acc, y) => {
      const v = Number(datos[String(y)]);
      return acc + (Number.isFinite(v) ? v : 0);
    }, 0);
    // Sin decimales si es entero; con 2 si tiene fracción (física puede ser 0.78).
    const esEntero = Number.isInteger(total);
    return esEntero ? String(total) : total.toFixed(2);
  }

  /** Recalcula totales y guarda cuando cambia la programación física. */
  onProgramacionFisicaChange(): void {
    this.onColeccionCambio();
  }

  /** Recalcula el presupuesto total (autosuma) y guarda cuando cambia un anual. */
  onPresupuestoChange(): void {
    // Autosuma: el total de cada resultado/producto = suma de los 5 anuales.
    for (const res of this.form.resultados) {
      res.presupuesto_total = Number(this.sumaAnual(res.presupuesto_anual)) || null;
      for (const prod of res.productos) {
        prod.presupuesto_total = Number(this.sumaAnual(prod.presupuesto_anual)) || null;
      }
    }
    this.onColeccionCambio();
  }

  /** Serializa la colección completa (contrato PATCH sección "resultados"). */
  private coleccionResultados(): any[] {
    return this.form.resultados.map((res: ResultadoDraft) => ({
      denominacion: res.denominacion,
      territorializacion: res.territorializacion,
      responsable: res.responsable,
      cuenta_con_financiamiento: !!res.cuenta_con_financiamiento,
      indicador: {
        indicador: res.indicador.indicador,
        formula: res.indicador.formula,
        unidad_medida: res.indicador.unidad_medida,
        linea_base: res.indicador.linea_base ?? null,
        meta_2030: res.indicador.meta_2030 ?? null,
      },
      programacion_fisica: this.soloValores(res.programacion_fisica),
      presupuesto_total: res.presupuesto_total ?? null,
      presupuesto_anual: this.soloValores(res.presupuesto_anual),
      productos: res.productos.map((p: ProductoDraft) => ({
        denominacion: p.denominacion,
        territorializacion: p.territorializacion,
        responsable: p.responsable,
        cuenta_con_financiamiento: !!p.cuenta_con_financiamiento,
        indicador: {
          indicador: p.indicador.indicador,
          formula: p.indicador.formula,
          unidad_medida: p.indicador.unidad_medida,
          linea_base: p.indicador.linea_base ?? null,
          meta_2030: p.indicador.meta_2030 ?? null,
        },
        programacion_fisica: this.soloValores(p.programacion_fisica),
        presupuesto_total: p.presupuesto_total ?? null,
        presupuesto_anual: this.soloValores(p.presupuesto_anual),
      })),
    }));
  }

  /** Descarta valores null/undefined del quinquenio. */
  private soloValores(dict: Record<string, number | null | undefined>): Record<string, number> {
    const salida: Record<string, number> = {};
    for (const year of this.quinquenio) {
      const v: number | null | undefined = dict ? dict[String(year)] : null;
      if (v !== null && v !== undefined) {
        salida[String(year)] = Number(v);
      }
    }
    return salida;
  }

  /** Restaura el formulario desde las secciones persistidas del borrador. */
  private hidratarFormulario(datos: Record<string, any>): void {
    const p1 = datos['p1_nacional'] || {};
    const p2 = datos['p2_acuerdos'] || {};
    const p3 = datos['p3_sectorial'] || {};
    const p4 = datos['p4_territorial'] || {};
    const p5 = datos['p5_lineamiento'] || {};

    this.form.eje = p1['eje'] || null;
    this.form.objetivo_impacto = p1['objetivo_impacto'] || '';
    this.form.componente = p1['componente'] || null;
    this.form.objetivo_efecto = p1['objetivo_efecto'] || '';
    this.form.ods = p2['ods'] || null;
    this.form.ndc = p2['ndc'] || null;
    this.form.ndt = p2['ndt'] || null;
    this.form.kmgbf = p2['kmgbf'] || null;
    this.form.sector = p3['sector'] || null;
    this.form.resultado_sectorial = p3['resultado_sectorial'] || null;
    this.form.cgeo = p4['cgeo'] || null;
    this.form.eta = p4['eta'] || '';
    this.form.politica = p4['politica'] || '';
    this.form.lineamiento = p5['lineamiento'] || null;

    // Colección "resultados" (formato nuevo) o transformación legacy p6..p10
    const resultadosRaw = datos['resultados'];
    if (Array.isArray(resultadosRaw) && resultadosRaw.length) {
      this.form.resultados = resultadosRaw.map((r: any) => this.hidratarResultado(r));
    } else {
      const p6 = datos['p6_resultado'] || {};
      const p7 = datos['p7_producto'] || {};
      const p8 = datos['p8_indicador_resultado'] || {};
      const p9 = datos['p9_indicador_producto'] || {};
      const p10 = datos['p10_financiera'] || {};
      const resultadoLegacy: any = {
        denominacion: p6['denominacion'] || '',
        territorializacion: p6['territorializacion'] || '',
        responsable: p6['responsable'] || '',
        cuenta_con_financiamiento: !!p6['cuenta_con_financiamiento'],
        indicador: {
          indicador: p8['indicador'] || '',
          formula: p8['formula'] || '',
          unidad_medida: p8['unidad_medida'] || '',
          linea_base: p8['linea_base'] ?? null,
          meta_2030: p8['meta_2030'] ?? null,
        },
        programacion_fisica: this.hidratarQuinquenio(p8['programacion_fisica']),
        presupuesto_total: p10['presupuesto_total'] ?? null,
        presupuesto_anual: this.hidratarQuinquenio(p10['presupuesto_anual']),
        productos: [{
          denominacion: p7['denominacion'] || '',
          territorializacion: p7['territorializacion'] || '',
          responsable: p7['responsable'] || '',
          cuenta_con_financiamiento: !!p7['cuenta_con_financiamiento'],
          indicador: {
            indicador: p9['indicador'] || '',
            formula: p9['formula'] || '',
            unidad_medida: p9['unidad_medida'] || '',
            linea_base: p9['linea_base'] ?? null,
            meta_2030: p9['meta_2030'] ?? null,
          },
          programacion_fisica: this.hidratarQuinquenio(p9['programacion_fisica']),
          presupuesto_total: p10['presupuesto_total'] ?? null,
          presupuesto_anual: this.hidratarQuinquenio(p10['presupuesto_anual']),
        }],
      };
      this.form.resultados = [this.hidratarResultado(resultadoLegacy)];
    }
  }

  private hidratarResultado(raw: any): ResultadoDraft {
    const ind = raw['indicador'] || {};
    const prodRaw = Array.isArray(raw['productos']) ? raw['productos'] : [];
    return {
      denominacion: raw['denominacion'] || '',
      territorializacion: raw['territorializacion'] || '',
      responsable: raw['responsable'] || '',
      cuenta_con_financiamiento: !!raw['cuenta_con_financiamiento'],
      indicador: {
        indicador: ind['indicador'] || '',
        formula: ind['formula'] || '',
        unidad_medida: ind['unidad_medida'] || '',
        linea_base: ind['linea_base'] ?? null,
        meta_2030: ind['meta_2030'] ?? null,
      },
      programacion_fisica: this.hidratarQuinquenio(raw['programacion_fisica']),
      presupuesto_total: raw['presupuesto_total'] ?? null,
      presupuesto_anual: this.hidratarQuinquenio(raw['presupuesto_anual']),
      productos: prodRaw.map((p: any) => {
        const pInd = p['indicador'] || {};
        return {
          denominacion: p['denominacion'] || '',
          territorializacion: p['territorializacion'] || '',
          responsable: p['responsable'] || '',
          cuenta_con_financiamiento: !!p['cuenta_con_financiamiento'],
          indicador: {
            indicador: pInd['indicador'] || '',
            formula: pInd['formula'] || '',
            unidad_medida: pInd['unidad_medida'] || '',
            linea_base: pInd['linea_base'] ?? null,
            meta_2030: pInd['meta_2030'] ?? null,
          },
          programacion_fisica: this.hidratarQuinquenio(p['programacion_fisica']),
          presupuesto_total: p['presupuesto_total'] ?? null,
          presupuesto_anual: this.hidratarQuinquenio(p['presupuesto_anual']),
        };
      }),
    };
  }

  private hidratarQuinquenio(dict: any): Record<string, number | null> {
    dict = dict || {};
    return this.quinquenio.reduce((acc, y) => {
      acc[String(y)] = dict[String(y)] ?? null;
      return acc;
    }, {} as Record<string, number | null>);
  }
  /** Sección del wizard que corresponde al paso actual (PATCH por sección). */
  private seccionDelPaso(paso: number): { seccion: string; valores: any } | null {
    switch (paso) {
      case 1:
        return {
          seccion: 'p1_nacional',
          valores: {
            eje: this.form.eje,
            objetivo_impacto: this.form.objetivo_impacto,
            componente: this.form.componente,
            objetivo_efecto: this.form.objetivo_efecto,
          },
        };
      case 2:
        return {
          seccion: 'p2_acuerdos',
          valores: {
            ods: this.form.ods,
            ndc: this.form.ndc,
            ndt: this.form.ndt,
            kmgbf: this.form.kmgbf,
          },
        };
      case 3:
        return {
          seccion: 'p3_sectorial',
          valores: {
            sector: this.form.sector,
            resultado_sectorial: this.form.resultado_sectorial,
          },
        };
      case 4:
        return {
          seccion: 'p4_territorial',
          valores: {
            cgeo: this.form.cgeo,
            eta: this.form.eta,
            politica: this.form.politica,
          },
        };
      case 5:
        return {
          seccion: 'p5_lineamiento',
          valores: { lineamiento: this.form.lineamiento },
        };
      // Pasos 6-10: la sección "resultados" SIEMPRE se envía como la lista
      // completa (el wizard mantiene la colección en memoria y la reemplaza
      // al agregar/editar resultado o producto).
      case 6:
      case 7:
      case 8:
      case 9:
      case 10:
        return {
          seccion: 'resultados',
          valores: this.coleccionResultados(),
        };
      default:
        return null;
    }
  }

  /** Guardado incremental: PATCH de la sección del paso indicado. */
  private guardarSeccion(paso: number): Promise<boolean> {
    if (!this.borradorId) return Promise.resolve(false);
    const seccionPaso = this.seccionDelPaso(paso);
    if (!seccionPaso) return Promise.resolve(true);
    return new Promise((resolve) => {
      this.service.guardarSeccion(
        this.borradorId!, seccionPaso.seccion, seccionPaso.valores,
      ).subscribe({
        next: () => resolve(true),
        error: (err) => {
          console.error('Error guardando sección', err);
          this.mensajeError = 'No se pudo guardar el paso actual en el backend.';
          this.cdr.detectChanges();
          resolve(false);
        },
      });
    });
  }

  onEjeChange(): void {
    // Autollenado del Objetivo de Impacto desde el catálogo PGDESA.
    this.form.objetivo_impacto = this.form.eje?.objetivo_impacto || '';
    this.form.componente = null;
    this.form.objetivo_efecto = '';
    this.form.lineamiento = null;
    this.cdr.detectChanges();
    this.autoAjustarTextareas();
  }

  onComponenteChange(): void {
    // Autollenado del Objetivo de Efecto desde el catálogo PDESA.
    this.form.objetivo_efecto = this.form.componente?.objetivo_efecto || '';
    this.form.lineamiento = null;
    this.cdr.detectChanges();
    this.autoAjustarTextareas();
  }

  /**
   * Autoajusta la altura de un textarea al contenido: mínimo 2 líneas y
   * scroll vertical cuando el texto excede ~6 líneas. Se invoca en input
   * y change para que el cuadro crezca/encoga mientras se edita.
   */
  autoAjustarTextarea(event: Event): void {
    const textarea = event?.target as HTMLTextAreaElement | null;
    if (!textarea) return;
    this.ajustarAlturaTextarea(textarea);
  }

  private ajustarAlturaTextarea(textarea: HTMLTextAreaElement): void {
    textarea.style.height = 'auto';
    // Límite de ~10 líneas: el resto se desplaza con scroll interno.
    const alturaMaxima = 10 * 24; // 24px por línea aprox.
    const alturaContenido = Math.min(textarea.scrollHeight, alturaMaxima);
    textarea.style.height = `${alturaContenido}px`;
    textarea.style.overflowY = textarea.scrollHeight > alturaMaxima ? 'auto' : 'hidden';
  }

  private autoAjustarTextareas(): void {
    if (this.taImpacto?.nativeElement) {
      this.ajustarAlturaTextarea(this.taImpacto.nativeElement);
    }
    if (this.taEfecto?.nativeElement) {
      this.ajustarAlturaTextarea(this.taEfecto.nativeElement);
    }
  }

  onLineamientoChange(): void {
    this.cdr.detectChanges();
  }

  onCgeoChange(): void {
    if (this.form.cgeo) {
      this.form.eta = this.form.cgeo.denominacion;
    }
    this.cdr.detectChanges();
  }

  onSectorChange(): void {
    this.form.resultado_sectorial = null;
    this.cdr.detectChanges();
  }

  irAPaso(paso: number): void {
    if (paso >= 1 && paso <= 11 && this.borradorId) {
      // Guarda la sección actual (best effort) y navega
      this.guardarSeccion(this.pasoActual).then(() => {
        this.pasoActual = paso;
        this.mensajeError = '';
        this.mensajeExito = '';
        this.cdr.detectChanges();
        if (paso === 1) this.autoAjustarTextareas();
      });
    }
  }

  pasoAnterior(): void {
    if (this.pasoActual > 1) {
      this.pasoActual--;
      this.mensajeError = '';
      this.mensajeExito = '';
      this.cdr.detectChanges();
    }
  }

  pasoSiguiente(): void {
    if (!this.validarPasoActual()) return;
    this.guardandoSeccion = true;
    this.mensajeError = '';
    this.guardarSeccion(this.pasoActual).then((ok) => {
      this.guardandoSeccion = false;
      if (ok) {
        this.pasoActual++;
        this.cdr.detectChanges();
      }
    });
  }

  private validarPasoActual(): boolean {
    this.mensajeError = '';
    if (this.pasoActual === 4 && !this.form.cgeo) {
      this.mensajeError = 'Debe seleccionar el código geográfico (CGEO).';
      return false;
    }
    if (this.pasoActual === 5 && !this.form.lineamiento) {
      this.mensajeError = 'Debe seleccionar el lineamiento estratégico PAD.';
      return false;
    }
    if (this.pasoActual === 6) {
      if (!this.form.resultados.length) {
        this.mensajeError = 'Agregue al menos un resultado PAD.';
        return false;
      }
      const sinNombre = this.form.resultados.find(
        (r: ResultadoDraft) => !r.denominacion.trim(),
      );
      if (sinNombre) {
        this.mensajeError = 'Complete la denominación de todos los resultados.';
        return false;
      }
      const sinProducto = this.form.resultados.find(
        (r: ResultadoDraft) => r.productos.some(p => !p.denominacion.trim()),
      );
      if (sinProducto) {
        this.mensajeError = 'Complete la denominación de todos los productos.';
        return false;
      }
    }
    if (this.pasoActual === 8) {
      const incompleto = this.form.resultados.find(
        (r: ResultadoDraft) => !r.indicador.indicador || !r.indicador.unidad_medida,
      );
      if (incompleto) {
        this.mensajeError = 'Complete indicador y unidad de medida de todos los resultados.';
        return false;
      }
    }
    if (this.pasoActual === 9) {
      const incompleto = this.form.resultados.find(
        (r: ResultadoDraft) => r.productos.some(
          p => !p.indicador.indicador || !p.indicador.unidad_medida,
        ),
      );
      if (incompleto) {
        this.mensajeError = 'Complete indicador y unidad de medida de todos los productos.';
        return false;
      }
    }
    return true;
  }

  /** Paso 11: guarda la colección completa y materializa el borrador. */
  materializar(): void {
    if (!this.borradorId) return;
    this.materializando = true;
    this.mensajeError = '';
    this.mensajeExito = '';
    this.guardarSeccion(10).then((ok) => {
      if (!ok) {
        this.materializando = false;
        return;
      }
      this.service.materializar(this.borradorId!).subscribe({
        next: (r) => {
          this.materializando = false;
          this.mensajeExito =
            `✅ Matriz PAD materializada: ${r.total_resultados} resultado(s) y ` +
            `${r.total_productos} producto(s) (${r.codigos ? r.codigos.resultados.join(', ') : ''}). ` +
            'Redirigiendo...';
          this.cdr.detectChanges();
          setTimeout(
            () => this.router.navigate(['/matrices-pad']),
            2500,
          );
        },
        error: (err) => {
          console.error('Error materializando', err);
          this.materializando = false;
          this.mensajeError =
            '❌ No se pudo materializar la matriz. Verifique que los datos estén completos.';
          this.cdr.detectChanges();
        },
      });
    });
  }
}
