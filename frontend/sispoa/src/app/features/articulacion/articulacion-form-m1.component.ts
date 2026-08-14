import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m1',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nueva Articulación PAD → PEI</h2>
        <p class="text-secondary">
          Secuencia metodológica de la guía PAD (4.5.2) y sus matrices A/B:
          nacional → acuerdos → sectorial → territorial → indicadores → programación → PEI.
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
              <input [(ngModel)]="form.objetivo_impacto" class="form-control" placeholder="Objetivo de impacto del PGDESA">
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
              <input [(ngModel)]="form.objetivo_efecto" class="form-control" placeholder="Efecto esperado del PDESA">
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
                <option *ngFor="let ods of catalogoODS" [ngValue]="ods">
                  ODS {{ ods.codigo }} - {{ ods.denominacion || ods.nombre }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>NDC (Contribución Nacional Determinada)</label>
              <select [(ngModel)]="form.ndc" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let ndc of catalogoNDC" [ngValue]="ndc">
                  {{ ndc.codigo }} - {{ ndc.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>NDT (Principios de Navegación para el Desarrollo)</label>
              <select [(ngModel)]="form.ndt" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
                <option *ngFor="let ndt of catalogoNDT" [ngValue]="ndt">
                  {{ ndt.codigo }} - {{ ndt.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Compromisos 30/30 (KMGBF)</label>
              <select [(ngModel)]="form.kmgbf" class="form-control">
                <option [ngValue]="null">Seleccionar...</option>
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
          <p class="field-hint">Matriz A — columnas D-E; guía 4.3: el lineamiento es el primer elemento a registrar, y organiza los demás elementos del plan.</p>
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

        <!-- ======= PASO 6: Resultado PAD ======= -->
        <div *ngIf="pasoActual === 6">
          <h3 class="step-title">Paso 6: Resultado PAD</h3>
          <p class="field-hint">Matriz A — columnas F-G: código compuesto CGEO.lineamiento.correlativo (autogenerado) + denominación en pretérito.</p>
          <div class="form-grid">
            <div class="field">
              <label>Código Resultado PAD (autogenerado)</label>
              <input [value]="codigoResultadoCompuesto" class="form-control codigo-readonly" readonly>
            </div>
            <div class="field">
              <label>¿Cuenta con financiamiento?</label>
              <select [(ngModel)]="form.resultado.cuenta_con_financiamiento" class="form-control">
                <option [ngValue]="true">SÍ</option>
                <option [ngValue]="false">NO</option>
              </select>
            </div>
            <div class="field-full">
              <label>Denominación del Resultado PAD (pretérito)</label>
              <textarea [(ngModel)]="form.resultado.denominacion" class="form-control" rows="2"
                        placeholder="Ej: Se ha incrementado la cobertura del servicio de energía eléctrica..."></textarea>
            </div>
            <div class="field">
              <label>Territorialización</label>
              <input [(ngModel)]="form.resultado.territorializacion" class="form-control"
                     placeholder="Ej: COMUNIDAD 1, DISTRITO 4,5">
            </div>
            <div class="field">
              <label>Responsable (entidad)</label>
              <input [(ngModel)]="form.resultado.responsable" class="form-control"
                     placeholder="Ej: Gobierno Autónomo Municipal de ...">
            </div>
          </div>
        </div>

        <!-- ======= PASO 7: Producto PAD ======= -->
        <div *ngIf="pasoActual === 7">
          <h3 class="step-title">Paso 7: Producto PAD</h3>
          <p class="field-hint">Matriz A — columnas H-K y U: código compuesto CGEO.lineamiento.resultado.correlativo (autogenerado) + territorialización + responsable + financiamiento.</p>
          <div class="form-grid">
            <div class="field">
              <label>Código Producto PAD (autogenerado)</label>
              <input [value]="codigoProductoCompuesto" class="form-control codigo-readonly" readonly>
            </div>
            <div class="field">
              <label>¿Cuenta con financiamiento?</label>
              <select [(ngModel)]="form.producto.cuenta_con_financiamiento" class="form-control">
                <option [ngValue]="true">SÍ</option>
                <option [ngValue]="false">NO</option>
              </select>
            </div>
            <div class="field-full">
              <label>Denominación del Producto PAD</label>
              <textarea [(ngModel)]="form.producto.denominacion" class="form-control" rows="2"
                        placeholder="Bien, servicio o intervención (proyecto/programa)"></textarea>
            </div>
            <div class="field">
              <label>Territorialización</label>
              <input [(ngModel)]="form.producto.territorializacion" class="form-control"
                     placeholder="Ej: COMUNIDAD 1, DISTRITO 4,5">
            </div>
            <div class="field">
              <label>Responsable (entidad)</label>
              <input [(ngModel)]="form.producto.responsable" class="form-control"
                     placeholder="Ej: ENDE Corporación, MDRyT, Programa Mi Riego">
            </div>
          </div>
        </div>

        <!-- ======= PASO 8: Indicador Resultado PAD ======= -->
        <div *ngIf="pasoActual === 8">
          <h3 class="step-title">Paso 8: Indicador Resultado PAD</h3>
          <p class="field-hint">Matriz A — columnas L-T (fila de resultado): indicador, fórmula, unidad, línea base, meta 2030 y programación física 2026-2030.</p>
          <div class="form-grid">
            <div class="field-full">
              <label>Indicador</label>
              <textarea [(ngModel)]="form.indicador_resultado.indicador" class="form-control" rows="2"
                        placeholder="Variable de medición del resultado PAD"></textarea>
            </div>
            <div class="field-full">
              <label>Fórmula</label>
              <input [(ngModel)]="form.indicador_resultado.formula" class="form-control"
                     placeholder="Ej: TCSEE = (N° de viviendas con energía / total viviendas) * 100">
            </div>
            <div class="field">
              <label>Unidad de Medida</label>
              <select [(ngModel)]="form.indicador_resultado.unidad_medida" class="form-control">
                <option value="">Seleccionar...</option>
                <option *ngFor="let um of catalogoUnidades" [value]="um.denominacion">
                  {{ um.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Línea Base</label>
              <input type="number" step="0.01" [(ngModel)]="form.indicador_resultado.linea_base"
                     class="form-control" placeholder="Valor línea base">
            </div>
            <div class="field">
              <label>Meta 2030</label>
              <input type="number" step="0.01" [(ngModel)]="form.indicador_resultado.meta_2030"
                     class="form-control" placeholder="Meta al 2030">
            </div>
          </div>
          <h4 class="section-subtitle">Programación Física 2026-2030</h4>
          <div class="quinquenio-grid">
            <div class="field" *ngFor="let year of quinquenio">
              <label>{{ year }}</label>
              <input type="number" step="0.01"
                     [(ngModel)]="form.pf_resultado[year]"
                     class="form-control" [placeholder]="'Meta ' + year">
            </div>
          </div>
        </div>

        <!-- ======= PASO 9: Indicador Producto PAD ======= -->
        <div *ngIf="pasoActual === 9">
          <h3 class="step-title">Paso 9: Indicador Producto PAD</h3>
          <p class="field-hint">Matriz A — columnas L-T (fila de producto): indicador, fórmula, unidad, línea base, meta 2030 y programación física 2026-2030.</p>
          <div class="form-grid">
            <div class="field-full">
              <label>Indicador</label>
              <textarea [(ngModel)]="form.indicador_producto.indicador" class="form-control" rows="2"
                        placeholder="Variable de medición del producto PAD"></textarea>
            </div>
            <div class="field-full">
              <label>Fórmula</label>
              <input [(ngModel)]="form.indicador_producto.formula" class="form-control"
                     placeholder="Ej: NV = N° de viviendas conectadas">
            </div>
            <div class="field">
              <label>Unidad de Medida</label>
              <select [(ngModel)]="form.indicador_producto.unidad_medida" class="form-control">
                <option value="">Seleccionar...</option>
                <option *ngFor="let um of catalogoUnidades" [value]="um.denominacion">
                  {{ um.denominacion }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>Línea Base</label>
              <input type="number" step="0.01" [(ngModel)]="form.indicador_producto.linea_base"
                     class="form-control" placeholder="Valor línea base">
            </div>
            <div class="field">
              <label>Meta 2030</label>
              <input type="number" step="0.01" [(ngModel)]="form.indicador_producto.meta_2030"
                     class="form-control" placeholder="Meta al 2030">
            </div>
          </div>
          <h4 class="section-subtitle">Programación Física 2026-2030</h4>
          <div class="quinquenio-grid">
            <div class="field" *ngFor="let year of quinquenio">
              <label>{{ year }}</label>
              <input type="number" step="0.01"
                     [(ngModel)]="form.pf_producto[year]"
                     class="form-control" [placeholder]="'Meta ' + year">
            </div>
          </div>
        </div>

        <!-- ======= PASO 10: Programación Financiera ======= -->
        <div *ngIf="pasoActual === 10">
          <h3 class="step-title">Paso 10: Programación Financiera</h3>
          <p class="field-hint">
            Matriz A — columnas V-AA / Matriz B AB-AG: presupuesto total PAD (referencial) y anual 2026-2030,
            en bolivianos SIN decimales. El desglose corriente/inversión corresponde al SIGEP/POA, no a las matrices PAD.
          </p>
          <div class="form-grid">
            <div class="field">
              <label>Presupuesto Total PAD (Bs.)</label>
              <input type="number" step="1" min="0" [(ngModel)]="form.presupuesto_total"
                     class="form-control" placeholder="Ej: 34000000">
            </div>
          </div>
          <h4 class="section-subtitle">Presupuesto Anual 2026-2030 (Bs.)</h4>
          <div class="quinquenio-grid">
            <div class="field" *ngFor="let year of quinquenio">
              <label>{{ year }}</label>
              <input type="number" step="1" min="0"
                     [(ngModel)]="form.presupuesto_anual[year]"
                     class="form-control" [placeholder]="'Bs. ' + year">
            </div>
          </div>
        </div>

        <!-- ======= PASO 11: Articulación PEI ======= -->
        <div *ngIf="pasoActual === 11">
          <h3 class="step-title">Paso 11: Articulación PEI</h3>
          <p class="field-hint">Nivel institucional: la Matriz B articula el PAD con el PEI (resultado + producto + contribución + ponderación).</p>
          <div class="form-grid">
            <div class="field">
              <label>Código Entidad</label>
              <input [(ngModel)]="form.codigo_entidad" class="form-control" placeholder="Código de la entidad">
            </div>
            <div class="field">
              <label>Entidad</label>
              <input [(ngModel)]="form.entidad" class="form-control" placeholder="Nombre de la entidad">
            </div>
            <h4 class="section-subtitle">Resultado PEI</h4>
            <div class="field">
              <label>Código Resultado PEI</label>
              <input [(ngModel)]="form.codigo_resultado_pei" class="form-control" placeholder="Ej: RPEI-01">
            </div>
            <div class="field-full">
              <label>Denominación Resultado PEI</label>
              <textarea [(ngModel)]="form.denominacion_resultado_pei" class="form-control" rows="2"
                        placeholder="Descripción del resultado PEI"></textarea>
            </div>
            <h4 class="section-subtitle">Producto PEI</h4>
            <div class="field">
              <label>Código Producto PEI</label>
              <input [(ngModel)]="form.codigo_producto_pei" class="form-control" placeholder="Ej: PPEI-01">
            </div>
            <div class="field-full">
              <label>Denominación Producto PEI</label>
              <textarea [(ngModel)]="form.denominacion_producto_pei" class="form-control" rows="2"
                        placeholder="Descripción del producto PEI"></textarea>
            </div>
            <h4 class="section-subtitle">Vinculación</h4>
            <div class="field">
              <label>Tipo de Contribución</label>
              <select [(ngModel)]="form.tipo_contribucion" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="DIRECTA">Directa</option>
                <option value="INDIRECTA">Indirecta</option>
                <option value="COMPLEMENTARIA">Complementaria</option>
              </select>
            </div>
            <div class="field">
              <label>Ponderación (%)</label>
              <input type="number" [(ngModel)]="form.ponderacion" class="form-control" min="0" max="100" placeholder="0-100">
            </div>
          </div>
        </div>

        <!-- ======= PASO 12: Revisión y Guardado ======= -->
        <div *ngIf="pasoActual === 12">
          <h3 class="step-title">Paso 12: Revisión y Guardado</h3>
          <div class="resumen-card">
            <p>Revise los datos antes de guardar. Todos los registros se crearán en una sola operación.</p>
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
              <div class="resumen-item"><strong>Resultado PAD:</strong> {{ codigoResultadoCompuesto }} — {{ form.resultado.denominacion || '—' }}</div>
              <div class="resumen-item"><strong>Producto PAD:</strong> {{ codigoProductoCompuesto }} — {{ form.producto.denominacion || '—' }}</div>
              <div class="resumen-item"><strong>Indicador Resultado:</strong> {{ form.indicador_resultado.indicador || '—' }}</div>
              <div class="resumen-item"><strong>Indicador Producto:</strong> {{ form.indicador_producto.indicador || '—' }}</div>
              <div class="resumen-item"><strong>Presupuesto Total:</strong> {{ form.presupuesto_total ? form.presupuesto_total + ' Bs.' : '—' }}</div>
              <div class="resumen-item"><strong>Resultado PEI:</strong> {{ form.codigo_resultado_pei }} — {{ form.denominacion_resultado_pei || '—' }}</div>
              <div class="resumen-item"><strong>Producto PEI:</strong> {{ form.codigo_producto_pei }} — {{ form.denominacion_producto_pei || '—' }}</div>
              <div class="resumen-item"><strong>Tipo Contribución:</strong> {{ form.tipo_contribucion || '—' }}</div>
              <div class="resumen-item"><strong>Ponderación:</strong> {{ form.ponderacion || '—' }}%</div>
            </div>
          </div>
        </div>

        <!-- Navegación -->
        <div class="form-nav">
          <button class="btn btn-outline" (click)="pasoAnterior()" [disabled]="pasoActual === 1">
            ← Anterior
          </button>
          <span class="step-counter">Paso {{ pasoActual }} de 12</span>
          <button class="btn btn-primary" (click)="pasoSiguiente()" *ngIf="pasoActual < 12">
            Siguiente →
          </button>
          <button class="btn btn-primary btn-guardar" (click)="guardarTodo()" *ngIf="pasoActual === 12" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : '💾 Guardar Articulación Completa' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .form-page { padding-bottom: 2rem; max-width: 960px; margin: 0 auto; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .stepper { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; overflow-x: auto; padding: 0.5rem 0; }
    .step { display: flex; align-items: center; gap: 0.375rem; cursor: pointer; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.6875rem; white-space: nowrap; opacity: 0.5; }
    .step.active { opacity: 1; background: #E8F5E9; }
    .step.completed { opacity: 0.8; color: var(--primary); }
    .step-circle { width: 22px; height: 22px; border-radius: 50%; background: var(--border); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.6875rem; color: var(--text-secondary); }
    .step.active .step-circle { background: var(--primary); color: white; }
    .step.completed .step-circle { background: var(--success); color: white; }
    .step-label { font-weight: 500; }

    .form-card { padding: 1.5rem; }
    .step-title { font-size: 1.125rem; color: var(--primary); margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }
    .section-subtitle { font-size: 0.875rem; color: var(--primary-dark); margin: 0.75rem 0 0.5rem; grid-column: 1 / -1; padding-top: 0.5rem; border-top: 1px solid var(--border); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field-hint { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .field { min-width: 0; }

    .codigo-readonly { background: var(--bg); font-weight: 700; color: var(--primary-dark); font-family: monospace; }

    .quinquenio-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem; }

    .resumen-card { background: var(--bg); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .resumen-card p { font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .resumen-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .resumen-item { font-size: 0.75rem; padding: 0.25rem 0; }
    .resumen-item strong { color: var(--primary-dark); }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .step-counter { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: #1B5E3B; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: #E8F5E9; color: #1B5E3B; border: 1px solid #A5D6A7; }
    .alert-danger { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
      .stepper { gap: 0; }
      .step-label { display: none; }
    }
  `],
})
export class ArticulacionFormM1Component implements OnInit {
  pasos = [
    'Planif. Nacional', 'Acuerdos Intl.', 'Planif. Sectorial', 'Contexto Territorial',
    'Lineamiento PAD', 'Resultado PAD', 'Producto PAD', 'Indicador Resultado',
    'Indicador Producto', 'Programación Fin.', 'Articulación PEI', 'Revisión / Guardar',
  ];
  pasoActual = 1;
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  quinquenio = [2026, 2027, 2028, 2029, 2030];

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
  existentesResultadosPEI: any[] = [];
  existentesProductosPEI: any[] = [];

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

  /** Código compuesto del resultado: CGEO.lineamiento.correlativo (ej: 1102.1.1). */
  get codigoResultadoCompuesto(): string {
    if (!this.form.cgeo || !this.form.lineamiento) return '';
    return `${this.form.cgeo.codigo}.${this.form.lineamiento.codigo}.${this.correlativoResultado()}`;
  }
  /** Código compuesto del producto: CGEO.lineamiento.resultado.correlativo (ej: 1102.1.1.1). */
  get codigoProductoCompuesto(): string {
    const base = this.codigoResultadoCompuesto;
    return base ? `${base}.${this.correlativoProducto()}` : '';
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
    resultado: { denominacion: '', territorializacion: '', responsable: '', cuenta_con_financiamiento: false },
    producto: { denominacion: '', territorializacion: '', responsable: '', cuenta_con_financiamiento: false },
    indicador_resultado: { indicador: '', formula: '', unidad_medida: '', linea_base: null, meta_2030: null },
    indicador_producto: { indicador: '', formula: '', unidad_medida: '', linea_base: null, meta_2030: null },
    pf_resultado: { '2026': null, '2027': null, '2028': null, '2029': null, '2030': null },
    pf_producto: { '2026': null, '2027': null, '2028': null, '2029': null, '2030': null },
    presupuesto_total: null,
    presupuesto_anual: { '2026': null, '2027': null, '2028': null, '2029': null, '2030': null },
    codigo_entidad: '',
    entidad: '',
    codigo_resultado_pei: '',
    denominacion_resultado_pei: '',
    codigo_producto_pei: '',
    denominacion_producto_pei: '',
    tipo_contribucion: '',
    ponderacion: null,
  };

  constructor(private api: ApiService, private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargarODS();
    this.cargarCatalogos();
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
    // NDC/NDT/KMGBF desde el catálogo maestro (MetaAcuerdoInternacional)
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
    // Registros existentes para correlativos de códigos compuestos y códigos PEI
    this.api.get<any>('/articulacion/resultados-pad/').subscribe({
      next: (r) => {
        this.existentesResultados = r.results || r || [];
        this.prefijarCodigosPEI();
        this.cdr.detectChanges();
      },
      error: () => { this.existentesResultados = []; },
    });
    this.api.get<any>('/articulacion/productos-pad/').subscribe({
      next: (r) => { this.existentesProductos = r.results || r || []; this.cdr.detectChanges(); },
      error: () => { this.existentesProductos = []; },
    });
    this.api.get<any>('/articulacion/resultados-pei/').subscribe({
      next: (r) => {
        this.existentesResultadosPEI = r.results || r || [];
        this.prefijarCodigosPEI();
        this.cdr.detectChanges();
      },
      error: () => { this.existentesResultadosPEI = []; },
    });
    this.api.get<any>('/articulacion/productos-pei/').subscribe({
      next: (r) => {
        this.existentesProductosPEI = r.results || r || [];
        this.prefijarCodigosPEI();
        this.cdr.detectChanges();
      },
      error: () => { this.existentesProductosPEI = []; },
    });
  }

  /** Prefija códigos PEI sugeridos (editables) a partir de los existentes. */
  private prefijarCodigosPEI(): void {
    if (!this.form.codigo_resultado_pei) {
      this.form.codigo_resultado_pei = `RPEI-${String(this.existentesResultadosPEI.length + 1).padStart(2, '0')}`;
    }
    if (!this.form.codigo_producto_pei) {
      this.form.codigo_producto_pei = `PPEI-${String(this.existentesProductosPEI.length + 1).padStart(2, '0')}`;
    }
  }

  /** Correlativo del resultado dentro del lineamiento (por catálogo y gestión). */
  correlativoResultado(): number {
    if (!this.form.lineamiento) return 1;
    const lid = this.form.lineamiento.id;
    return this.existentesResultados.filter(
      r => r.lineamiento_pad_catalogo === lid && r.vigencia_desde === 2026,
    ).length + 1;
  }

  /** Correlativo del producto dentro del resultado: resultado recién creado → 1. */
  correlativoProducto(): number {
    if (!this.form.cgeo || !this.form.lineamiento) return 1;
    return 1;
  }

  /** Cascada: al cambiar el eje se limpia componente y lineamiento */
  onEjeChange(): void {
    this.form.componente = null;
    this.form.lineamiento = null;
    this.cdr.detectChanges();
  }

  /** Cascada: al cambiar el componente se limpia el lineamiento */
  onComponenteChange(): void {
    this.form.lineamiento = null;
    this.cdr.detectChanges();
  }

  /** Al cambiar el lineamiento se refresca el código compuesto del resultado */
  onLineamientoChange(): void {
    this.cdr.detectChanges();
  }

  /** Al elegir el CGEO se pre-llena la ETA con la denominación del territorio */
  onCgeoChange(): void {
    if (this.form.cgeo) {
      this.form.eta = this.form.cgeo.denominacion;
    }
    this.cdr.detectChanges();
  }

  /** Al cambiar el sector se limpia el resultado sectorial seleccionado */
  onSectorChange(): void {
    this.form.resultado_sectorial = null;
    this.cdr.detectChanges();
  }

  private cargarODS(): void {
    this.api.get<any>('/articulacion/acuerdos/', { tipo_acuerdo: 'ODS' }).subscribe({
      next: (r) => { this.catalogoODS = r.results || r || []; this.cdr.detectChanges(); },
      error: () => {
        // Catálogo hardcodeado si falla API
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

  irAPaso(paso: number): void {
    if (paso >= 1 && paso <= 12) {
      this.pasoActual = paso;
      this.mensajeError = '';
      this.mensajeExito = '';
    }
  }

  pasoAnterior(): void {
    if (this.pasoActual > 1) {
      this.pasoActual--;
      this.mensajeError = '';
      this.mensajeExito = '';
    }
  }

  pasoSiguiente(): void {
    if (this.validarPasoActual()) {
      this.pasoActual++;
      this.mensajeError = '';
    }
  }

  private validarPasoActual(): boolean {
    this.mensajeError = '';
    if (this.pasoActual === 4) {
      if (!this.form.cgeo) {
        this.mensajeError = 'Debe seleccionar el código geográfico (CGEO).';
        return false;
      }
    }
    if (this.pasoActual === 5) {
      if (!this.form.lineamiento) {
        this.mensajeError = 'Debe seleccionar el lineamiento estratégico PAD.';
        return false;
      }
    }
    if (this.pasoActual === 6) {
      if (!this.form.resultado.denominacion) {
        this.mensajeError = 'Debe completar la denominación del Resultado PAD.';
        return false;
      }
    }
    if (this.pasoActual === 7) {
      if (!this.form.producto.denominacion) {
        this.mensajeError = 'Debe completar la denominación del Producto PAD.';
        return false;
      }
    }
    if (this.pasoActual === 8) {
      if (!this.form.indicador_resultado.indicador || !this.form.indicador_resultado.unidad_medida) {
        this.mensajeError = 'Debe completar indicador y unidad de medida del Resultado PAD.';
        return false;
      }
    }
    if (this.pasoActual === 9) {
      if (!this.form.indicador_producto.indicador || !this.form.indicador_producto.unidad_medida) {
        this.mensajeError = 'Debe completar indicador y unidad de medida del Producto PAD.';
        return false;
      }
    }
    if (this.pasoActual === 11) {
      if (!this.form.denominacion_resultado_pei || !this.form.denominacion_producto_pei) {
        this.mensajeError = 'Debe completar las denominaciones del Resultado y Producto PEI.';
        return false;
      }
    }
    return true;
  }

  private programaFisica(nivel: 'resultado' | 'producto'): Record<string, number> {
    const pf = this.form[`pf_${nivel}`] || {};
    const salida: Record<string, number> = {};
    for (const year of this.quinquenio) {
      const v = pf[year];
      if (v !== null && v !== undefined && v !== '') {
        salida[String(year)] = Number(v);
      }
    }
    return salida;
  }

  private presupuestoAnual(): Record<string, number> {
    const pa = this.form.presupuesto_anual || {};
    const salida: Record<string, number> = {};
    for (const year of this.quinquenio) {
      const v = pa[year];
      if (v !== null && v !== undefined && v !== '') {
        salida[String(year)] = Number(v);
      }
    }
    return salida;
  }

  guardarTodo(): void {
    this.guardando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    const gestion = 2026;
    const idCadena = `M1${Date.now()}${Math.floor(Math.random() * 90 + 10)}`;

    // 1. Crear Resultado PAD con todos los campos de la Matriz A/B
    const payloadResultado: any = {
      id_cadena: idCadena,
      codigo_resultado: this.codigoResultadoCompuesto,
      denominacion: this.form.resultado.denominacion,
      lineamiento_pad: this.form.lineamiento ? this.form.lineamiento.codigo : '',
      politica: this.form.politica,
      territorializacion: this.form.resultado.territorializacion,
      responsable_pad: this.form.resultado.responsable,
      cuenta_con_financiamiento: !!this.form.resultado.cuenta_con_financiamiento,
      vigencia_desde: gestion,
      vigencia_hasta: 2030,
      cod_geografico: this.form.cgeo ? this.form.cgeo.codigo : '',
      eta: this.form.eta,
      resultado_sectorial_catalogo: this.form.resultado_sectorial ? this.form.resultado_sectorial.id : null,
      entidad_territorial_cgeo: this.form.cgeo ? this.form.cgeo.id : null,
      lineamiento_pad_catalogo: this.form.lineamiento ? this.form.lineamiento.id : null,
      acuerdo_ods: this.form.ods ? [this.form.ods.id] : [],
      acuerdo_ndc: this.form.ndc ? [this.form.ndc.id] : [],
      acuerdo_ndt: this.form.ndt ? [this.form.ndt.id] : [],
      acuerdo_kmgbf: this.form.kmgbf ? [this.form.kmgbf.id] : [],
      cod_eje_pgdesa: this.form.eje ? this.form.eje.codigo : '',
      objetivo_impacto: this.form.objetivo_impacto,
      cod_componente_pdesa: this.form.componente ? this.form.componente.codigo : '',
      objetivo_efecto: this.form.objetivo_efecto,
      cod_sector: this.form.sector ? this.form.sector.codigo : '',
      sector: this.form.sector ? this.form.sector.denominacion : '',
      cod_resultado_pds: this.form.resultado_sectorial ? this.form.resultado_sectorial.codigo : '',
      resultado_pds: this.form.resultado_sectorial ? this.form.resultado_sectorial.denominacion : '',
      estado: 'REFERENCIAL',
    };

    this.api.post<any>('/articulacion/resultados-pad/', payloadResultado).subscribe({
      next: (resPad) => {
        const resultadoPadId = resPad.id || resPad;
        const correlativoProductoReal = this.existentesProductos.filter(
          p => p.resultado_pad === resultadoPadId,
        ).length + 1;

        // 2. Crear Producto PAD vinculado
        this.api.post<any>('/articulacion/productos-pad/', {
          codigo_producto: `${this.codigoResultadoCompuesto}.${correlativoProductoReal}`,
          denominacion: this.form.producto.denominacion,
          resultado_pad: resultadoPadId,
          territorializacion: this.form.producto.territorializacion,
          responsable: this.form.producto.responsable,
          cuenta_con_financiamiento: !!this.form.producto.cuenta_con_financiamiento,
        }).subscribe({
          next: (prodPad) => {
            const productoPadId = prodPad.id || prodPad;

            // 3. Indicador a nivel de RESULTADO PAD
            const payloadIndicadorResultado: any = {
              nivel_indicador: 'RESULTADO_PAD',
              resultado_pad: resultadoPadId,
              indicador: this.form.indicador_resultado.indicador,
              formula: this.form.indicador_resultado.formula,
              unidad_medida: this.form.indicador_resultado.unidad_medida,
              linea_base: this.form.indicador_resultado.linea_base,
              meta_2030: this.form.indicador_resultado.meta_2030,
              programacion_fisica: this.programaFisica('resultado'),
            };
            this.api.post<any>('/articulacion/indicadores/', payloadIndicadorResultado).subscribe({
              next: () => {
                // 4. Indicador a nivel de PRODUCTO PAD (+ programación financiera)
                const payloadIndicadorProducto: any = {
                  nivel_indicador: 'PRODUCTO_PAD',
                  producto_pad: productoPadId,
                  indicador: this.form.indicador_producto.indicador,
                  formula: this.form.indicador_producto.formula,
                  unidad_medida: this.form.indicador_producto.unidad_medida,
                  linea_base: this.form.indicador_producto.linea_base,
                  meta_2030: this.form.indicador_producto.meta_2030,
                  programacion_fisica: this.programaFisica('producto'),
                  presupuesto_total: this.form.presupuesto_total,
                  presupuesto_anual: this.presupuestoAnual(),
                };
                this.api.post<any>('/articulacion/indicadores/', payloadIndicadorProducto).subscribe({
                  next: () => { this.crearBloquePEI(productoPadId); },
                  error: (err) => { this.onError(err, 'Error al crear el indicador del producto'); },
                });
              },
              error: (err) => { this.onError(err, 'Error al crear el indicador del resultado'); },
            });
          },
          error: (err) => { this.onError(err, 'Error al crear el producto PAD'); },
        });
      },
      error: (err) => { this.onError(err, 'Error al crear el resultado PAD'); },
    });
  }

  /** Crea Resultado PEI → Producto PEI → Articulación PAD-PEI. */
  private crearBloquePEI(productoPadId: string): void {
    // 5. Crear Resultado PEI
    this.api.post<any>('/articulacion/resultados-pei/', {
      codigo_resultado: this.form.codigo_resultado_pei,
      denominacion: this.form.denominacion_resultado_pei,
      cod_entidad: this.form.codigo_entidad,
      entidad: this.form.entidad || this.form.codigo_entidad,
      vigencia_desde: 2026,
      vigencia_hasta: 2030,
    }).subscribe({
      next: (resPei) => {
        const resultadoPeiId = resPei.id || resPei;

        // 6. Crear Producto PEI vinculado
        this.api.post<any>('/articulacion/productos-pei/', {
          codigo_producto: this.form.codigo_producto_pei,
          denominacion: this.form.denominacion_producto_pei,
          resultado_pei: resultadoPeiId,
        }).subscribe({
          next: (prodPei) => {
            const productoPeiId = prodPei.id || prodPei;

            // 7. Crear Articulación PAD→PEI
            this.api.post<any>('/articulacion/articulaciones-pad-pei/', {
              producto_pad: productoPadId,
              producto_pei: productoPeiId,
              tipo_contribucion: this.form.tipo_contribucion,
              ponderacion: this.form.ponderacion,
              estado: 'REFERENCIAL',
            }).subscribe({
              next: () => {
                this.mensajeExito = '✅ Articulación PAD→PEI creada exitosamente. Redirigiendo...';
                this.guardando = false;
                this.cdr.detectChanges();
                setTimeout(() => this.router.navigate(['/articulacion/pad-pei']), 2000);
              },
              error: (err) => { this.onError(err, 'Error al crear la articulación'); },
            });
          },
          error: (err) => { this.onError(err, 'Error al crear el producto PEI'); },
        });
      },
      error: (err) => { this.onError(err, 'Error al crear el resultado PEI'); },
    });
  }

  private onError(err: any, msg: string): void {
    console.error(msg, err);
    this.mensajeError = `❌ ${msg}. Verifique los datos e intente nuevamente.`;
    this.guardando = false;
    this.cdr.detectChanges();
  }
}
