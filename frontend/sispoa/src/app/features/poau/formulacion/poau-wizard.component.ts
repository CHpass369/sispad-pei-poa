import { HttpClient } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { concatMap, from, of, switchMap, toArray } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';
import { environment } from '../../../../environments/environment';
import {
  ActividadForm,
  CabeceraPoau,
  FilaMatrizPoau,
  Hallazgo,
  MESES,
  OperacionForm,
  TIPOS_OPERACION,
  TareaForm,
  actividadVacia,
  cabeceraVacia,
  indicadorVacio,
  codigoActividad,
  codigoOperacion,
  codigoTarea,
  construirFilas,
  operacionVacia,
  ponderacionTotal,
  programacionVacia,
  tareaVacia,
  tieneErrores,
  totalAnual,
  validarMatriz,
} from './poau-matriz.model';

/**
 * Asistente de formulación del POAU (RE-SPO, Artículo 14 inciso b).
 *
 * Toma una acción de corto plazo del POA y la desagrega en operaciones,
 * actividades y tareas, con programación física mensual.
 */
@Component({
  selector: 'app-poau-wizard',
  standalone: false,
  template: `
    <div class="poau-full">
      <div class="poau-header">
        <h1>FORMULACIÓN POAU — PROGRAMACIÓN FÍSICA</h1>
        <p>
          Desagregación operativa de la acción de corto plazo:
          Operaciones → Actividades → Tareas específicas, mes a mes
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

      <!-- PASO 0: ARTICULACIÓN CON EL POA -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Acción de corto plazo a desagregar</h3>
        <p>
          El POAU no se formula en el aire: desagrega una acción de corto plazo ya
          programada en el POA, heredando su articulación con el PEI.
        </p>
        <div class="form-2col">
          <div class="field"><label>Gestión</label>
            <input [ngModel]="cabecera.gestion" name="gestion" type="number" class="form-control" readonly
                   title="La fija la habilitación de gestión fiscal"></div>
          <div class="field">
            <label>Acción de corto plazo del POA</label>
            <select [(ngModel)]="accionSel" class="form-control" (change)="heredarDelPoa()">
              <option value="">Seleccione...</option>
              <option *ngFor="let a of accionesPoa" [value]="a.id">
                {{ a.codigo_accion }} — {{ (a.denominacion || '') | slice:0:70 }}
              </option>
            </select>
          </div>
        </div>

        <div class="aviso-vacio" *ngIf="!cargandoPoa && !accionesPoa.length">
          No hay acciones de corto plazo registradas. Formule primero el POA:
          sin él el POAU no tiene qué desagregar.
          <a routerLink="/sis-poa/poas" class="btn btn-sm btn-primary">Ir a la formulación POA</a>
        </div>

        <div class="heredado" *ngIf="cabecera.accionPoaId">
          <h4>Heredado del POA</h4>
          <div class="form-2col">
            <div class="field"><label>Código acción de corto plazo</label>
              <input [ngModel]="cabecera.codigoAccionCortoPlazo" class="form-control" readonly></div>
            <div class="field"><label>Categoría programática</label>
              <input [(ngModel)]="cabecera.categoriaProgramatica" class="form-control"></div>
          </div>
          <div class="field"><label>Acción de corto plazo {{ cabecera.gestion }}</label>
            <textarea [ngModel]="cabecera.accionCortoPlazo" class="form-control" rows="2" readonly></textarea></div>
          <div class="field" *ngIf="catalogoDisponible">
            <label>Categoría programática del catálogo maestro</label>
            <select [(ngModel)]="categoriaSel" class="form-control" (change)="aplicarCategoriaMaestro()">
              <option [ngValue]="null">Seleccione del catálogo…</option>
              <option *ngFor="let c of categoriasMaestro" [ngValue]="c">
                {{ c.codigo || c.codigo_compuesto }}
              </option>
            </select>
          </div>
          <div class="field"><label>Denominación de la categoría programática</label>
            <input [(ngModel)]="cabecera.denominacionCategoria" class="form-control"
                   [readonly]="catalogoDisponible"
                   [class.derivada]="catalogoDisponible"
                   placeholder="Se toma del catálogo maestro">
            <small *ngIf="catalogoDisponible">
              Denominación oficial del clasificador: no se escribe a mano.
            </small>
            <small *ngIf="!catalogoDisponible" class="alerta">
              El catálogo maestro no está disponible; la denominación queda bajo su
              responsabilidad hasta que se pueda validar contra el clasificador.
            </small>
          </div>
        </div>

        <div class="step-nav">
          <span></span>
          <button class="btn btn-primary" [disabled]="!cabecera.accionPoaId" (click)="paso = 1">
            Siguiente → Operaciones
          </button>
        </div>
      </div>

      <!-- PASO 1: OPERACIONES -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Operaciones</h3>
        <p>
          Las operaciones conducen al resultado esperado de la acción de corto plazo y se
          clasifican por tipo: de funcionamiento o de inversión.
        </p>
        <div class="inline-actions">
          <button class="btn btn-accent btn-sm" (click)="agregarOperacion()">+ Agregar operación</button>
          <span class="ponderacion" [class.desviada]="Math.abs(ponderacion - 100) > 0.01">
            Ponderación total: {{ ponderacion }}%
          </span>
        </div>

        <div class="operacion-card" *ngFor="let o of operaciones; let i = index">
          <div class="operacion-head">
            <span class="codigo">{{ codigoDeOperacion(i) }}</span>
            <span class="operacion-nombre">{{ o.denominacion || 'Operación sin denominar' }}</span>
            <button class="btn btn-sm btn-danger" (click)="quitarOperacion(i)">Quitar</button>
          </div>

          <div class="field"><label>Operación (producto intermedio)</label>
            <input [(ngModel)]="o.denominacion" class="form-control"
                   placeholder="Ej: Ejecutar el 100% de los servicios de asesoramiento jurídico"></div>
          <div class="form-3col">
            <div class="field"><label>Tipo de operación</label>
              <select [(ngModel)]="o.tipoOperacion" class="form-control">
                <option *ngFor="let t of tiposOperacion" [value]="t.valor">{{ t.etiqueta }}</option>
              </select>
            </div>
            <div class="field"><label>Unidad organizacional ejecutora</label>
              <input [(ngModel)]="o.unidadEjecutora" class="form-control"></div>
            <div class="field"><label>% Ponderación</label>
              <input [(ngModel)]="o.ponderacion" type="number" class="form-control"></div>
          </div>
          <div class="field"><label>Producto intermedio esperado</label>
            <textarea [(ngModel)]="o.productoIntermedio" class="form-control" rows="2"
                      placeholder="El bien o servicio que queda al concluir la operación"></textarea></div>

          <h5>Indicador</h5>
          <div class="form-3col">
            <div class="field"><label>Indicador</label>
              <input [(ngModel)]="o.indicador.indicador" class="form-control"></div>
            <div class="field"><label>Fórmula</label>
              <input [(ngModel)]="o.indicador.formula" class="form-control"></div>
            <div class="field"><label>Unidad de medida</label>
              <input [(ngModel)]="o.indicador.unidadMedida" class="form-control" placeholder="Porcentaje / Número"></div>
          </div>
          <div class="form-3col">
            <div class="field"><label>Línea base</label>
              <input [(ngModel)]="o.indicador.lineaBase" type="number" class="form-control"></div>
            <div class="field"><label>Meta</label>
              <input [(ngModel)]="o.indicador.meta" type="number" class="form-control"></div>
            <div class="field"><label>Total programado</label>
              <input [ngModel]="total(o.programacion)" class="form-control derivada" readonly></div>
          </div>
          <div class="form-2col">
            <div class="field"><label>Fecha prevista de inicio</label>
              <input [(ngModel)]="o.fechaInicio" type="date" class="form-control"></div>
            <div class="field"><label>Fecha prevista de finalización</label>
              <input [(ngModel)]="o.fechaFin" type="date" class="form-control"></div>
          </div>

          <h5>Programación física mensual</h5>
          <div class="meses-grid">
            <div *ngFor="let mes of meses" class="field">
              <label>{{ mes | slice:0:3 }}</label>
              <input [(ngModel)]="o.programacion[mes]" type="number" class="form-control">
            </div>
          </div>
        </div>

        <div class="vacio-operaciones" *ngIf="!operaciones.length">
          Sin operaciones no hay POAU: agregue al menos una.
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 0">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!operaciones.length" (click)="paso = 2">
            Siguiente → Actividades y tareas
          </button>
        </div>
      </div>

      <!-- PASO 2: ACTIVIDADES Y TAREAS ESPECÍFICAS -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Actividades y tareas específicas</h3>
        <p>
          La actividad es opcional: se usa cuando hace falta asignar recursos de forma
          individualizada dentro de la operación. Las tareas específicas son lo que se
          ejecuta para alcanzarla.
        </p>

        <div class="operacion-card" *ngFor="let o of operaciones; let i = index">
          <div class="operacion-head">
            <span class="codigo">{{ codigoDeOperacion(i) }}</span>
            <span class="operacion-nombre">{{ o.denominacion || 'Operación sin denominar' }}</span>
            <span class="rango" *ngIf="o.fechaInicio || o.fechaFin">
              {{ o.fechaInicio || '?' }} → {{ o.fechaFin || '?' }}
            </span>
            <button class="btn btn-accent btn-sm" (click)="agregarActividad(o)">+ Actividad</button>
          </div>

          <div class="sin-actividades" *ngIf="!o.actividades.length">
            Esta operación no tiene actividades. Es válido: la desagregación es opcional.
          </div>

          <div class="actividad-card" *ngFor="let ac of o.actividades; let j = index">
            <div class="operacion-head">
              <span class="codigo">{{ codigoDeActividad(i, j) }}</span>
              <span class="operacion-nombre">{{ ac.denominacion || 'Actividad sin denominar' }}</span>
              <button class="btn btn-sm btn-danger" (click)="quitarActividad(o, j)">Quitar</button>
            </div>

            <div class="field"><label>Actividad</label>
              <input [(ngModel)]="ac.denominacion" class="form-control"></div>
            <div class="field"><label>Producto intermedio de la actividad</label>
              <input [(ngModel)]="ac.productoIntermedio" class="form-control"></div>
            <div class="form-3col">
              <div class="field"><label>Indicador</label>
                <input [(ngModel)]="ac.indicador.indicador" class="form-control"></div>
              <div class="field"><label>Unidad de medida</label>
                <input [(ngModel)]="ac.indicador.unidadMedida" class="form-control"></div>
              <div class="field"><label>Meta</label>
                <input [(ngModel)]="ac.indicador.meta" type="number" class="form-control"></div>
            </div>

            <div class="fechas-fila">
              <div class="field"><label>Fecha prevista de inicio</label>
                <input [(ngModel)]="ac.fechaInicio" type="date" class="form-control"></div>
              <div class="field"><label>Fecha prevista de finalización</label>
                <input [(ngModel)]="ac.fechaFin" type="date" class="form-control"></div>
              <button class="btn btn-sm btn-heredar" (click)="fechasDeOperacion(o, ac)"
                      [disabled]="!o.fechaInicio && !o.fechaFin"
                      title="Copia las fechas de la operación">
                ⇱ Mismas fechas que la operación
              </button>
            </div>

            <h5>Programación física mensual</h5>
            <div class="meses-grid">
              <div *ngFor="let mes of meses" class="field">
                <label>{{ mes | slice:0:3 }}</label>
                <input [(ngModel)]="ac.programacion[mes]" type="number" class="form-control">
              </div>
            </div>

            <div class="tareas-zona">
              <div class="inline-actions">
                <strong class="mini-titulo">Tareas específicas</strong>
                <button class="btn btn-accent btn-sm" (click)="agregarTarea(ac)">+ Agregar tarea</button>
              </div>

              <div class="tarea-card" *ngFor="let ta of ac.tareas; let k = index">
                <div class="operacion-head">
                  <span class="codigo">{{ codigoDeTarea(i, j, k) }}</span>
                  <span class="operacion-nombre">{{ ta.denominacion || 'Tarea sin denominar' }}</span>
                  <button class="btn btn-sm btn-danger" (click)="quitarTarea(ac, k)">Quitar</button>
                </div>
                <div class="form-2col">
                  <div class="field"><label>Tarea específica</label>
                    <input [(ngModel)]="ta.denominacion" class="form-control"></div>
                  <div class="field"><label>Responsable</label>
                    <input [(ngModel)]="ta.responsable" class="form-control"></div>
                </div>
                <div class="fechas-fila">
                  <div class="field"><label>Fecha prevista de inicio</label>
                    <input [(ngModel)]="ta.fechaInicio" type="date" class="form-control"></div>
                  <div class="field"><label>Fecha prevista de finalización</label>
                    <input [(ngModel)]="ta.fechaFin" type="date" class="form-control"></div>
                  <button class="btn btn-sm btn-heredar" (click)="fechasDeActividad(ac, ta)"
                          [disabled]="!ac.fechaInicio && !ac.fechaFin"
                          title="Copia las fechas de la actividad">
                    ⇱ Mismas fechas que la actividad
                  </button>
                </div>
                <h5>Programación física mensual</h5>
                <div class="meses-grid">
                  <div *ngFor="let mes of meses" class="field">
                    <label>{{ mes | slice:0:3 }}</label>
                    <input [(ngModel)]="ta.programacion[mes]" type="number" class="form-control">
                  </div>
                </div>
                <div class="tarea-total">
                  Total programado: <strong>{{ total(ta.programacion) }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 1">← Anterior</button>
          <button class="btn btn-primary" (click)="paso = 3">Siguiente → Revisión</button>
        </div>
      </div>

      <!-- PASO 3: REVISIÓN -->
      <div *ngIf="paso === 3" class="step-content card">
        <h3>Paso 4: Revisión y registro del POAU</h3>
        <div class="resumen-grid">
          <div class="resumen-item"><span>Gestión</span><strong>{{ cabecera.gestion }}</strong></div>
          <div class="resumen-item"><span>Acción de corto plazo</span><strong>{{ cabecera.codigoAccionCortoPlazo || '-' }}</strong></div>
          <div class="resumen-item"><span>Operaciones</span><strong>{{ operaciones.length }}</strong></div>
          <div class="resumen-item"><span>Actividades</span><strong>{{ totalActividades }}</strong></div>
          <div class="resumen-item"><span>Ponderación</span><strong>{{ ponderacion }}%</strong></div>
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
          <button class="btn btn-outline" (click)="paso = 2">← Anterior</button>
          <button class="btn btn-success" [disabled]="bloqueado || guardando" (click)="guardar()">
            {{ guardando ? 'Registrando…' : '✓ Registrar POAU' }}
          </button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass === 'error'"
             [class.exito]="msgClass === 'exito'">{{ msg }}</div>
      </div>

        </div>

        <app-control-metodologico [hallazgos]="hallazgos"
                                  fuente="Reglamento Específico SPO — Cuadro 3">
        </app-control-metodologico>
      </div>

      <app-poau-matriz-viewer [filas]="filas" [hallazgos]="hallazgos"
                              [gestion]="cabecera.gestion"></app-poau-matriz-viewer>
    </div>
  `,
  styles: [`
    .poau-full { max-width: var(--ancho-trabajo); margin: 0 auto; padding-bottom: 2rem; }
    .poau-header h1 { font-size: 1.35rem; color: var(--primary); }
    .poau-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1rem; }

    .progress-bar-horizontal { display: flex; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
    .progress-step { flex: 1; text-align: center; padding: 0.5rem 0.25rem; cursor: pointer; position: relative; min-width: 90px; }
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
    .step-content h5 { font-size: 0.8125rem; margin: 0.9rem 0 0.4rem; color: var(--primary); }
    .step-content p { color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 0.8125rem; }

    .form-2col, .form-3col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; }
    .form-2col { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .form-3col { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
    .field { margin-bottom: 0.5rem; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.2rem; }
    .inline-actions { margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .mini-titulo { font-size: 0.8125rem; color: var(--primary); }
    .ponderacion { font-size: 0.75rem; color: var(--text-secondary); }
    .ponderacion.desviada { color: var(--aviso-tinta); font-weight: 700; }
    .step-nav { display: flex; justify-content: space-between; margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }

    .meses-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 0.3rem; margin-bottom: 0.5rem; }
    .meses-grid input { font-size: 0.6875rem; padding: 0.2rem 0.25rem; text-align: right; }
    .meses-grid label { font-size: 0.5625rem; text-align: center; }

    .heredado { margin-top: 1rem; padding: 0.9rem; border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 6px; background: #F7FBF8; }
    .heredado h4 { margin-top: 0; }
    .aviso-vacio { margin-top: 1rem; padding: 0.9rem; background: var(--aviso-fondo); color: var(--aviso-tinta); border-radius: 6px; font-size: 0.8125rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .derivada { background: #F3F7F4; font-weight: 700; }
    .field small { font-size: 0.625rem; color: var(--text-secondary); }
    .field small.alerta { color: var(--aviso-tinta); }

    .operacion-card { border: 2px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1.25rem; }
    .operacion-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .operacion-head .codigo { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); }
    .operacion-nombre { flex: 1; font-size: 0.8125rem; font-weight: 600; }
    .actividades-zona { margin-top: 1rem; padding-left: 1rem; border-left: 3px solid var(--primary); }
    .actividad-card { border: 1px dashed var(--border); border-radius: 6px; padding: 0.75rem; margin-bottom: 0.75rem; }
    .tareas-zona { margin-top: 0.9rem; padding-left: 0.9rem; border-left: 2px dotted var(--border); }
    .tarea-card { border: 1px solid var(--border); border-radius: 6px; padding: 0.7rem; margin-bottom: 0.6rem; background: #FCFDFC; }
    .tarea-total { margin-top: 0.4rem; font-size: 0.75rem; color: var(--text-secondary); }
    .fechas-fila { display: grid; grid-template-columns: 1fr 1fr auto; gap: 0.75rem; align-items: end; margin-bottom: 0.5rem; }
    .btn-heredar { background: transparent; border: 1px dashed var(--primary); color: var(--primary); border-radius: 4px; cursor: pointer; padding: 0.35rem 0.6rem; font-size: 0.6875rem; white-space: nowrap; }
    .btn-heredar:hover:not([disabled]) { background: var(--ok-fondo); border-style: solid; }
    .btn-heredar[disabled] { opacity: 0.45; cursor: not-allowed; }
    .rango { font-size: 0.6875rem; color: var(--text-secondary); font-family: 'Courier New', monospace; }
    .sin-actividades { padding: 0.75rem; text-align: center; color: var(--text-secondary); font-size: 0.75rem; border: 1px dashed var(--border); border-radius: 6px; margin-bottom: 0.75rem; }
    .vacio-operaciones { padding: 1.5rem; text-align: center; color: var(--text-secondary); font-size: 0.8125rem; border: 1px dashed var(--border); border-radius: 8px; }

    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .resumen-item { padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
    .resumen-item span { display: block; font-size: 0.6875rem; color: var(--text-secondary); }
    .resumen-item strong { font-size: 0.8125rem; }

    .hallazgos ul { list-style: none; padding: 0; margin: 0; }
    .hallazgos li { padding: 0.4rem 0.6rem; border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.75rem; }
    .hallazgos li.error { background: var(--error-fondo); color: var(--warn); }
    .hallazgos li.aviso { background: var(--aviso-fondo); color: var(--aviso-tinta); }

    .msg-box { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .msg-box.error { background: var(--error-fondo); color: var(--warn); }
    .msg-box.exito { background: var(--ok-fondo); color: var(--success); }
    .btn-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); border-radius: 4px; cursor: pointer; padding: 0.2rem 0.5rem; font-size: 0.6875rem; }

    @media (max-width: 900px) { .meses-grid { grid-template-columns: repeat(4, 1fr); } }
    @media (max-width: 768px) { .form-2col, .form-3col, .fechas-fila { grid-template-columns: 1fr; } }
  `],
})
export class PoauWizardComponent implements OnInit {
  paso = 0;
  pasos = ['Acción de corto plazo', 'Operaciones', 'Actividades y tareas', 'Registro'];

