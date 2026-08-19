import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { concatMap, from, of, switchMap, toArray } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { MatricesPadService } from '../matrices-pad.service';
import {
  AcuerdoInternacionalOption,
  CompatibilidadAcuerdo,
  CompatibilidadesAcuerdosService,
  TipoAcuerdo,
  TipoRelacion,
} from './compatibilidades-acuerdos.service';
import {
  ACCIONES_DE_CAMBIO_PAD,
  CATALOGO_ODS,
  ComponentePdesa,
  EJES_PGDESA,
  EjePgdesa,
  GESTIONES_PAD,
} from './pad-catalogos';
import {
  CabeceraPad,
  FilaMatrizA,
  FilaMatrizB,
  Hallazgo,
  ProductoPadForm,
  ResultadoPadForm,
  cabeceraVacia,
  codigoProducto,
  codigoResultado,
  construirMatrizA,
  construirMatrizB,
  consolidarPresupuesto,
  productoVacio,
  redactarResultado,
  resultadoVacio,
  sumarProgramacion,
  tieneErrores,
  validarMatrices,
} from './pad-matriz.model';

type CodigoAcuerdo = string | string[];

interface OpcionAcuerdoFiltrada extends AcuerdoInternacionalOption {
  compatibilidad?: CompatibilidadAcuerdo;
  seleccionGuardada?: boolean;
}

/**
 * Asistente de construcción de las Matrices de Planificación PAD 2026-2030.
 *
 * Sigue la secuencia de la Guía PAD (§4): visión → política → lineamiento
 * estratégico → resultados territoriales → productos, proyectando cada paso
 * sobre el visualizador de matrices, con la misma mecánica del asistente PEI.
 */
@Component({
  selector: 'app-pad-wizard',
  standalone: false,
  template: `
    <div class="pad-full">
      <div class="pad-header">
        <div class="migas">
          <a routerLink="/matrices-pad">Matrices PAD</a>
          <span>›</span>
          <span>{{ modoEdicion ? 'Editar registro' : 'Registro nuevo' }}</span>
        </div>
        <h1>MATRICES PAD 2026-2030 — GUÍA METODOLÓGICA OFICIAL</h1>
        <div class="aviso-edicion" *ngIf="modoEdicion">
          <strong>Editando un registro existente.</strong>
          Los cambios se guardan sobre el mismo borrador al confirmar el registro.
          <span *ngIf="cargandoBorrador"> Cargando datos…</span>
        </div>
        <p>
          Construcción por bloques: PGDESA → PDESA → Acuerdos → Sector →
          Política → Lineamiento → Resultados territoriales → Productos
        </p>
      </div>

      <div class="progress-bar-horizontal">
        <div *ngFor="let nv of pasos; let i = index" class="progress-step"
             [class.completed]="paso > i" [class.active]="paso === i" (click)="irAPaso(i)">
          <div class="step-circle">{{ paso > i ? '✓' : i + 1 }}</div>
          <div class="step-label">{{ nv }}</div>
        </div>
      </div>

      <div class="wizard-layout">
        <div class="wizard-main">

      <!-- PASO 0: PLANIFICACIÓN NACIONAL -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Matriz B — Planificación nacional</h3>
        <p>Seleccione el eje del PGDESA (objetivo de impacto) y su componente PDESA (objetivo de efecto).</p>
        <div class="select-cards">
          <div *ngFor="let eje of ejes" class="select-card"
               [class.selected]="cabecera.codEjePgdesa === eje.codigo" (click)="selEje(eje)">
            <div class="card-cod">Eje {{ eje.codigo }}</div>
            <div class="card-nombre">{{ eje.titulo }}</div>
          </div>
        </div>
        <div class="field" *ngIf="ejeActual">
          <label>Objetivo de impacto PGDESA</label>
          <textarea [(ngModel)]="cabecera.objetivoImpacto" class="form-control" rows="3"></textarea>
        </div>
        <h4 *ngIf="ejeActual">Componente PDESA</h4>
        <div class="select-cards" *ngIf="ejeActual">
          <div *ngFor="let c of ejeActual.componentes" class="select-card"
               [class.selected]="cabecera.codComponentePdesa === c.codigo" (click)="selComponente(c)">
            <div class="card-cod">{{ c.codigo }}</div>
            <div class="card-desc">{{ c.objetivoEfecto | slice:0:120 }}…</div>
          </div>
        </div>
        <div class="field" *ngIf="cabecera.codComponentePdesa">
          <label>Objetivo de efecto PDESA</label>
          <textarea [(ngModel)]="cabecera.objetivoEfecto" class="form-control" rows="3"></textarea>
        </div>
        <div class="step-nav">
          <span></span>
          <button class="btn btn-primary" [disabled]="!cabecera.codComponentePdesa" (click)="paso = 1">
            Siguiente → Acuerdos
          </button>
        </div>
      </div>

      <!-- PASO 1: ACUERDOS INTERNACIONALES -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Matriz B — Acuerdos internacionales</h3>
        <p>
          17 ODS, 35 metas NDC y 19 principios NDT. Registre solo los que tengan relación
          directa con el resultado; si no aplica, deje <strong>N/A</strong>.
        </p>
        <div class="form-2col">
          <div class="field"><label>Código ODS</label>
           <select [(ngModel)]="cabecera.codOds" (ngModelChange)="onOdsChange()" class="form-control">
              <option value="">Sin vinculación</option>
              <option *ngFor="let o of catalogoOds" [value]="o.codigo">
                {{ o.codigo }} — {{ o.denominacion | slice:0:90 }}
              </option>
            </select>
          </div>
          <div class="field"><label>Código meta NDC</label>
           <select [(ngModel)]="cabecera.codNdc" (ngModelChange)="onNdcChange()" class="form-control">
             <option value="N/A">N/A — no aplica</option>
             <option *ngFor="let n of catalogoNdc" [value]="n.codigo">
                 {{ n.codigo }} — {{ n.denominacion | slice:0:90 }} · {{ etiquetaCompatibilidad(n) }}
             </option>
            </select>
          </div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código principio NDT</label>
           <select [(ngModel)]="cabecera.codNdt" (ngModelChange)="onNdtChange()" class="form-control">
             <option value="N/A">N/A — no aplica</option>
             <option *ngFor="let n of catalogoNdt" [value]="n.codigo">
                 {{ n.codigo }} — {{ n.denominacion | slice:0:90 }} · {{ etiquetaCompatibilidad(n) }}
             </option>
            </select>
          </div>
           <div class="field"><label>KMGBF/30x30 (según target)</label>
             <select [(ngModel)]="cabecera.compromiso3030" (ngModelChange)="onKmgbfChange()" class="form-control">
               <option value="N/A">N/A — no aplica</option>
               <option *ngFor="let c of catalogo3030" [value]="c.codigo">
                 {{ c.codigo }} — {{ c.denominacion | slice:0:90 }} · {{ etiquetaCompatibilidad(c) }}
               </option>
             </select>
           </div>
         </div>
         <div class="nota cascada-aviso" *ngIf="mensajeCascada('NDC')">
           {{ mensajeCascada('NDC') }}
         </div>
         <div class="nota cascada-aviso" *ngIf="mensajeCascada('NDT')">
           {{ mensajeCascada('NDT') }}
         </div>
         <div class="nota cascada-aviso" *ngIf="mensajeCascada('COMPROMISO_3030')">
           {{ mensajeCascada('COMPROMISO_3030') }}
         </div>
         <div class="nota" *ngIf="!acuerdos.length">
          El catálogo de acuerdos internacionales no está disponible; los códigos quedarán
          sin validar contra el maestro.
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 0">← Anterior</button>
          <button class="btn btn-primary" (click)="paso = 2">Siguiente → Sector</button>
        </div>
      </div>

      <!-- PASO 2: PLANIFICACIÓN SECTORIAL -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Matriz B — Planificación sectorial</h3>
        <div class="form-2col">
          <div class="field"><label>Código de sector</label>
            <select [(ngModel)]="cabecera.codSector" class="form-control" (change)="onSectorChange()">
              <option value="">Seleccione...</option>
              <option *ngFor="let s of sectores" [value]="s.codigo">{{ s.codigo }} — {{ s.nombre }}</option>
            </select>
          </div>
          <div class="field"><label>Sector</label>
            <input [(ngModel)]="cabecera.sector" class="form-control" placeholder="Ej: Saneamiento Básico"></div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código resultado sectorial (PDS)</label>
            <input [(ngModel)]="cabecera.codResultadoSectorial" class="form-control" placeholder="Ej: 5.1"></div>
          <div class="field"><label>Resultado sectorial</label>
            <textarea [(ngModel)]="cabecera.resultadoSectorial" class="form-control" rows="2"
                      placeholder="Ej: Se ha incrementado la cobertura de agua potable"></textarea>
          </div>
        </div>
        <div class="nota">
          Si el PDS no define un resultado que corresponda al resultado PAD, consigne el
          código del sector seguido de <strong>"0"</strong>.
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 1">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!cabecera.codSector" (click)="paso = 3">
            Siguiente → Política
          </button>
        </div>
      </div>

      <!-- PASO 3: POLÍTICA Y LINEAMIENTO -->
      <div *ngIf="paso === 3" class="step-content card">
        <h3>Paso 4: Matriz A — Política y lineamiento estratégico</h3>
        <p>
          La política es un texto corto que define ámbitos de intervención. El lineamiento
          responde a <strong>¿qué se quiere lograr?</strong> y es el primer elemento de la
          matriz: a partir de él se organizan resultados y productos.
        </p>
        <div class="entidad-fija">
          <h4>Entidad territorial</h4>
          <div class="form-3col">
            <div class="field"><label>Código geográfico (clasificador presupuestario)</label>
              <input [(ngModel)]="cabecera.codGeografico" class="form-control"></div>
            <div class="field"><label>Denominación de la ETA</label>
              <input [(ngModel)]="cabecera.eta" class="form-control"></div>
            <div class="field"><label>Quinquenio</label>
              <input value="2026 - 2030" class="form-control derivada" readonly></div>
          </div>
          <small>
            Precargado del clasificador geográfico: 351 corresponde a Sacaba
            (departamento 3, provincia 5, municipio 1), escrito corrido como en el
            ejemplo del Ministerio. Ajustable si formula para otra ETA.
          </small>
        </div>

        <div class="field">
          <label>Política</label>
          <input [(ngModel)]="cabecera.politica" class="form-control"
                 placeholder="Texto corto que define el ámbito o tema de intervención">
          <small>
            La política organiza la propuesta estratégica de la entidad y surge de su
            diagnóstico y su visión (§4.2).
          </small>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código del lineamiento estratégico</label>
            <input [ngModel]="cabecera.codLineamiento" class="form-control derivada" readonly
                   placeholder="se asigna solo">
            <small>Correlativo asignado automáticamente por la entidad.</small>
          </div>
          <div class="field"><label>Lineamiento del catálogo (opcional)</label>
            <select [(ngModel)]="cabecera.lineamientoId" class="form-control" (change)="onLineamientoCatalogo()">
              <option [ngValue]="null">Captura manual</option>
              <option *ngFor="let l of lineamientos" [ngValue]="l.id">
                {{ l.codigo }} — {{ (l.denominacion || '') | slice:0:60 }}
              </option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>Lineamiento estratégico</label>
          <textarea [(ngModel)]="cabecera.lineamiento" class="form-control" rows="3"
                    placeholder="Ej: Promover la reactivación económica del municipio, mediante el fortalecimiento de los procesos productivos locales…"></textarea>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 2">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!cabecera.codLineamiento" (click)="paso = 4">
            Siguiente → Resultados
          </button>
        </div>
      </div>

      <!-- PASO 4: RESULTADOS Y PRODUCTOS -->
      <div *ngIf="paso === 4" class="step-content card">
        <h3>Paso 5: Resultados territoriales y sus productos</h3>
        <p>
          El resultado se redacta en tiempo pretérito y se mide con un indicador; los
          productos son las intervenciones concretas que lo hacen realidad.
        </p>
        <div class="inline-actions">
          <button class="btn btn-accent btn-sm" (click)="agregarResultado()">+ Agregar resultado</button>
        </div>

        <div class="resultado-card" *ngFor="let r of resultados; let i = index">
          <div class="resultado-head">
            <span class="codigo">{{ codigoDeResultado(i) }}</span>
            <span class="resultado-nombre">{{ nombreDeResultado(r) || 'Resultado sin redactar' }}</span>
            <button class="btn btn-sm btn-danger" (click)="quitarResultado(i)">Quitar</button>
          </div>

          <div class="form-2col">
            <div class="field"><label>Acción de cambio (tiempo pretérito)</label>
              <select [(ngModel)]="r.accionCambio" class="form-control">
                <option value="">Seleccione...</option>
                <option *ngFor="let a of acciones" [value]="a">{{ a }}</option>
              </select>
            </div>
            <div class="field"><label>Variable del resultado</label>
              <input [(ngModel)]="r.variableResultado" class="form-control"
                     placeholder="la cobertura del servicio de agua potable en el municipio"></div>
          </div>
          <div class="form-2col">
            <div class="field"><label>Territorialización</label>
              <input [(ngModel)]="r.territorializacion" class="form-control"
                     placeholder="Unidad de planificación, distrito, comunidad…"></div>
            <div class="field"><label>Responsable (entidad)</label>
              <input [(ngModel)]="r.responsable" class="form-control"
                     placeholder="Gobierno Autónomo Municipal de…"></div>
          </div>

          <h5>Indicador del resultado</h5>
          <div class="field"><label>Indicador</label>
            <input [(ngModel)]="r.indicador.indicador" class="form-control"
                   placeholder="Ej: Tasa de cobertura del servicio de agua potable"></div>
          <div class="form-3col">
            <div class="field"><label>Fórmula</label>
              <input [(ngModel)]="r.indicador.formula" class="form-control"
                     placeholder="(Valor alcanzado / Meta programada) × 100"></div>
            <div class="field"><label>Unidad de medida</label>
              <input [(ngModel)]="r.indicador.unidadMedida" class="form-control" placeholder="% / Número"></div>
            <div class="field"><label>Año de la línea base</label>
              <input [(ngModel)]="r.indicador.anioLineaBase" type="number" class="form-control"></div>
          </div>
          <div class="form-2col">
            <div class="field"><label>Línea base</label>
              <input [(ngModel)]="r.indicador.lineaBase" type="number" class="form-control"></div>
            <div class="field"><label>Meta 2030</label>
              <input [(ngModel)]="r.indicador.meta2030" type="number" class="form-control"></div>
          </div>

          <h5>Programación física del resultado</h5>
          <div class="prog-grid">
            <div *ngFor="let anio of gestiones" class="field">
              <label>{{ anio }}</label>
              <input [(ngModel)]="r.fisica[anio]" type="number" class="form-control">
            </div>
          </div>

          <div class="productos-zona">
            <div class="inline-actions">
              <strong class="mini-titulo">Productos territoriales</strong>
              <button class="btn btn-accent btn-sm" (click)="agregarProducto(r)">+ Agregar producto</button>
            </div>

            <div class="producto-card" *ngFor="let p of r.productos; let j = index">
              <div class="producto-head">
                <span class="codigo">{{ codigoDeProducto(i, j) }}</span>
                <span class="producto-nombre">{{ p.denominacion || 'Producto sin denominar' }}</span>
                <button class="btn btn-sm btn-danger" (click)="quitarProducto(r, j)">Quitar</button>
              </div>
              <div class="field"><label>Producto (proyecto o programa)</label>
                <input [(ngModel)]="p.denominacion" class="form-control"
                       placeholder="Ej: Construcción de sistemas de agua potable"></div>
              <div class="form-3col">
                <div class="field"><label>Territorialización</label>
                  <input [(ngModel)]="p.territorializacion" class="form-control"
                         placeholder="Comunidad, distrito, unidad de planificación"></div>
                <div class="field"><label>Responsable</label>
                  <input [(ngModel)]="p.responsable" class="form-control"></div>
                <div class="field"><label>¿Cuenta con financiamiento?</label>
                  <select [(ngModel)]="p.cuentaConFinanciamiento" class="form-control">
                    <option [ngValue]="true">SÍ</option>
                    <option [ngValue]="false">NO</option>
                  </select>
                </div>
              </div>
              <div class="field"><label>Indicador del producto</label>
                <input [(ngModel)]="p.indicador.indicador" class="form-control"
                       placeholder="Ej: Número de sistemas de agua potable implementados"></div>
              <div class="form-3col">
                <div class="field"><label>Fórmula</label>
                  <input [(ngModel)]="p.indicador.formula" class="form-control" placeholder="N/A"></div>
                <div class="field"><label>Línea base</label>
                  <input [(ngModel)]="p.indicador.lineaBase" type="number" class="form-control"></div>
                <div class="field"><label>Meta 2030</label>
                  <input [(ngModel)]="p.indicador.meta2030" type="number" class="form-control"></div>
              </div>

              <h6>Programación física por gestión</h6>
              <div class="prog-grid">
                <div *ngFor="let anio of gestiones" class="field">
                  <label>{{ anio }}</label>
                  <input [(ngModel)]="p.fisica[anio]" type="number" class="form-control">
                </div>
              </div>

              <h6>Programación financiera (Bs., sin decimales)</h6>
              <div class="prog-grid">
                <div *ngFor="let anio of gestiones" class="field">
                  <label>{{ anio }}</label>
                  <input [(ngModel)]="p.presupuesto[anio]" type="number" class="form-control">
                </div>
              </div>
              <div class="producto-totales">
                <span>Presupuesto del producto: <strong>{{ moneda(totalProducto(p)) }} Bs.</strong></span>
              </div>
            </div>
          </div>

          <div class="resultado-totales">
            Presupuesto del resultado (suma de sus productos):
            <strong>{{ moneda(totalResultado(r)) }} Bs.</strong>
          </div>
        </div>

        <div class="vacio-resultados" *ngIf="!resultados.length">
          Sin resultados no hay matriz: agregue al menos uno.
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 3">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!resultados.length" (click)="paso = 5">
            Siguiente → Revisión
          </button>
        </div>
      </div>

      <!-- PASO 5: REVISIÓN Y REGISTRO -->
      <div *ngIf="paso === 5" class="step-content card">
        <h3>Paso 6: Revisión y registro del PAD</h3>
        <div class="resumen-grid">
          <div class="resumen-item"><span>ETA</span><strong>{{ cabecera.codGeografico }} — {{ cabecera.eta || '-' }}</strong></div>
          <div class="resumen-item"><span>Lineamiento</span><strong>{{ cabecera.codLineamiento || '-' }}</strong></div>
          <div class="resumen-item"><span>Resultados</span><strong>{{ resultados.length }}</strong></div>
          <div class="resumen-item"><span>Productos</span><strong>{{ totalProductos }}</strong></div>
          <div class="resumen-item"><span>Presupuesto quinquenal</span><strong>{{ moneda(presupuestoQuinquenal) }} Bs.</strong></div>
        </div>

        <div class="hallazgos" *ngIf="hallazgos.length">
          <h4>Observaciones metodológicas</h4>
          <ul>
            <li *ngFor="let h of hallazgos" [class.error]="h.severidad === 'error'"
                [class.aviso]="h.severidad === 'aviso'">
              <strong>{{ h.seccion }}:</strong> {{ h.mensaje }}
            </li>
          </ul>
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 4">← Anterior</button>
          <button class="btn btn-success" [disabled]="bloqueado || guardando" (click)="guardar()">
            {{ guardando ? 'Registrando…' : '✓ Registrar matrices PAD' }}
          </button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass === 'error'"
             [class.exito]="msgClass === 'exito'">{{ msg }}</div>
      </div>

        </div>

        <app-control-metodologico [hallazgos]="hallazgos"
                                  fuente="Guía Metodológica PAD 2026-2030">
        </app-control-metodologico>
      </div>

      <app-pad-matriz-viewer [filasA]="filasA" [filasB]="filasB" [hallazgos]="hallazgos">
      </app-pad-matriz-viewer>
    </div>
  `,
  styles: [`
    .pad-full { max-width: var(--ancho-trabajo); margin: 0 auto; padding-bottom: 2rem; }
    .migas { font-size: 0.6875rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: flex; gap: 0.4rem; align-items: center; }
    .migas a { color: var(--primary); text-decoration: none; font-weight: 600; }
    .migas a:hover { text-decoration: underline; }
    .aviso-edicion { margin: 0.5rem 0 0; padding: 0.55rem 0.75rem; background: var(--aviso-fondo); color: var(--aviso-tinta); border-radius: 6px; font-size: 0.75rem; }
    .pad-header h1 { font-size: 1.35rem; color: var(--primary); }
    .pad-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1rem; }

    .progress-bar-horizontal { display: flex; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
    .progress-step { flex: 1; text-align: center; padding: 0.5rem 0.25rem; cursor: pointer; position: relative; min-width: 70px; }
    .progress-step::after { content: ''; position: absolute; top: 50%; right: -50%; width: 100%; height: 2px; background: var(--border); z-index: 0; }
    .progress-step:last-child::after { display: none; }
    .step-circle { width: 28px; height: 28px; border-radius: 50%; margin: 0 auto 0.25rem; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; background: var(--border); color: var(--text-secondary); position: relative; z-index: 1; }
    .progress-step.active .step-circle { background: var(--primary); color: #fff; }
    .progress-step.completed .step-circle { background: var(--success); color: #fff; }
    .step-label { font-weight: 700; font-size: 0.6875rem; }

    .wizard-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 1.25rem; align-items: start; }
    app-control-metodologico { position: sticky; top: var(--e-2); align-self: start; max-height: calc(100vh - 5rem); overflow-y: auto; }
    .wizard-main { min-width: 0; }
    @media (max-width: 1100px) { .wizard-layout { grid-template-columns: 1fr; } }

    .step-content { padding: 1.5rem; min-height: 300px; }
    .step-content h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
    .step-content h4 { font-size: 0.9rem; margin: 1rem 0 0.5rem; color: var(--text-secondary); }
    .step-content h5 { font-size: 0.8125rem; margin: 0.75rem 0 0.4rem; color: var(--primary); }
    .step-content h6 { font-size: 0.75rem; margin: 0.6rem 0 0.3rem; color: var(--text-secondary); }
    .step-content p { color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 0.8125rem; }
    .step-content code { background: var(--border); padding: 0 0.25rem; border-radius: 3px; font-size: 0.75rem; }

    .select-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem; }
    .select-card { padding: 0.75rem; border: 2px solid var(--border); border-radius: 6px; cursor: pointer; }
    .select-card:hover { border-color: var(--primary); background: var(--realce); }
    .select-card.selected { border-color: var(--primary); background: var(--ok-fondo); }
    .card-cod { font-weight: 800; font-size: 0.7rem; color: var(--primary); }
    .card-nombre { font-size: 0.8125rem; font-weight: 600; }
    .card-desc { font-size: 0.6875rem; color: var(--text-secondary); margin-top: 0.25rem; }

    .form-2col, .form-3col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; }
    .form-2col { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .form-3col { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
    .field { margin-bottom: 0.5rem; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.2rem; }
    .inline-actions { margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.75rem; }
    .mini-titulo { font-size: 0.8125rem; color: var(--primary); }
    .step-nav { display: flex; justify-content: space-between; margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }

    .entidad-fija { padding: 0.85rem; border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 6px; background: #F7FBF8; margin-bottom: 1rem; }
    .entidad-fija h4 { margin: 0 0 0.5rem; }
    .entidad-fija small { font-size: 0.625rem; color: var(--text-secondary); }
    .derivada { background: #F3F7F4; font-weight: 700; }

    .prog-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; }
    .prog-grid input { font-size: 0.75rem; padding: 0.25rem 0.375rem; }

    .resultado-card { border: 2px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem; }
    .resultado-head, .producto-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .resultado-head .codigo, .producto-head .codigo { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); }
    .resultado-nombre, .producto-nombre { flex: 1; font-size: 0.8125rem; font-weight: 600; }
    .resultado-totales { margin-top: 0.75rem; padding-top: 0.5rem; border-top: 2px solid var(--border); font-size: 0.8125rem; }
    .productos-zona { margin-top: 1rem; padding-left: 1rem; border-left: 3px solid var(--primary); }
    .producto-card { border: 1px dashed var(--border); border-radius: 6px; padding: 0.75rem; margin-bottom: 0.75rem; }
    .producto-totales { margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary); }
    .vacio-resultados { padding: 1.5rem; text-align: center; color: var(--text-secondary); font-size: 0.8125rem; border: 1px dashed var(--border); border-radius: 8px; }

    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .resumen-item { padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
    .resumen-item span { display: block; font-size: 0.6875rem; color: var(--text-secondary); }
    .resumen-item strong { font-size: 0.8125rem; }

    .hallazgos ul { list-style: none; padding: 0; margin: 0; }
    .hallazgos li { padding: 0.4rem 0.6rem; border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.75rem; }
    .hallazgos li.error { background: var(--error-fondo); color: var(--warn); }
    .hallazgos li.aviso { background: var(--aviso-fondo); color: var(--aviso-tinta); }

     .nota { margin-top: 0.75rem; padding: 0.6rem 0.75rem; background: var(--aviso-fondo); color: var(--aviso-tinta); border-radius: 6px; font-size: 0.75rem; }
     .cascada-aviso { border-left: 3px solid var(--primary); }
    .msg-box { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .msg-box.error { background: var(--error-fondo); color: var(--warn); }
    .msg-box.exito { background: var(--ok-fondo); color: var(--success); }
    .btn-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); border-radius: 4px; cursor: pointer; padding: 0.2rem 0.5rem; font-size: 0.6875rem; }

    @media (max-width: 768px) {
      .form-2col, .form-3col, .prog-grid { grid-template-columns: 1fr; }
    }
  `],
})
export class PadWizardComponent implements OnInit {
  paso = 0;
  pasos = ['Nacional', 'Acuerdos', 'Sector', 'Lineamiento', 'Resultados', 'Registro'];