  Math = Math;
  meses = MESES;
  tiposOperacion = TIPOS_OPERACION;

  cabecera: CabeceraPoau = cabeceraVacia();
  operaciones: OperacionForm[] = [operacionVacia()];

  accionesPoa: any[] = [];
  productosPei: any[] = [];
  accionSel = '';
  cargandoPoa = true;

  /** Catálogo maestro de categorías programáticas (API V2 de presupuesto). */
  categoriasMaestro: any[] = [];
  categoriaSel: any = null;
  catalogoDisponible = true;

  guardando = false;
  msg = '';
  msgClass = '';

  /** Acción de corto plazo que se está editando; vacío al formular una nueva. */
  editandoAccion = '';
  /** Registro sobre el que se pulsó "editar" en la matriz, para resaltarlo. */
  foco = '';
  cargandoEdicion = false;

  constructor(
    private api: ApiService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private ruta: ActivatedRoute,
    private gestionActiva: GestionHabilitadaService,
  ) {}

  ngOnInit(): void {
    // El POAU se formula sobre la gestión habilitada (ADR-007).
    this.cabecera.gestion = this.gestionActiva.anio() ?? 0;
    this.cargarAccionesPoa();
    this.cargarProductosPei();
    this.cargarCategoriasMaestro();

    // Con `:accion` en la ruta el wizard abre en modo edición: trae lo que ya
    // está formulado en vez de arrancar con una operación vacía.
    this.ruta.paramMap.subscribe(p => {
      const accion = p.get('accion') || '';
      this.foco = this.ruta.snapshot.queryParamMap.get('foco') || '';
      if (accion && accion !== this.editandoAccion) {
        this.editandoAccion = accion;
        this.cargarParaEditar(accion);
      }
    });
  }