  gestiones = GESTIONES_PAD;
  ejes = EJES_PGDESA;
  ods = CATALOGO_ODS;
  acciones = ACCIONES_DE_CAMBIO_PAD;

  gestion = 2026;
  cabecera: CabeceraPad = cabeceraVacia();
  resultados: ResultadoPadForm[] = [resultadoVacio()];

  sectores: any[] = [];
  lineamientos: any[] = [];
  /** Correlativo calculado para un lineamiento nuevo. */
  codigoAsignado = '1';
  acuerdos: AcuerdoInternacionalOption[] = [];
  opcionesNdc: OpcionAcuerdoFiltrada[] = [];
  opcionesNdt: OpcionAcuerdoFiltrada[] = [];
  opcionesKmgbf: OpcionAcuerdoFiltrada[] = [];
  cargandoCompatibilidades: Record<TipoAcuerdo, boolean> = {
    ODS: false,
    NDC: false,
    NDT: false,
    COMPROMISO_3030: false,
  };
  private preservarSeleccionesGuardadas = false;

  guardando = false;
  msg = '';
  msgClass = '';

  /** Borrador en edición; vacío cuando es un registro nuevo. */
  borradorId: string | null = null;
  cargandoBorrador = false;

  constructor(
    private api: ApiService,
    private matrices: MatricesPadService,
    private ruta: ActivatedRoute,
    private cdr: ChangeDetectorRef,
    private compatibilidades: CompatibilidadesAcuerdosService,
  ) {}

  ngOnInit(): void {
    this.cargarSectores();
    this.cargarLineamientos();
    this.cargarAcuerdos();

    const id = this.ruta.snapshot.paramMap.get('id');
    if (id) {
      this.borradorId = id;
      this.cargarBorrador(id);
    }
  }

  get modoEdicion(): boolean {
    return !!this.borradorId;
  }

  /** Rehidrata el asistente con las secciones guardadas del borrador. */
  private cargarBorrador(id: string): void {
    this.cargandoBorrador = true;
    this.matrices.obtener(id).subscribe({
      next: (borrador: any) => {
        const datos = borrador?.datos || {};
        this.gestion = borrador?.gestion || this.gestion;

        const nacional = datos.p1_nacional || {};
        this.cabecera.codEjePgdesa = nacional?.eje?.codigo || '';
        this.cabecera.objetivoImpacto = nacional.objetivo_impacto || '';
        this.cabecera.codComponentePdesa = nacional?.componente?.codigo || '';
        this.cabecera.objetivoEfecto = nacional.objetivo_efecto || '';

        const acuerdos = datos.p2_acuerdos || {};
        this.cabecera.codOds = this.codigoAcuerdo(acuerdos.ods);
        this.cabecera.codNdc = this.codigoAcuerdo(acuerdos.ndc) || 'N/A';
        this.cabecera.codNdt = this.codigoAcuerdo(acuerdos.ndt) || 'N/A';
        this.cabecera.compromiso3030 = this.codigoAcuerdo(acuerdos.kmgbf) || 'N/A';

        const sectorial = datos.p3_sectorial || {};
        this.cabecera.codSector = sectorial?.sector?.codigo || '';
        this.cabecera.sector = sectorial?.sector?.denominacion || '';
        this.cabecera.codResultadoSectorial = sectorial?.resultado_sectorial?.codigo || '';
        this.cabecera.resultadoSectorial = sectorial?.resultado_sectorial?.denominacion || '';

        const territorial = datos.p4_territorial || {};
        this.cabecera.codGeografico = territorial?.cgeo?.codigo || this.cabecera.codGeografico;
        this.cabecera.eta = territorial.eta || this.cabecera.eta;
        this.cabecera.politica = territorial.politica || '';

        const lineamiento = (datos.p5_lineamiento || {}).lineamiento || {};
        this.cabecera.lineamientoId = lineamiento.id || null;
        this.cabecera.codLineamiento = lineamiento.codigo || this.cabecera.codLineamiento;
        this.cabecera.lineamiento = lineamiento.denominacion || '';

        const resultados = Array.isArray(datos.resultados) ? datos.resultados : [];
        if (resultados.length) {
          this.resultados = resultados.map((r: any) => this.hidratarResultado(r));
        }

        this.cargandoBorrador = false;
        if (this.acuerdos.length) this.inicializarCascada();
        this.cdr.markForCheck();
      },
      error: () => {
        this.cargandoBorrador = false;
        this.msg = '❌ No se pudo cargar el registro solicitado.';
        this.msgClass = 'error';
        this.cdr.markForCheck();
      },
    });
  }