  /** Trae la acción con su programación y llena los formularios. */
  cargarParaEditar(accionId: string): void {
    this.cargandoEdicion = true;
    this.msg = '';
    this.http.get<any>(`${environment.apiUrl}/articulacion/matriz-poau/${accionId}/`)
      .subscribe({
        next: d => {
          this.cabecera = { ...cabeceraVacia(), ...d.cabecera };
          this.accionSel = d.cabecera.accionPoaId || '';
          this.operaciones = (d.operaciones || []).map((o: any) => ({
            ...operacionVacia(),
            ...o,
            indicador: { ...indicadorVacio(), ...(o.indicador || {}) },
            programacion: { ...programacionVacia(), ...(o.programacion || {}) },
            actividades: (o.actividades || []).map((a: any) => ({
              ...actividadVacia(),
              ...a,
              indicador: { ...indicadorVacio(), ...(a.indicador || {}) },
              programacion: { ...programacionVacia(), ...(a.programacion || {}) },
              tareas: (a.tareas || []).map((t: any) => ({
                ...tareaVacia(), ...t,
                programacion: { ...programacionVacia(), ...(t.programacion || {}) },
              })),
            })),
          }));
          // Sin operaciones el wizard necesita una fila en blanco donde escribir.
          if (!this.operaciones.length) { this.operaciones = [operacionVacia()]; }
          this.paso = 1;
          this.cargandoEdicion = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.msg = 'No se pudo cargar la acción para editar.';
          this.msgClass = 'error';
          this.cargandoEdicion = false;
          this.cdr.markForCheck();
        },
      });
  }