  private codigoAcuerdo(valor: any): string {
    if (!valor || valor === 'N/A') return '';
    return typeof valor === 'string' ? valor : (valor.codigo || '');
  }

  private hidratarProgramacion(origen: any): Record<string, number | null> {
    const destino: Record<string, number | null> = {};
    for (const anio of this.gestiones) {
      const valor = (origen || {})[anio];
      destino[anio] = valor === undefined || valor === null ? null : Number(valor);
    }
    return destino;
  }

  private hidratarIndicador(origen: any): any {
    const indicador = origen || {};
    return {
      indicador: indicador.indicador || '',
      formula: indicador.formula || 'N/A',
      unidadMedida: indicador.unidad_medida || '',
      lineaBase: indicador.linea_base ?? null,
      anioLineaBase: indicador.anio_linea_base ?? 2025,
      meta2030: indicador.meta_2030 ?? null,
    };
  }

  private hidratarResultado(origen: any): any {
    const denominacion = String(origen?.denominacion || '');
    const accion = this.acciones.find(a => denominacion.startsWith(a)) || '';
    return {
      accionCambio: accion,
      variableResultado: accion ? denominacion.slice(accion.length).trim() : denominacion,
      territorializacion: origen?.territorializacion || '',
      responsable: origen?.responsable || '',
      cuentaConFinanciamiento: !!origen?.cuenta_con_financiamiento,
      indicador: this.hidratarIndicador(origen?.indicador),
      fisica: this.hidratarProgramacion(origen?.programacion_fisica),
      presupuesto: this.hidratarProgramacion(origen?.presupuesto_anual),
      productos: (origen?.productos || []).map((p: any) => ({
        denominacion: p?.denominacion || '',
        territorializacion: p?.territorializacion || '',
        responsable: p?.responsable || '',
        cuentaConFinanciamiento: !!p?.cuenta_con_financiamiento,
        indicador: this.hidratarIndicador(p?.indicador),
        fisica: this.hidratarProgramacion(p?.programacion_fisica),
        presupuesto: this.hidratarProgramacion(p?.presupuesto_anual),
      })),
    };
  }

  // --- Derivados ------------------------------------------------------------

  get ejeActual(): EjePgdesa | undefined {
    return this.ejes.find(e => e.codigo === this.cabecera.codEjePgdesa);
  }

  get filasA(): FilaMatrizA[] {
    return construirMatrizA(this.cabecera, this.resultados);
  }

  get filasB(): FilaMatrizB[] {
    return construirMatrizB(this.cabecera, this.resultados);
  }

  get hallazgos(): Hallazgo[] {
    return validarMatrices(this.cabecera, this.resultados);
  }

  get bloqueado(): boolean {
    return tieneErrores(this.hallazgos);
  }

  get totalProductos(): number {
    return this.resultados.reduce((total, r) => total + r.productos.length, 0);
  }

  get presupuestoQuinquenal(): number {
    return this.resultados.reduce(
      (total, r) => total + sumarProgramacion(consolidarPresupuesto(r.productos)),
      0,
    );
  }