  // --- Derivados ------------------------------------------------------------

  get filas(): FilaMatrizPoau[] {
    return construirFilas(this.cabecera, this.operaciones);
  }

  get hallazgos(): Hallazgo[] {
    return validarMatriz(this.cabecera, this.operaciones);
  }

  get bloqueado(): boolean {
    return tieneErrores(this.hallazgos);
  }

  get ponderacion(): number {
    return ponderacionTotal(this.operaciones);
  }

  get totalActividades(): number {
    return this.operaciones.reduce((t, o) => t + o.actividades.length, 0);
  }

  // --- Navegación y herencia ------------------------------------------------

  irAPaso(p: number): void {
    if (p <= this.paso) this.paso = p;
  }

  heredarDelPoa(): void {
    const accion = this.accionesPoa.find(a => a.id === this.accionSel);
    if (!accion) {
      this.cabecera.accionPoaId = null;
      return;
    }
    this.cabecera.accionPoaId = accion.id;
    this.cabecera.codigoAccionCortoPlazo = accion.codigo_accion || '';
    this.cabecera.accionCortoPlazo = accion.denominacion || '';
    this.cabecera.categoriaProgramatica = accion.categoria_programatica || '';
    this.cabecera.indicadorProceso = accion.indicador || '';
    if (accion.gestion) this.cabecera.gestion = accion.gestion;

    const producto = this.productosPei.find(p => p.id === accion.producto_pei);
    this.cabecera.codigoProductoPei = producto?.codigo_producto || '';
    this.cabecera.accionInstitucionalEspecifica = producto?.denominacion || '';
    this.sincronizarDenominacion();
  }

  // --- Colecciones ----------------------------------------------------------

  agregarOperacion(): void { this.operaciones.push(operacionVacia()); }
  quitarOperacion(i: number): void { this.operaciones.splice(i, 1); }
  agregarActividad(o: OperacionForm): void { o.actividades.push(actividadVacia()); }
  quitarActividad(o: OperacionForm, j: number): void { o.actividades.splice(j, 1); }
  agregarTarea(a: ActividadForm): void { a.tareas.push(tareaVacia()); }
  quitarTarea(a: ActividadForm, k: number): void { a.tareas.splice(k, 1); }

  codigoDeOperacion(i: number): string {
    return codigoOperacion(this.cabecera.codigoAccionCortoPlazo, i) || `OP.${i + 1}`;
  }

  codigoDeActividad(i: number, j: number): string {
    return codigoActividad(this.codigoDeOperacion(i), j) || `ACT.${j + 1}`;
  }

  codigoDeTarea(i: number, j: number, k: number): string {
    return codigoTarea(this.codigoDeActividad(i, j), k) || `TAR.${k + 1}`;
  }

  total(programacion: Record<string, number | null>): number {
    return totalAnual(programacion);
  }

  /** La actividad hereda la ventana temporal de su operación. */
  fechasDeOperacion(operacion: OperacionForm, actividad: ActividadForm): void {
    actividad.fechaInicio = operacion.fechaInicio;
    actividad.fechaFin = operacion.fechaFin;
  }