  // --- Navegación y selección ----------------------------------------------

  irAPaso(p: number): void {
    if (p <= this.paso) this.paso = p;
  }

  selEje(eje: EjePgdesa): void {
    this.cabecera.codEjePgdesa = eje.codigo;
    this.cabecera.objetivoImpacto = eje.objetivoImpacto;
    this.cabecera.codComponentePdesa = '';
    this.cabecera.objetivoEfecto = '';
  }

  selComponente(componente: ComponentePdesa): void {
    this.cabecera.codComponentePdesa = componente.codigo;
    this.cabecera.objetivoEfecto = componente.objetivoEfecto;
  }

  onSectorChange(): void {
    const sector = this.sectores.find(
      s => String(s.codigo) === String(this.cabecera.codSector),
    );
    if (sector) {
      this.cabecera.sector = sector.nombre;
      if (!this.cabecera.codResultadoSectorial) {
        this.cabecera.codResultadoSectorial = `${sector.codigo}.1`;
      }
    }
  }

  onLineamientoCatalogo(): void {
    const elegido = this.lineamientos.find(l => l.id === this.cabecera.lineamientoId);
    if (!elegido) {
      // Vuelve a captura manual: recupera el correlativo asignado.
      this.cabecera.codLineamiento = this.codigoAsignado;
      return;
    }
    this.cabecera.codLineamiento = elegido.codigo || this.cabecera.codLineamiento;
    this.cabecera.lineamiento = elegido.denominacion || this.cabecera.lineamiento;
  }

  /** Reloads the first downstream level and clears selections made invalid. */
  onOdsChange(): void {
    this.preservarSeleccionesGuardadas = false;
    this.cabecera.codNdc = 'N/A';
    this.cabecera.codNdt = 'N/A';
    this.cabecera.compromiso3030 = 'N/A';
    this.opcionesNdc = [];
    this.opcionesNdt = [];
    this.opcionesKmgbf = [];
    this.cargarCompatibilidades('ODS', 'NDC');
  }

  /** Reloads NDT options for the selected ODS/NDC path. */
  onNdcChange(): void {
    this.cabecera.codNdt = 'N/A';
    this.cabecera.compromiso3030 = 'N/A';
    this.opcionesNdt = [];
    this.opcionesKmgbf = [];
    this.cargarCompatibilidades(['ODS', 'NDC'], 'NDT');
  }

  /** Reloads KMGBF/30x30 options for the selected ODS/NDC/NDT path. */
  onNdtChange(): void {
    this.cabecera.compromiso3030 = 'N/A';
    this.opcionesKmgbf = [];
    // NDT options were already intersected with ODS + NDC; only the selected
    // NDT is needed for the terminal lookup.
    this.cargarCompatibilidades('NDT', 'COMPROMISO_3030');
  }

  onKmgbfChange(): void {
    // The terminal selection does not have a downstream level.
  }

  private cargarCompatibilidades(
    origenTipos: TipoAcuerdo | TipoAcuerdo[],
    destinoTipo: TipoAcuerdo,
  ): void {
    const tipos = Array.isArray(origenTipos) ? origenTipos : [origenTipos];
    const origenIds = this.idsPorTipos(tipos);
    const origenClave = origenIds.join(',');
    if (!origenIds.length) {
      this.asignarOpciones(destinoTipo, []);
      return;
    }

    this.cargandoCompatibilidades[destinoTipo] = true;
    this.compatibilidades.listar({
      origenIds,
      destinoTipo,
      incluirSugerencias: true,
    }).subscribe({
      next: response => {
        if (this.idsPorTipos(tipos).join(',') !== origenClave) return;
        this.asignarOpciones(destinoTipo, response.results || []);
        this.cargandoCompatibilidades[destinoTipo] = false;
        if (destinoTipo === 'NDC' && this.codigoSeleccionado(this.cabecera.codNdc)) {
          this.cargarCompatibilidades(['ODS', 'NDC'], 'NDT');
        } else if (destinoTipo === 'NDT' && this.codigoSeleccionado(this.cabecera.codNdt)) {
          this.cargarCompatibilidades('NDT', 'COMPROMISO_3030');
        }
        this.cdr.markForCheck();
      },
      error: () => {
        this.asignarOpciones(destinoTipo, []);
        this.cargandoCompatibilidades[destinoTipo] = false;
        this.cdr.markForCheck();
      },
    });
  }

  private asignarOpciones(
    destinoTipo: TipoAcuerdo,
    relaciones: CompatibilidadAcuerdo[],
  ): void {
    const mejores = new Map<string, CompatibilidadAcuerdo>();
    for (const relacion of relaciones) {
      if (relacion.estado === 'RECHAZADA' || !relacion.activo) continue;
      const anterior = mejores.get(relacion.destino.id);
      if (!anterior || this.rangoRelacion(relacion) < this.rangoRelacion(anterior)) {
        mejores.set(relacion.destino.id, relacion);
      }
    }
    const opciones: OpcionAcuerdoFiltrada[] = Array.from(mejores.values())
      .sort((a, b) => this.compararOpciones(a, b))
      .map(relacion => ({ ...relacion.destino, compatibilidad: relacion }));

    const codigoActual = this.codigosDeValor(this.codigoDeTipo(destinoTipo))[0] || '';
    if (
      this.preservarSeleccionesGuardadas
      && this.codigoSeleccionado(codigoActual)
      && !opciones.some(opcion => opcion.codigo === codigoActual)
    ) {
      const guardada = this.acuerdos.find(
        acuerdo => acuerdo.tipo_acuerdo === destinoTipo && acuerdo.codigo === codigoActual,
      );
      if (guardada) opciones.push({ ...guardada, seleccionGuardada: true });
    }
    this.asignarOpcionesDirectamente(destinoTipo, opciones);
  }

  private asignarOpcionesDirectamente(
    destinoTipo: TipoAcuerdo,
    opciones: OpcionAcuerdoFiltrada[],
  ): void {
    if (destinoTipo === 'NDC') this.opcionesNdc = opciones;
    if (destinoTipo === 'NDT') this.opcionesNdt = opciones;
    if (destinoTipo === 'COMPROMISO_3030') this.opcionesKmgbf = opciones;
  }

  private compararOpciones(a: CompatibilidadAcuerdo, b: CompatibilidadAcuerdo): number {
    return this.rangoRelacion(a) - this.rangoRelacion(b)
      || String(a.destino.codigo).localeCompare(String(b.destino.codigo), 'es', { numeric: true });
  }

  private rangoRelacion(relacion: CompatibilidadAcuerdo): number {
    const confianza = { ALTA: 0, MEDIA: 10, BAJA: 20 }[relacion.confianza] ?? 30;
    const tipo = {
      OFICIAL_EXPLICITA: 0,
      DERIVADA_DOCUMENTAL: 1,
      SUGERENCIA_SEMANTICA: 2,
    }[relacion.tipo_relacion] ?? 3;
    return confianza + tipo;
  }