  /** La tarea hereda la ventana temporal de su actividad. */
  fechasDeActividad(actividad: ActividadForm, tarea: TareaForm): void {
    tarea.fechaInicio = actividad.fechaInicio;
    tarea.fechaFin = actividad.fechaFin;
  }

  // --- Persistencia ---------------------------------------------------------

  guardar(): void {
    if (this.bloqueado || this.guardando) return;
    this.guardando = true;
    this.msg = 'Registrando el POAU…';
    this.msgClass = '';

    from(this.operaciones.map((o, i) => ({ operacion: o, indice: i })))
      .pipe(
        concatMap(({ operacion, indice }) =>
          this.api.post<any>('/articulacion/operaciones/', this.cuerpoOperacion(operacion, indice)).pipe(
            switchMap((creada: any) =>
              operacion.actividades.length
                ? from(operacion.actividades.map((a, j) => ({ actividad: a, j }))).pipe(
                    concatMap(({ actividad, j }) =>
                      this.api.post<any>('/articulacion/actividades/',
                        this.cuerpoActividad(creada.id, actividad, indice, j),
                      ).pipe(
                        switchMap((actCreada: any) =>
                          actividad.tareas.length
                            ? from(actividad.tareas.map((t, k) => ({ tarea: t, k }))).pipe(
                                concatMap(({ tarea, k }) =>
                                  this.api.post('/articulacion/tareas/',
                                    this.cuerpoTarea(actCreada.id, tarea, indice, j, k),
                                  ),
                                ),
                                toArray(),
                              )
                            : of([]),
                        ),
                      ),
                    ),
                    toArray(),
                  )
                : of([]),
            ),
          ),
        ),
        toArray(),
      )
      .subscribe({
        next: () => {
          this.guardando = false;
          this.msg = `✅ POAU registrado: ${this.operaciones.length} operación(es) y ${this.totalActividades} actividad(es) sobre ${this.cabecera.codigoAccionCortoPlazo}.`;
          this.msgClass = 'exito';
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

  private cuerpoOperacion(operacion: OperacionForm, indice: number): Record<string, unknown> {
    return {
      codigo_operacion: this.codigoDeOperacion(indice),
      denominacion: operacion.denominacion,
      tipo_operacion: operacion.tipoOperacion,
      producto_entregable: operacion.productoIntermedio,
      accion_poa: this.cabecera.accionPoaId,
      codigo_unidad_ejecutora: '',
      responsable: operacion.unidadEjecutora,
      meta_anual: operacion.indicador.meta,
      indicador: operacion.indicador.indicador,
      formula: operacion.indicador.formula,
      unidad_medida: operacion.indicador.unidadMedida,
      fecha_inicio: operacion.fechaInicio || null,
      fecha_fin: operacion.fechaFin || null,
      programacion_mensual: operacion.programacion,
      total_programado: totalAnual(operacion.programacion),
    };
  }

  private cuerpoActividad(
    operacionId: string,
    actividad: ActividadForm,
    i: number,
    j: number,
  ): Record<string, unknown> {
    return {
      codigo_actividad: this.codigoDeActividad(i, j),
      denominacion: actividad.denominacion,
      operacion: operacionId,
      producto_entregable: actividad.productoIntermedio,
      meta_anual: actividad.indicador.meta,
      indicador: actividad.indicador.indicador,
      formula: actividad.indicador.formula,
      unidad_medida: actividad.indicador.unidadMedida,
      fecha_inicio: actividad.fechaInicio || null,
      fecha_fin: actividad.fechaFin || null,
      programacion_mensual: actividad.programacion,
      total_programado: totalAnual(actividad.programacion),
    };
  }

  private cuerpoTarea(
    actividadId: string,
    tarea: TareaForm,
    i: number,
    j: number,
    k: number,
  ): Record<string, unknown> {
    return {
      codigo_tarea: this.codigoDeTarea(i, j, k),
      denominacion: tarea.denominacion,
      actividad: actividadId,
      responsable: tarea.responsable,
      fecha_inicio: tarea.fechaInicio || null,
      fecha_fin: tarea.fechaFin || null,
      programacion_mensual: tarea.programacion,
    };
  }

  private detalleError(err: any): string {
    const cuerpo = err?.error ?? err;
    if (cuerpo && typeof cuerpo === 'object') {
      const detalles = Object.entries(cuerpo).map(
        ([campo, valor]) => `${campo}: ${Array.isArray(valor) ? valor.join(', ') : valor}`,
      );
      if (detalles.length) return detalles.join(' · ');
    }
    return err?.message || 'No se pudo registrar el POAU.';
  }

  // --- Carga de catálogos ---------------------------------------------------

  private cargarAccionesPoa(): void {
    this.api.get<any>('/articulacion/acciones-poa/').subscribe({
      next: (r: any) => {
        this.accionesPoa = r.results || r || [];
        this.cargandoPoa = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.accionesPoa = [];
        this.cargandoPoa = false;
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * La denominación de la categoría programática es dato del clasificador:
   * se resuelve contra el catálogo maestro, nunca se teclea.
   */
  private cargarCategoriasMaestro(): void {
    this.http
      .get<any>(`${environment.apiUrlV2}/sis-poa/budget/programmatic-categories/`)
      .subscribe({
        next: (r: any) => {
          this.categoriasMaestro = r?.results || (Array.isArray(r) ? r : []);
          this.catalogoDisponible = this.categoriasMaestro.length > 0;
          this.sincronizarDenominacion();
          this.cdr.markForCheck();
        },
        error: () => {
          this.categoriasMaestro = [];
          this.catalogoDisponible = false;
          this.cdr.markForCheck();
        },
      });
  }

  /** Busca en el catálogo la categoría heredada del POA y trae su denominación. */
  private sincronizarDenominacion(): void {
    const codigo = this.normalizarCodigo(this.cabecera.categoriaProgramatica);
    if (!codigo || !this.categoriasMaestro.length) return;
    const encontrada = this.categoriasMaestro.find(
      c => this.normalizarCodigo(c.codigo || c.codigo_compuesto) === codigo,
    );
    if (encontrada) {
      this.categoriaSel = encontrada;
      this.cabecera.denominacionCategoria = encontrada.denominacion || '';
    }
  }

  private normalizarCodigo(valor: string): string {
    return String(valor || '').replace(/\s+/g, ' ').trim().toUpperCase();
  }

  aplicarCategoriaMaestro(): void {
    if (!this.categoriaSel) return;
    this.cabecera.categoriaProgramatica =
      this.categoriaSel.codigo || this.categoriaSel.codigo_compuesto || '';
    this.cabecera.denominacionCategoria = this.categoriaSel.denominacion || '';
  }

  private cargarProductosPei(): void {
    this.api.get<any>('/articulacion/productos-pei/').subscribe({
      next: (r: any) => { this.productosPei = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.productosPei = [];         this.cdr.markForCheck();
      },
    });
  }
}