  private idsPorTipo(tipo: TipoAcuerdo): string[] {
    const codigos = this.codigosDeValor(this.codigoDeTipo(tipo));
    return this.acuerdos
      .filter(acuerdo => acuerdo.tipo_acuerdo === tipo && codigos.includes(acuerdo.codigo))
      .map(acuerdo => acuerdo.id);
  }

  private idsPorTipos(tipos: TipoAcuerdo[]): string[] {
    return tipos.reduce<string[]>(
      (ids, tipo) => [...ids, ...this.idsPorTipo(tipo)],
      [],
    );
  }

  private codigosDeValor(valor: CodigoAcuerdo): string[] {
    return (Array.isArray(valor) ? valor : [valor])
      .map(codigo => String(codigo || '').trim())
      .filter(codigo => codigo && codigo.toUpperCase() !== 'N/A');
  }

  private codigoSeleccionado(valor: CodigoAcuerdo): boolean {
    return this.codigosDeValor(valor).length > 0;
  }

  private codigoDeTipo(tipo: TipoAcuerdo): CodigoAcuerdo {
    if (tipo === 'ODS') return this.cabecera.codOds;
    if (tipo === 'NDC') return this.cabecera.codNdc;
    if (tipo === 'NDT') return this.cabecera.codNdt;
    return this.cabecera.compromiso3030;
  }

  etiquetaCompatibilidad(opcion: OpcionAcuerdoFiltrada): string {
    if (opcion.seleccionGuardada) return 'Guardada · sin relación clasificada';
    if (!opcion.compatibilidad) return 'Sin clasificar';
    const etiquetas: Record<TipoRelacion, string> = {
      OFICIAL_EXPLICITA: 'Oficial',
      DERIVADA_DOCUMENTAL: 'Derivada',
      SUGERENCIA_SEMANTICA: 'Sugerencia IA',
    };
    return `${etiquetas[opcion.compatibilidad.tipo_relacion]} · ${opcion.compatibilidad.confianza_display}`;
  }

  mensajeCascada(tipo: TipoAcuerdo): string {
    if (!this.codigoSeleccionado(this.codigoDeTipo(tipo === 'NDC' ? 'ODS' : tipo === 'NDT' ? 'NDC' : 'NDT'))) {
      return '';
    }
    const opciones = tipo === 'NDC' ? this.opcionesNdc : tipo === 'NDT' ? this.opcionesNdt : this.opcionesKmgbf;
    if (this.cargandoCompatibilidades[tipo]) return 'Cargando compatibilidades clasificadas…';
    if (!opciones.length) return 'No hay relaciones clasificadas para esta selección; no se muestra todo el catálogo.';
    if (opciones.every(opcion => opcion.compatibilidad?.tipo_relacion === 'SUGERENCIA_SEMANTICA')) {
      return 'Solo hay Sugerencias IA: son referencias semánticas candidatas y no constituyen compatibilidad normativa.';
    }
    return '';
  }

  /**
   * El código del lineamiento es un correlativo de la entidad (Guía PAD
   * §4.5.2.b): continúa la numeración de los lineamientos ya registrados.
   */
  private asignarCodigoLineamiento(): void {
    const usados = this.lineamientos
      .map(l => Number(String(l?.codigo || '').trim()))
      .filter(n => Number.isFinite(n) && n > 0);
    this.codigoAsignado = String(usados.length ? Math.max(...usados) + 1 : 1);
    if (!this.cabecera.lineamientoId) {
      this.cabecera.codLineamiento = this.codigoAsignado;
    }
    this.cdr.markForCheck();
  }

  // --- Resultados y productos ----------------------------------------------

  agregarResultado(): void {
    this.resultados.push(resultadoVacio());
  }

  quitarResultado(indice: number): void {
    this.resultados.splice(indice, 1);
  }

  agregarProducto(resultado: ResultadoPadForm): void {
    resultado.productos.push(productoVacio(resultado.responsable));
  }

  quitarProducto(resultado: ResultadoPadForm, indice: number): void {
    resultado.productos.splice(indice, 1);
  }

  codigoDeResultado(indice: number): string {
    return (
      codigoResultado(
        this.cabecera.codGeografico,
        this.cabecera.codLineamiento,
        indice + 1,
      ) || `RES.${indice + 1}`
    );
  }

  codigoDeProducto(indiceResultado: number, indiceProducto: number): string {
    const base = codigoResultado(
      this.cabecera.codGeografico,
      this.cabecera.codLineamiento,
      indiceResultado + 1,
    );
    return codigoProducto(base, indiceProducto) || `PROD.${indiceProducto + 1}`;
  }

  nombreDeResultado(resultado: ResultadoPadForm): string {
    return redactarResultado(resultado.accionCambio, resultado.variableResultado);
  }

  totalProducto(producto: ProductoPadForm): number {
    return sumarProgramacion(producto.presupuesto);
  }

  totalResultado(resultado: ResultadoPadForm): number {
    return sumarProgramacion(consolidarPresupuesto(resultado.productos));
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '0';
  }

  // --- Persistencia ---------------------------------------------------------

  /**
   * Crea el borrador, guarda cada sección con el contrato del backend
   * (`seccion` + `valores`) y lo materializa en ResultadoPAD → ProductoPAD.
   */
  guardar(): void {
    if (this.bloqueado || this.guardando) return;
    this.guardando = true;
    this.msg = 'Registrando las matrices PAD…';
    this.msgClass = '';

    const origen = this.modoEdicion
      ? this.matrices.obtener(this.borradorId as string)
      : this.matrices.crear({ gestion: Number(this.gestion) });

    origen.pipe(
      switchMap(borrador =>
        from(this.secciones()).pipe(
          concatMap(([seccion, valores]) =>
            this.matrices.guardarSeccion(borrador.id, seccion, valores),
          ),
          toArray(),
          // El backend rechaza rematerializar: un borrador COMPLETO ya generó
          // sus ResultadoPAD/ProductoPAD y solo se actualizan sus secciones.
          switchMap(() =>
            borrador.estado === 'COMPLETO'
              ? of({ materializado: false })
              : this.matrices.materializar(borrador.id),
          ),
        ),
      ),
    ).subscribe({
      next: (resultado: any) => {
        this.guardando = false;
        this.msgClass = 'exito';
        this.msg = resultado?.materializado === false
          ? `✅ Registro actualizado: ${this.resultados.length} resultado(s) y ${this.totalProductos} producto(s). Los registros operativos ya materializados no se recrean.`
          : `✅ Matrices PAD registradas: ${this.resultados.length} resultado(s) y ${this.totalProductos} producto(s) materializados.`;
        this.cdr.markForCheck();
      },
      error: (err: any) => {
        this.guardando = false;
        this.msg = `❌ ${this.detalleError(err)}`;
        this.msgClass = 'error';
        this.cdr.markForCheck();
      },
    });
  }

  /** Secciones del borrador en el orden que espera el backend. */
  private secciones(): [string, unknown][] {
    return [
      ['p1_nacional', {
        eje: { codigo: this.cabecera.codEjePgdesa },
        componente: { codigo: this.cabecera.codComponentePdesa },
        objetivo_impacto: this.cabecera.objetivoImpacto,
        objetivo_efecto: this.cabecera.objetivoEfecto,
      }],
      ['p2_acuerdos', {
        ods: this.acuerdo('ODS', this.cabecera.codOds),
        ndc: this.acuerdo('NDC', this.cabecera.codNdc),
        ndt: this.acuerdo('NDT', this.cabecera.codNdt),
        kmgbf: this.acuerdo('COMPROMISO_3030', this.cabecera.compromiso3030),
      }],
      ['p3_sectorial', {
        sector: {
          codigo: this.cabecera.codSector,
          denominacion: this.cabecera.sector,
        },
        resultado_sectorial: {
          codigo: this.cabecera.codResultadoSectorial,
          denominacion: this.cabecera.resultadoSectorial,
        },
      }],
      ['p4_territorial', {
        cgeo: { codigo: this.cabecera.codGeografico },
        eta: this.cabecera.eta,
        politica: this.cabecera.politica,
      }],
      ['p5_lineamiento', {
        lineamiento: {
          id: this.cabecera.lineamientoId,
          codigo: this.cabecera.codLineamiento,
          denominacion: this.cabecera.lineamiento,
        },
      }],
      ['resultados', this.resultados.map(r => ({
        denominacion: redactarResultado(r.accionCambio, r.variableResultado),
        territorializacion: r.territorializacion,
        responsable: r.responsable,
        cuenta_con_financiamiento: r.cuentaConFinanciamiento,
        indicador: this.indicadorPayload(r),
        programacion_fisica: r.fisica,
        presupuesto_total: sumarProgramacion(consolidarPresupuesto(r.productos)),
        presupuesto_anual: consolidarPresupuesto(r.productos),
        productos: r.productos.map(p => ({
          denominacion: p.denominacion,
          territorializacion: p.territorializacion,
          responsable: p.responsable,
          cuenta_con_financiamiento: p.cuentaConFinanciamiento,
          indicador: this.indicadorPayload(p),
          programacion_fisica: p.fisica,
          presupuesto_total: sumarProgramacion(p.presupuesto),
          presupuesto_anual: p.presupuesto,
        })),
      }))],
    ];
  }

  private indicadorPayload(origen: ResultadoPadForm | ProductoPadForm): Record<string, unknown> {
    return {
      indicador: origen.indicador.indicador,
      formula: origen.indicador.formula,
      unidad_medida: origen.indicador.unidadMedida,
      linea_base: origen.indicador.lineaBase,
      meta_2030: origen.indicador.meta2030,
    };
  }

  /**
   * El backend solo considera el acuerdo cuando llega con `id`; 'N/A' o vacío
   * significan que no aplica.
   */
  private acuerdo(tipo: string, codigo: string): unknown {
    if (!codigo || codigo.trim().toUpperCase() === 'N/A') return 'N/A';
    const encontrado = this.acuerdos.find(
      a => a.tipo_acuerdo === tipo && String(a.codigo) === String(codigo).trim(),
    );
    return encontrado
      ? { id: encontrado.id, codigo: encontrado.codigo }
      : { codigo: String(codigo).trim() };
  }

  private detalleError(err: any): string {
    const cuerpo = err?.error ?? err;
    if (cuerpo && typeof cuerpo === 'object') {
      const detalles = Object.entries(cuerpo).map(
        ([campo, valor]) => `${campo}: ${Array.isArray(valor) ? valor.join(', ') : valor}`,
      );
      if (detalles.length) return detalles.join(' · ');
    }
    return err?.message || 'No se pudieron registrar las matrices PAD.';
  }

  // --- Carga de catálogos ---------------------------------------------------

  private cargarSectores(): void {
    this.api.get<any>('/pad/sectores-pad/').subscribe({
      next: (r: any) => { this.sectores = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.sectores = [];         this.cdr.markForCheck();
      },
    });
  }

  private cargarLineamientos(pagina = 1, acumulado: any[] = []): void {
    this.api.get<any>('/articulacion/lineamientos-pad/', { page: pagina }).subscribe({
      next: (r: any) => {
        const lote = r?.results || (Array.isArray(r) ? r : []);
        const total = [...acumulado, ...lote];
        if (r?.next) {
          this.cargarLineamientos(pagina + 1, total);
        } else {
          this.lineamientos = total;
          this.asignarCodigoLineamiento();
        }
              this.cdr.markForCheck();
      },
      error: () => { this.lineamientos = acumulado; this.asignarCodigoLineamiento();         this.cdr.markForCheck();
      },
    });
  }


  /**
   * Catálogo maestro de acuerdos internacionales. La API pagina de a 25 y no
   * acepta `page_size`, así que hay que recorrer las páginas.
   */
  private cargarAcuerdosPagina(pagina = 1, acumulado: any[] = []): void {
    this.api.get<any>('/articulacion/acuerdos/', { page: pagina, activo: true }).subscribe({
      next: (r: any) => {
        const lote = r?.results || (Array.isArray(r) ? r : []);
        const total = [...acumulado, ...lote];
        if (r?.next) {
          this.cargarAcuerdosPagina(pagina + 1, total);
        } else {
          this.acuerdos = total;
          this.cdr.markForCheck();
          this.inicializarCascada();
        }
      },
      error: () => { this.acuerdos = acumulado; this.cdr.markForCheck(); },
    });
  }

  private porTipo(tipo: TipoAcuerdo): AcuerdoInternacionalOption[] {
    return this.acuerdos
      .filter(a => a.tipo_acuerdo === tipo)
      .sort((a, b) => String(a.codigo).localeCompare(String(b.codigo), 'es', { numeric: true }));
  }

  get catalogoOds(): AcuerdoInternacionalOption[] { return this.porTipo('ODS'); }
  get catalogoNdc(): OpcionAcuerdoFiltrada[] { return this.opcionesNdc; }
  get catalogoNdt(): OpcionAcuerdoFiltrada[] { return this.opcionesNdt; }
  get catalogo3030(): OpcionAcuerdoFiltrada[] { return this.opcionesKmgbf; }

  private inicializarCascada(): void {
    this.preservarSeleccionesGuardadas = true;
    this.cargarCompatibilidades('ODS', 'NDC');
  }

  private cargarAcuerdos(): void {
    this.cargarAcuerdosPagina();
  }
}
