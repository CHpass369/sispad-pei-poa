import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { concatMap, forkJoin, from, map, Observable, of, switchMap, toArray } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { PeiBorradoresService } from './pei-borradores.service';
import {
  ACCIONES_DE_CAMBIO,
  CATALOGO_ODS,
  CONDICIONES_DE_ESTADO,
  ComponentePdesa,
  EJES_PGDESA,
  EjePgdesa,
  GESTIONES_PEI,
  TIPOS_PRODUCTO,
} from './pei-catalogos';
import {
  ArticulacionPei,
  FilaMatrizPei,
  Hallazgo,
  ProductoPeiForm,
  ResultadoPeiForm,
  articulacionVacia,
  codigoProducto,
  codigoResultado,
  construirFilas,
  productoVacio,
  redactarProducto,
  redactarResultado,
  resultadoVacio,
  tieneErrores,
  totalIndicador,
  validarMatriz,
} from './pei-matriz.model';

/**
 * Asistente de construcción de la Matriz de Planificación PEI 2026-2030.
 *
 * Sigue la secuencia lógica de la Guía Metodológica PEI (anexo 5.1) y va
 * proyectando cada paso sobre el visualizador de matriz que acompaña al
 * formulario, con la misma mecánica del articulador PAD.
 */
@Component({
  selector: 'app-pei-wizard',
  standalone: false,
  template: `
    <div class="pei-full">
      <div class="pei-header">
        <div class="migas">
          <a routerLink="/sis-pe/pei">Matrices PEI</a>
          <span>›</span>
          <span>{{ modoEdicion ? 'Editar registro' : 'Registro nuevo' }}</span>
        </div>
        <h1>MATRIZ PEI 2026-2030 — GUÍA METODOLÓGICA OFICIAL</h1>
        <div class="aviso-edicion" *ngIf="modoEdicion">
          <strong>Editando un registro existente.</strong>
          Los cambios se guardan sobre el mismo borrador al confirmar el registro.
          <span *ngIf="cargandoBorrador"> Cargando datos…</span>
        </div>
        <p>
          Construcción sección por sección: PGDESA → PDESA → Acuerdos → Sector → PAD →
          Resultado institucional → Productos institucionales
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

      <!-- PASO 0: ENTIDAD Y ORIGEN -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Entidad y origen de la articulación</h3>
        <p>
          El código de entidad del clasificador presupuestario es el prefijo de todos los
          códigos del PEI: resultado <code>{{ resultado.codEntidad || 'ENT' }}.1</code>,
          producto <code>{{ resultado.codEntidad || 'ENT' }}.1.1</code>.
        </p>
        <div class="form-2col">
          <div class="field">
            <label>Código de entidad (clasificador presupuestario)</label>
            <input [(ngModel)]="resultado.codEntidad" class="form-control" placeholder="Ej: 907">
          </div>
          <div class="field">
            <label>Entidad (clasificador presupuestario)</label>
            <input [(ngModel)]="resultado.entidad" class="form-control"
                   placeholder="Ej: GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA">
          </div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Vigencia desde</label>
            <input [(ngModel)]="resultado.vigenciaDesde" type="number" class="form-control"></div>
          <div class="field"><label>Vigencia hasta</label>
            <input [(ngModel)]="resultado.vigenciaHasta" type="number" class="form-control"></div>
        </div>

        <h4>¿De dónde parte este resultado institucional?</h4>
        <div class="bifurcacion">
          <div class="bif-card" [class.selected]="origen === 'pad'" (click)="origen = 'pad'">
            <h4>Derivar de un resultado del PAD</h4>
            <p>
              Hereda las secciones I a IV y el código de resultado territorial desde un
              resultado del PAD ya formulado.
            </p>
            <select [(ngModel)]="resultadoPadSel" class="form-control"
                    (change)="heredarDelPad()" *ngIf="origen === 'pad'">
              <option value="">Seleccione un resultado PAD...</option>
              <option *ngFor="let r of resultadosPad" [value]="r.id">
                {{ r.codigo_resultado }} — {{ (r.denominacion || '') | slice:0:70 }}
              </option>
            </select>
            <small *ngIf="origen === 'pad' && !resultadosPad.length">
              No hay resultados PAD registrados todavía; formule desde cero y vincule el
              código territorial más adelante.
            </small>
          </div>
          <div class="bif-card" [class.selected]="origen === 'cero'" (click)="origen = 'cero'">
            <h4>Formular desde cero</h4>
            <p>Captura manual de cada sección de la matriz, con validación metodológica.</p>
          </div>
        </div>

        <div class="step-nav">
          <span></span>
          <button class="btn btn-primary" [disabled]="!resultado.codEntidad || !resultado.entidad" (click)="paso = 1">
            Siguiente → Planificación nacional
          </button>
        </div>
      </div>

      <!-- PASO 1: SECCIÓN I -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Sección I — Planificación nacional</h3>
        <p>Seleccione el eje del PGDESA (objetivo de impacto) y su componente PDESA (objetivo de efecto).</p>
        <div class="select-cards">
          <div *ngFor="let eje of ejes" class="select-card"
               [class.selected]="articulacion.codEjePgdesa === eje.codigo" (click)="selEje(eje)">
            <div class="card-cod">Eje {{ eje.codigo }}</div>
            <div class="card-nombre">{{ eje.titulo }}</div>
          </div>
        </div>
        <div class="field" *ngIf="ejeActual">
          <label>Objetivo de impacto PGDESA</label>
          <textarea [(ngModel)]="articulacion.objetivoImpacto" class="form-control" rows="3"></textarea>
        </div>
        <h4 *ngIf="ejeActual">Componente PDESA</h4>
        <div class="select-cards" *ngIf="ejeActual">
          <div *ngFor="let c of ejeActual.componentes" class="select-card"
               [class.selected]="articulacion.codComponentePdesa === c.codigo" (click)="selComponente(c)">
            <div class="card-cod">{{ c.codigo }}</div>
            <div class="card-desc">{{ c.objetivoEfecto | slice:0:120 }}…</div>
          </div>
        </div>
        <div class="field" *ngIf="articulacion.codComponentePdesa">
          <label>Objetivo de efecto PDESA</label>
          <textarea [(ngModel)]="articulacion.objetivoEfecto" class="form-control" rows="3"></textarea>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 0">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!articulacion.codComponentePdesa" (click)="paso = 2">
            Siguiente → Acuerdos
          </button>
        </div>
      </div>

      <!-- PASO 2: SECCIÓN II -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Sección II — Acuerdos internacionales</h3>
        <p>
          Registre únicamente los códigos cuya relación con el resultado sea directa y
          verificable. Si no aplica, deje <strong>N/A</strong>.
        </p>
        <div class="form-2col">
          <div class="field"><label>Código ODS</label>
            <select [(ngModel)]="articulacion.codOds" class="form-control">
              <option value="">Sin vinculación</option>
              <option *ngFor="let o of catalogoOds" [value]="o.codigo">
                {{ o.codigo }} — {{ o.denominacion | slice:0:90 }}
              </option>
            </select>
          </div>
          <div class="field"><label>Código NDC (contribuciones determinadas a nivel nacional)</label>
            <select [(ngModel)]="articulacion.codNdc" class="form-control">
              <option value="N/A">N/A — no aplica</option>
              <option *ngFor="let n of catalogoNdc" [value]="n.codigo">
                {{ n.codigo }} — {{ n.denominacion | slice:0:90 }}
              </option>
            </select>
          </div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código NDT (neutralidad en la degradación de la tierra)</label>
            <select [(ngModel)]="articulacion.codNdt" class="form-control">
              <option value="N/A">N/A — no aplica</option>
              <option *ngFor="let n of catalogoNdt" [value]="n.codigo">
                {{ n.codigo }} — {{ n.denominacion | slice:0:90 }}
              </option>
            </select>
          </div>
          <div class="field"><label>Código Meta 30x30 (Kunming-Montreal)</label>
            <select [(ngModel)]="articulacion.codMeta3030" class="form-control">
              <option value="N/A">N/A — no aplica</option>
              <option *ngFor="let c of catalogo3030" [value]="c.codigo">
                {{ c.codigo }} — {{ c.denominacion | slice:0:90 }}
              </option>
            </select>
          </div>
        </div>
        <div class="nota" *ngIf="!acuerdos.length">
          El catálogo de acuerdos internacionales no está disponible; los códigos quedarán
          sin validar contra el maestro.
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 1">← Anterior</button>
          <button class="btn btn-primary" (click)="paso = 3">Siguiente → Sector</button>
        </div>
      </div>

      <!-- PASO 3: SECCIONES III Y IV -->
      <div *ngIf="paso === 3" class="step-content card">
        <h3>Paso 4: Secciones III y IV — Sector y articulación sectorial</h3>
        <div class="form-2col">
          <div class="field"><label>Código de sector (clasificador presupuestario)</label>
            <select [(ngModel)]="articulacion.codSector" class="form-control" (change)="onSectorChange()">
              <option value="">Seleccione...</option>
              <option *ngFor="let s of sectores" [value]="s.codigo">{{ s.codigo }} — {{ s.nombre }}</option>
            </select>
          </div>
          <div class="field"><label>Sector</label>
            <input [(ngModel)]="articulacion.sector" class="form-control" placeholder="Ej: ENERGIA"></div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código resultado sectorial PES</label>
            <input [(ngModel)]="articulacion.codResultadoSectorial" class="form-control" placeholder="Ej: 5.1"></div>
          <div class="field"><label>Resultado sectorial</label>
            <textarea [(ngModel)]="articulacion.resultadoSectorial" class="form-control" rows="2"
                      placeholder="Ej: SE HA INCREMENTADO COBERTURA DE ENERGIA ELECTRICA A NIVEL NACIONAL"></textarea>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 2">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!articulacion.codSector" (click)="paso = 4">
            Siguiente → Territorial
          </button>
        </div>
      </div>

      <!-- PASO 4: ARTICULACIÓN TERRITORIAL -->
      <div *ngIf="paso === 4" class="step-content card">
        <h3>Paso 5: Articulación territorial — bisagra con el PAD</h3>
        <p>
          Registre el código del resultado territorial del PAD al que contribuyen este
          resultado institucional y sus productos. Es la columna que después permite cruzar
          la matriz PAD con la matriz PEI.
        </p>
        <div class="form-2col">
          <div class="field">
            <label>Resultado territorial del PAD</label>
            <select [(ngModel)]="resultadoPadSel" class="form-control" (change)="heredarDelPad()">
              <option value="">Sin vincular / captura manual</option>
              <option *ngFor="let r of resultadosPad" [value]="r.id">
                {{ r.codigo_resultado }} — {{ (r.denominacion || '') | slice:0:70 }}
              </option>
            </select>
          </div>
          <div class="field">
            <label>Código resultado territorial</label>
            <input [(ngModel)]="articulacion.codResultadoTerritorial" class="form-control" placeholder="Ej: 7.1.">
          </div>
        </div>
        <div class="nota" *ngIf="!articulacion.codResultadoTerritorial">
          Sin este código el PEI queda formulado, pero la articulación PAD → PEI no podrá
          construirse después.
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 3">← Anterior</button>
          <button class="btn btn-primary" (click)="paso = 5">Siguiente → Resultado institucional</button>
        </div>
      </div>

      <!-- PASO 5: SECCIÓN V -->
      <div *ngIf="paso === 5" class="step-content card">
        <h3>Paso 6: Sección V — Objetivo estratégico y resultado institucional</h3>
        <div class="form-2col">
          <div class="field"><label>Código objetivo estratégico institucional</label>
            <input [(ngModel)]="resultado.codOei" class="form-control" placeholder="Ej: OE 1."></div>
          <div class="field"><label>Correlativo del resultado</label>
            <input [(ngModel)]="resultado.correlativoResultado" type="number" min="1" class="form-control"></div>
        </div>
        <div class="field">
          <label>Objetivo estratégico institucional</label>
          <textarea [(ngModel)]="resultado.objetivoEstrategico" class="form-control" rows="2"
                    placeholder="Inicie con un verbo en infinitivo: Fortalecer, Consolidar, Contribuir…"></textarea>
          <small>Sin metas cuantitativas, porcentajes ni plazos: eso se expresa en el resultado y su indicador.</small>
        </div>

        <h4>Resultado institucional = acción de cambio + variable de resultado</h4>
        <div class="form-2col">
          <div class="field"><label>Acción de cambio (pretérito perfecto compuesto)</label>
            <select [(ngModel)]="resultado.accionCambio" class="form-control">
              <option value="">Seleccione...</option>
              <option *ngFor="let a of acciones" [value]="a">{{ a }}</option>
            </select>
          </div>
          <div class="field"><label>Variable de resultado</label>
            <input [(ngModel)]="resultado.variableResultado" class="form-control"
                   placeholder="el acceso de la población a servicios de salud especializados">
          </div>
        </div>
        <div class="preview-box">
          <span class="preview-cod">{{ codResultadoPei || 'ENT.1' }}</span>
          <span class="preview-txt">{{ resultadoRedactado || 'El resultado se irá redactando aquí…' }}</span>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 4">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!resultadoRedactado" (click)="paso = 6">
            Siguiente → Indicador
          </button>
        </div>
      </div>

      <!-- PASO 6: SECCIONES VI Y VII DEL RESULTADO -->
      <div *ngIf="paso === 6" class="step-content card">
        <h3>Paso 7: Secciones VI y VII — Indicador del resultado institucional</h3>
        <div class="field"><label>Indicador</label>
          <input [(ngModel)]="resultado.indicador.indicador" class="form-control"
                 placeholder="Ej: Número de familias beneficiadas con acceso a energía eléctrica"></div>
        <div class="form-3col">
          <div class="field"><label>Tipo de indicador</label>
            <input class="form-control" value="Resultado" readonly></div>
          <div class="field"><label>Unidad de medida</label>
            <input [(ngModel)]="resultado.indicador.unidadMedida" class="form-control" placeholder="Número / % / Tasa"></div>
          <div class="field"><label>Fórmula</label>
            <input [(ngModel)]="resultado.indicador.formula" class="form-control" placeholder="N/A o relación matemática"></div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Línea base</label>
            <input [(ngModel)]="resultado.indicador.lineaBase" type="number" class="form-control"></div>
          <div class="field"><label>Meta 2030</label>
            <input [(ngModel)]="resultado.indicador.meta2030" type="number" class="form-control"></div>
        </div>
        <h4>Programación física del resultado (metas acumulativas)</h4>
        <div class="prog-grid">
          <div *ngFor="let anio of gestiones" class="field">
            <label>{{ anio }}</label>
            <input [(ngModel)]="resultado.indicador.fisica[anio]" type="number" class="form-control">
          </div>
        </div>
        <div class="nota">
          El presupuesto de esta fila no se captura: la guía lo define como la sumatoria del
          presupuesto de los productos que componen el resultado.
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 5">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!resultado.indicador.indicador || !resultado.indicador.unidadMedida" (click)="paso = 7">
            Siguiente → Productos
          </button>
        </div>
      </div>

      <!-- PASO 7: PRODUCTOS INSTITUCIONALES -->
      <div *ngIf="paso === 7" class="step-content card">
        <h3>Paso 8: Productos institucionales</h3>
        <p>
          En el ciclo 2026-2030 se suprime la Acción de Mediano Plazo: el resultado se alcanza
          mediante productos institucionales, y cada uno se articula con un programa presupuestario.
        </p>
        <div class="inline-actions">
          <button class="btn btn-accent btn-sm" (click)="agregarProducto()">+ Agregar producto</button>
        </div>

        <div class="producto-card" *ngFor="let p of productos; let i = index">
          <div class="producto-head">
            <span class="codigo">{{ codigoDeProducto(i) }}</span>
            <span class="producto-nombre">{{ nombreDeProducto(p) || 'Producto sin redactar' }}</span>
            <button class="btn btn-sm btn-danger" (click)="quitarProducto(i)">Quitar</button>
          </div>

          <div class="form-2col">
            <div class="field"><label>Bien, servicio o norma</label>
              <input [(ngModel)]="p.bienServicio" class="form-control"
                     placeholder="Ej: Redes de electrificación"></div>
            <div class="field"><label>Condición de estado</label>
              <select [(ngModel)]="p.condicionEstado" class="form-control">
                <option value="">Seleccione...</option>
                <option *ngFor="let c of condiciones" [value]="c">{{ c }}</option>
              </select>
            </div>
          </div>
          <div class="form-3col">
            <div class="field"><label>Tipo de producto</label>
              <select [(ngModel)]="p.tipoProducto" class="form-control">
                <option *ngFor="let t of tiposProducto" [value]="t.valor">{{ t.etiqueta }}</option>
              </select>
            </div>
            <div class="field"><label>Código programa presupuestario</label>
              <input [(ngModel)]="p.codProgramaPresup" class="form-control" placeholder="Ej: 110"></div>
            <div class="field"><label>Descripción del programa</label>
              <input [(ngModel)]="p.programaPresup" class="form-control"
                     placeholder="Ej: DESARROLLO DE LA ELECTRIFICACIÓN"></div>
          </div>

          <h5>Indicador del producto</h5>
          <div class="field"><label>Indicador</label>
            <input [(ngModel)]="p.indicador.indicador" class="form-control"
                   placeholder="Ej: Número de kilómetros de red construidos"></div>
          <div class="form-3col">
            <div class="field"><label>Unidad de medida</label>
              <input [(ngModel)]="p.indicador.unidadMedida" class="form-control" placeholder="Número"></div>
            <div class="field"><label>Fórmula</label>
              <input [(ngModel)]="p.indicador.formula" class="form-control" placeholder="N/A"></div>
            <div class="field"><label>Línea base</label>
              <input [(ngModel)]="p.indicador.lineaBase" type="number" class="form-control"></div>
          </div>
          <div class="field meta-field"><label>Meta 2030</label>
            <input [(ngModel)]="p.indicador.meta2030" type="number" class="form-control"></div>

          <h5>Programación física por gestión (no acumulativa)</h5>
          <div class="prog-grid">
            <div *ngFor="let anio of gestiones" class="field">
              <label>{{ anio }}</label>
              <input [(ngModel)]="p.indicador.fisica[anio]" type="number" class="form-control">
            </div>
          </div>

          <h5>Programación financiera — gasto de inversión (Bs)</h5>
          <div class="prog-grid">
            <div *ngFor="let anio of gestiones" class="field">
              <label>{{ anio }}</label>
              <input [(ngModel)]="p.indicador.inversion[anio]" type="number" class="form-control">
            </div>
          </div>

          <h5>Programación financiera — gasto corriente (Bs)</h5>
          <div class="prog-grid">
            <div *ngFor="let anio of gestiones" class="field">
              <label>{{ anio }}</label>
              <input [(ngModel)]="p.indicador.corriente[anio]" type="number" class="form-control">
            </div>
          </div>

          <div class="producto-totales">
            <span>Inversión: <strong>{{ moneda(totalesDe(p).inversionTotal) }}</strong></span>
            <span>Corriente: <strong>{{ moneda(totalesDe(p).corrienteTotal) }}</strong></span>
            <span>Total quinquenal: <strong>{{ moneda(totalesDe(p).presupuestoTotal) }}</strong></span>
          </div>
        </div>

        <div class="vacio-productos" *ngIf="!productos.length">
          Sin productos no hay matriz: agregue al menos uno.
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 6">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!productos.length" (click)="paso = 8">
            Siguiente → Revisión
          </button>
        </div>
      </div>

      <!-- PASO 8: REVISIÓN Y GUARDADO -->
      <div *ngIf="paso === 8" class="step-content card">
        <h3>Paso 9: Revisión y registro del PEI</h3>
        <div class="resumen-grid">
          <div class="resumen-item"><span>Entidad</span><strong>{{ resultado.codEntidad }} — {{ resultado.entidad || '-' }}</strong></div>
          <div class="resumen-item"><span>Resultado PEI</span><strong>{{ codResultadoPei || '-' }}</strong></div>
          <div class="resumen-item"><span>Resultado territorial PAD</span><strong>{{ articulacion.codResultadoTerritorial || 'sin vincular' }}</strong></div>
          <div class="resumen-item"><span>Productos</span><strong>{{ productos.length }}</strong></div>
          <div class="resumen-item"><span>Presupuesto quinquenal</span><strong>{{ moneda(presupuestoQuinquenal) }} Bs</strong></div>
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
          <button class="btn btn-outline" (click)="paso = 7">← Anterior</button>
          <button class="btn btn-success" [disabled]="bloqueado || guardando" (click)="guardar()">
            {{ guardando ? 'Guardando…' : '✓ Registrar matriz PEI' }}
          </button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass === 'error'"
             [class.exito]="msgClass === 'exito'">{{ msg }}</div>
      </div>

        </div>

        <app-control-metodologico [hallazgos]="hallazgos"
                                  fuente="Guía Metodológica PEI 2026-2030">
        </app-control-metodologico>
      </div>

      <app-pei-matriz-viewer [filas]="filas" [hallazgos]="hallazgos"></app-pei-matriz-viewer>
    </div>
  `,
  styles: [`
    .pei-full { max-width: 1200px; margin: 0 auto; padding-bottom: 2rem; }
    .migas { font-size: 0.6875rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: flex; gap: 0.4rem; align-items: center; }
    .migas a { color: var(--primary); text-decoration: none; font-weight: 600; }
    .migas a:hover { text-decoration: underline; }
    .aviso-edicion { margin: 0.5rem 0 0; padding: 0.55rem 0.75rem; background: #FFF8E1; color: #8A6100; border-radius: 6px; font-size: 0.75rem; }
    .pei-header h1 { font-size: 1.35rem; color: var(--primary); }
    .pei-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1rem; }

    .progress-bar-horizontal { display: flex; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
    .progress-step { flex: 1; text-align: center; padding: 0.5rem 0.25rem; cursor: pointer; position: relative; min-width: 70px; }
    .progress-step::after { content: ''; position: absolute; top: 50%; right: -50%; width: 100%; height: 2px; background: var(--border); z-index: 0; }
    .progress-step:last-child::after { display: none; }
    .step-circle { width: 28px; height: 28px; border-radius: 50%; margin: 0 auto 0.25rem; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; background: var(--border); color: var(--text-secondary); position: relative; z-index: 1; }
    .progress-step.active .step-circle { background: var(--primary); color: #fff; }
    .progress-step.completed .step-circle { background: var(--success); color: #fff; }
    .step-label { font-weight: 700; font-size: 0.6875rem; }

    .wizard-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 1.25rem; align-items: start; }
    .wizard-main { min-width: 0; }
    @media (max-width: 1100px) { .wizard-layout { grid-template-columns: 1fr; } }

    .step-content { padding: 1.5rem; min-height: 300px; }
    .step-content h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
    .step-content h4 { font-size: 0.9rem; margin: 1rem 0 0.5rem; color: var(--text-secondary); }
    .step-content h5 { font-size: 0.8125rem; margin: 0.75rem 0 0.4rem; color: var(--primary); }
    .step-content p { color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 0.8125rem; }
    .step-content code { background: var(--border); padding: 0 0.25rem; border-radius: 3px; font-size: 0.75rem; }

    .select-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem; }
    .select-card { padding: 0.75rem; border: 2px solid var(--border); border-radius: 6px; cursor: pointer; }
    .select-card:hover { border-color: var(--primary); background: #F0F7F3; }
    .select-card.selected { border-color: var(--primary); background: #E8F5E9; }
    .card-cod { font-weight: 800; font-size: 0.7rem; color: var(--primary); }
    .card-nombre { font-size: 0.8125rem; font-weight: 600; }
    .card-desc { font-size: 0.6875rem; color: var(--text-secondary); margin-top: 0.25rem; }

    .form-2col, .form-3col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; }
    .form-2col { grid-template-columns: 1fr 1fr; }
    .form-3col { grid-template-columns: 1fr 1fr 1fr; }
    .field { margin-bottom: 0.5rem; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.2rem; }
    .field small { font-size: 0.625rem; color: var(--text-secondary); }
    .meta-field { max-width: 220px; }
    .inline-actions { margin-bottom: 0.75rem; }
    .step-nav { display: flex; justify-content: space-between; margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }

    .bifurcacion { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .bif-card { padding: 1rem; border: 2px dashed var(--border); border-radius: 8px; cursor: pointer; }
    .bif-card:hover { border-color: var(--primary); background: #F0F7F3; }
    .bif-card.selected { border-style: solid; border-color: var(--primary); background: #E8F5E9; }
    .bif-card h4 { font-size: 0.875rem; margin-top: 0; }
    .bif-card p { font-size: 0.75rem; }
    .bif-card select { font-size: 0.75rem; margin-bottom: 0.5rem; }

    .prog-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; }
    .prog-grid input { font-size: 0.75rem; padding: 0.25rem 0.375rem; }

    .preview-box { margin-top: 0.75rem; padding: 0.75rem; background: #E8F5E9; border-left: 4px solid var(--primary); border-radius: 4px; }
    .preview-cod { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); margin-right: 0.5rem; }
    .preview-txt { font-size: 0.8125rem; }

    .producto-card { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .producto-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .producto-head .codigo { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); }
    .producto-nombre { flex: 1; font-size: 0.8125rem; font-weight: 600; }
    .producto-totales { display: flex; gap: 1.25rem; margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px dashed var(--border); font-size: 0.75rem; color: var(--text-secondary); }
    .vacio-productos { padding: 1.5rem; text-align: center; color: var(--text-secondary); font-size: 0.8125rem; border: 1px dashed var(--border); border-radius: 8px; }

    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .resumen-item { padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
    .resumen-item span { display: block; font-size: 0.6875rem; color: var(--text-secondary); }
    .resumen-item strong { font-size: 0.8125rem; }

    .hallazgos ul { list-style: none; padding: 0; margin: 0; }
    .hallazgos li { padding: 0.4rem 0.6rem; border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.75rem; }
    .hallazgos li.error { background: #FFEBEE; color: var(--warn); }
    .hallazgos li.aviso { background: #FFF8E1; color: #8A6100; }

    .nota { margin-top: 0.75rem; padding: 0.6rem 0.75rem; background: #FFF8E1; color: #8A6100; border-radius: 6px; font-size: 0.75rem; }
    .msg-box { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .msg-box.error { background: #FFEBEE; color: var(--warn); }
    .msg-box.exito { background: #E8F5E9; color: var(--success); }
    .btn-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); border-radius: 4px; cursor: pointer; padding: 0.2rem 0.5rem; font-size: 0.6875rem; }

    @media (max-width: 768px) {
      .form-2col, .form-3col, .prog-grid, .bifurcacion { grid-template-columns: 1fr; }
    }
  `],
})
export class PeiWizardComponent implements OnInit {
  paso = 0;
  pasos = [
    'Entidad', 'Nacional', 'Acuerdos', 'Sector', 'Territorial',
    'Resultado', 'Indicador', 'Productos', 'Registro',
  ];

  gestiones = GESTIONES_PEI;
  ejes = EJES_PGDESA;
  ods = CATALOGO_ODS;
  acciones = ACCIONES_DE_CAMBIO;
  condiciones = CONDICIONES_DE_ESTADO;
  tiposProducto = TIPOS_PRODUCTO;

  articulacion: ArticulacionPei = articulacionVacia();
  resultado: ResultadoPeiForm = resultadoVacio();
  productos: ProductoPeiForm[] = [productoVacio()];

  origen: 'pad' | 'cero' = 'cero';
  resultadosPad: any[] = [];
  acuerdos: any[] = [];
  resultadoPadSel = '';
  sectores: any[] = [];

  guardando = false;
  msg = '';
  msgClass = '';

  /** Borrador en edición; vacío cuando es un registro nuevo. */
  borradorId: string | null = null;
  cargandoBorrador = false;

  constructor(
    private api: ApiService,
    private borradores: PeiBorradoresService,
    private ruta: ActivatedRoute,
    private cdr: ChangeDetectorRef,
  ) {}

  get modoEdicion(): boolean { return !!this.borradorId; }

  ngOnInit(): void {
    this.cargarResultadosPad();
    this.cargarSectores();
    this.cargarAcuerdos();

    const id = this.ruta.snapshot.paramMap.get('id');
    if (id) { this.borradorId = id; this.cargarBorrador(id); }
  }

  // --- Derivados ------------------------------------------------------------

  get ejeActual(): EjePgdesa | undefined {
    return this.ejes.find(e => e.codigo === this.articulacion.codEjePgdesa);
  }

  get codResultadoPei(): string {
    return codigoResultado(this.resultado.codEntidad, this.resultado.correlativoResultado);
  }

  get resultadoRedactado(): string {
    return redactarResultado(this.resultado.accionCambio, this.resultado.variableResultado);
  }

  get filas(): FilaMatrizPei[] {
    return construirFilas(this.articulacion, this.resultado, this.productos);
  }

  get hallazgos(): Hallazgo[] {
    return validarMatriz(this.articulacion, this.resultado, this.productos);
  }

  get bloqueado(): boolean {
    return tieneErrores(this.hallazgos);
  }

  get presupuestoQuinquenal(): number {
    return this.productos.reduce(
      (total, p) => total + totalIndicador(p.indicador).presupuestoTotal,
      0,
    );
  }

  // --- Navegación y selección ----------------------------------------------

  irAPaso(p: number): void {
    if (p <= this.paso) this.paso = p;
  }

  selEje(eje: EjePgdesa): void {
    this.articulacion.codEjePgdesa = eje.codigo;
    this.articulacion.objetivoImpacto = eje.objetivoImpacto;
    this.articulacion.codComponentePdesa = '';
    this.articulacion.objetivoEfecto = '';
  }

  selComponente(componente: ComponentePdesa): void {
    this.articulacion.codComponentePdesa = componente.codigo;
    this.articulacion.objetivoEfecto = componente.objetivoEfecto;
  }

  onSectorChange(): void {
    const sector = this.sectores.find(s => String(s.codigo) === String(this.articulacion.codSector));
    if (sector) {
      this.articulacion.sector = sector.nombre;
      if (!this.articulacion.codResultadoSectorial) {
        this.articulacion.codResultadoSectorial = `${sector.codigo}.1`;
      }
    }
  }

  /** Hereda las secciones I a IV y el código territorial del resultado PAD elegido. */
  heredarDelPad(): void {
    const origen = this.resultadosPad.find(r => r.id === this.resultadoPadSel);
    if (!origen) {
      this.articulacion.resultadoPadId = null;
      return;
    }
    this.articulacion.resultadoPadId = origen.id;
    this.articulacion.codResultadoTerritorial = origen.codigo_resultado || '';
    this.articulacion.codEjePgdesa = origen.cod_eje_pgdesa || this.articulacion.codEjePgdesa;
    this.articulacion.objetivoImpacto = origen.objetivo_impacto || this.articulacion.objetivoImpacto;
    this.articulacion.codComponentePdesa =
      origen.cod_componente_pdesa || this.articulacion.codComponentePdesa;
    this.articulacion.objetivoEfecto = origen.objetivo_efecto || this.articulacion.objetivoEfecto;
    this.articulacion.codSector = origen.cod_sector || this.articulacion.codSector;
    this.articulacion.sector = origen.sector || this.articulacion.sector;
    this.articulacion.codResultadoSectorial =
      origen.cod_resultado_pds || this.articulacion.codResultadoSectorial;
    this.articulacion.resultadoSectorial =
      origen.resultado_pds || this.articulacion.resultadoSectorial;
  }

  // --- Productos ------------------------------------------------------------

  agregarProducto(): void {
    this.productos.push(productoVacio());
  }

  quitarProducto(indice: number): void {
    this.productos.splice(indice, 1);
  }

  codigoDeProducto(indice: number): string {
    return codigoProducto(this.codResultadoPei, indice) || `PROD.${indice + 1}`;
  }

  nombreDeProducto(producto: ProductoPeiForm): string {
    return redactarProducto(producto.bienServicio, producto.condicionEstado);
  }

  totalesDe(producto: ProductoPeiForm): {
    inversionTotal: number;
    corrienteTotal: number;
    presupuestoTotal: number;
  } {
    return totalIndicador(producto.indicador);
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '0';
  }

  // --- Persistencia ---------------------------------------------------------

  /** Secciones del borrador, en el orden que espera el backend. */
  private secciones(): [string, unknown][] {
    return [
      ['s1_nacional', {
        eje: { codigo: this.articulacion.codEjePgdesa },
        componente: { codigo: this.articulacion.codComponentePdesa },
        objetivo_impacto: this.articulacion.objetivoImpacto,
        objetivo_efecto: this.articulacion.objetivoEfecto,
      }],
      ['s2_acuerdos', {
        ods: this.articulacion.codOds,
        ndc: this.articulacion.codNdc,
        ndt: this.articulacion.codNdt,
        kmgbf: this.articulacion.codMeta3030,
      }],
      ['s3_sector', {
        sector: {
          codigo: this.articulacion.codSector,
          denominacion: this.articulacion.sector,
        },
        resultado_sectorial: {
          codigo: this.articulacion.codResultadoSectorial,
          denominacion: this.articulacion.resultadoSectorial,
        },
      }],
      ['s4_territorial', {
        cod_resultado_territorial: this.articulacion.codResultadoTerritorial,
        resultado_pad: this.articulacion.resultadoPadId,
      }],
      ['s5_institucional', {
        cod_entidad: this.resultado.codEntidad,
        entidad: this.resultado.entidad,
        cod_oei: this.resultado.codOei,
        objetivo_estrategico: this.resultado.objetivoEstrategico,
        vigencia_desde: Number(this.resultado.vigenciaDesde),
        vigencia_hasta: Number(this.resultado.vigenciaHasta),
      }],
      ['resultados', [{
        correlativo: this.resultado.correlativoResultado,
        accion_cambio: this.resultado.accionCambio,
        variable_resultado: this.resultado.variableResultado,
        denominacion: this.resultadoRedactado,
        indicador: this.indicadorPayload(this.resultado.indicador),
        programacion_fisica: this.resultado.indicador.fisica,
        productos: this.productos.map(p => ({
          denominacion: redactarProducto(p.bienServicio, p.condicionEstado),
          bien_servicio: p.bienServicio,
          condicion_estado: p.condicionEstado,
          tipo_producto: p.tipoProducto,
          cod_programa_presup: p.codProgramaPresup,
          programa_presup: p.programaPresup,
          indicador: this.indicadorPayload(p.indicador),
          programacion_fisica: p.indicador.fisica,
          inversion: p.indicador.inversion,
          corriente: p.indicador.corriente,
        })),
      }]],
    ];
  }

  private indicadorPayload(indicador: any): Record<string, unknown> {
    return {
      indicador: indicador.indicador,
      tipo_indicador: indicador.tipoIndicador,
      unidad_medida: indicador.unidadMedida,
      formula: indicador.formula,
      linea_base: indicador.lineaBase,
      meta_2030: indicador.meta2030,
    };
  }

  /**
   * Guarda sección por sección sobre el borrador y lo materializa. Un borrador
   * ya materializado no se recrea: el backend lo rechaza.
   */
  guardar(): void {
    if (this.bloqueado || this.guardando) return;
    this.guardando = true;
    this.msg = this.modoEdicion ? 'Guardando cambios…' : 'Registrando la matriz PEI…';
    this.msgClass = '';

    const origen = this.modoEdicion
      ? this.borradores.obtener(this.borradorId as string)
      : this.borradores.crear({ gestion: Number(this.resultado.vigenciaDesde) });

    origen.pipe(
      switchMap((borrador: any) =>
        from(this.secciones()).pipe(
          concatMap(([seccion, valores]) =>
            this.borradores.guardarSeccion(borrador.id, seccion, valores),
          ),
          toArray(),
          switchMap(() =>
            borrador.estado === 'COMPLETO'
              ? of({ materializado: false })
              : this.borradores.materializar(borrador.id),
          ),
          map((resultado: any) => ({ resultado, borrador })),
        ),
      ),
    ).subscribe({
      next: ({ resultado, borrador }: any) => {
        this.guardando = false;
        this.borradorId = borrador.id;
        this.msgClass = 'exito';
        this.msg = resultado?.materializado === false
          ? `✅ Registro actualizado: ${this.productos.length} producto(s). Los registros operativos ya materializados no se recrean.`
          : `✅ Matriz PEI registrada: resultado ${this.codResultadoPei} con ${this.productos.length} producto(s).`;
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

  /** Rehidrata el asistente con las secciones guardadas del borrador. */
  private cargarBorrador(id: string): void {
    this.cargandoBorrador = true;
    this.borradores.obtener(id).subscribe({
      next: (borrador: any) => {
        const datos = borrador?.datos || {};

        const nacional = datos.s1_nacional || {};
        this.articulacion.codEjePgdesa = nacional?.eje?.codigo || '';
        this.articulacion.objetivoImpacto = nacional.objetivo_impacto || '';
        this.articulacion.codComponentePdesa = nacional?.componente?.codigo || '';
        this.articulacion.objetivoEfecto = nacional.objetivo_efecto || '';

        const acuerdos = datos.s2_acuerdos || {};
        this.articulacion.codOds = acuerdos.ods || '';
        this.articulacion.codNdc = acuerdos.ndc || 'N/A';
        this.articulacion.codNdt = acuerdos.ndt || 'N/A';
        this.articulacion.codMeta3030 = acuerdos.kmgbf || 'N/A';

        const sector = datos.s3_sector || {};
        this.articulacion.codSector = sector?.sector?.codigo || '';
        this.articulacion.sector = sector?.sector?.denominacion || '';
        this.articulacion.codResultadoSectorial = sector?.resultado_sectorial?.codigo || '';
        this.articulacion.resultadoSectorial = sector?.resultado_sectorial?.denominacion || '';

        const territorial = datos.s4_territorial || {};
        this.articulacion.codResultadoTerritorial = territorial.cod_resultado_territorial || '';
        this.articulacion.resultadoPadId = territorial.resultado_pad || null;

        const institucional = datos.s5_institucional || {};
        this.resultado.codEntidad = institucional.cod_entidad || '';
        this.resultado.entidad = institucional.entidad || '';
        this.resultado.codOei = institucional.cod_oei || this.resultado.codOei;
        this.resultado.objetivoEstrategico = institucional.objetivo_estrategico || '';
        this.resultado.vigenciaDesde = institucional.vigencia_desde || this.resultado.vigenciaDesde;
        this.resultado.vigenciaHasta = institucional.vigencia_hasta || this.resultado.vigenciaHasta;

        const lista = Array.isArray(datos.resultados) ? datos.resultados : [];
        const primero = lista[0];
        if (primero) {
          this.resultado.correlativoResultado = primero.correlativo || 1;
          this.resultado.accionCambio = primero.accion_cambio || '';
          this.resultado.variableResultado = primero.variable_resultado || '';
          this.resultado.indicador = this.hidratarIndicador(
            primero.indicador, 'Resultado', primero.programacion_fisica,
          );
          this.productos = (primero.productos || []).map((p: any) => ({
            codigoProducto: '',
            denominacion: p.denominacion || '',
            bienServicio: p.bien_servicio || '',
            condicionEstado: p.condicion_estado || '',
            tipoProducto: p.tipo_producto || 'TERMINAL',
            codProgramaPresup: p.cod_programa_presup || '',
            programaPresup: p.programa_presup || '',
            indicador: this.hidratarIndicador(
              p.indicador, 'Producto', p.programacion_fisica, p.inversion, p.corriente,
            ),
          }));
        }

        this.cargandoBorrador = false;
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

  private hidratarProgramacion(origen: any): Record<string, number | null> {
    const destino: Record<string, number | null> = {};
    for (const anio of this.gestiones) {
      const valor = (origen || {})[anio];
      destino[anio] = valor === undefined || valor === null ? null : Number(valor);
    }
    return destino;
  }

  private hidratarIndicador(
    origen: any, tipo: 'Resultado' | 'Producto',
    fisica?: any, inversion?: any, corriente?: any,
  ): any {
    const i = origen || {};
    return {
      indicador: i.indicador || '',
      tipoIndicador: tipo,
      unidadMedida: i.unidad_medida || '',
      formula: i.formula || 'N/A',
      lineaBase: i.linea_base ?? null,
      meta2030: i.meta_2030 ?? null,
      fisica: this.hidratarProgramacion(fisica),
      inversion: this.hidratarProgramacion(inversion),
      corriente: this.hidratarProgramacion(corriente),
    };
  }

  private cuerpoResultado(): Record<string, unknown> {
    return {
      codigo_resultado: this.codResultadoPei,
      denominacion: this.resultadoRedactado,
      cod_entidad: this.resultado.codEntidad,
      entidad: this.resultado.entidad,
      cod_oei: this.resultado.codOei,
      objetivo_estrategico: this.resultado.objetivoEstrategico,
      vigencia_desde: Number(this.resultado.vigenciaDesde),
      vigencia_hasta: Number(this.resultado.vigenciaHasta),
      cod_eje_pgdesa: this.articulacion.codEjePgdesa,
      objetivo_impacto: this.articulacion.objetivoImpacto,
      cod_componente_pdesa: this.articulacion.codComponentePdesa,
      objetivo_efecto: this.articulacion.objetivoEfecto,
      cod_ods: this.articulacion.codOds,
      cod_ndc: this.articulacion.codNdc,
      cod_ndt: this.articulacion.codNdt,
      cod_meta_3030: this.articulacion.codMeta3030,
      cod_sector: this.articulacion.codSector,
      sector: this.articulacion.sector,
      cod_resultado_sectorial: this.articulacion.codResultadoSectorial,
      resultado_sectorial: this.articulacion.resultadoSectorial,
      cod_resultado_territorial: this.articulacion.codResultadoTerritorial,
      resultado_pad: this.articulacion.resultadoPadId,
    };
  }

  private cuerpoProducto(
    resultadoId: string,
    producto: ProductoPeiForm,
    indice: number,
  ): Record<string, unknown> {
    return {
      codigo_producto: this.codigoDeProducto(indice),
      denominacion: this.nombreDeProducto(producto),
      resultado_pei: resultadoId,
      tipo_producto: producto.tipoProducto,
      cod_programa_presup: producto.codProgramaPresup,
      programa_presup: producto.programaPresup,
    };
  }

  private cuerpoIndicadorResultado(resultadoId: string): Record<string, unknown> {
    const consolidado = this.filas[0];
    return {
      nivel_indicador: 'resultado_pei',
      resultado_pei: resultadoId,
      indicador: this.resultado.indicador.indicador,
      tipo_indicador: 'Resultado',
      unidad_medida: this.resultado.indicador.unidadMedida,
      formula: this.resultado.indicador.formula,
      linea_base: this.resultado.indicador.lineaBase,
      meta_2030: this.resultado.indicador.meta2030,
      programacion_fisica: this.resultado.indicador.fisica,
      presupuesto_inversion_total: consolidado.inversionTotal,
      presupuesto_corriente_total: consolidado.corrienteTotal,
      ...this.montosPorGestion(consolidado.inversion, consolidado.corriente),
    };
  }

  private cuerpoIndicadorProducto(
    productoId: string,
    producto: ProductoPeiForm,
  ): Record<string, unknown> {
    const totales = totalIndicador(producto.indicador);
    return {
      nivel_indicador: 'producto_pei',
      producto_pei: productoId,
      indicador: producto.indicador.indicador,
      tipo_indicador: 'Producto',
      unidad_medida: producto.indicador.unidadMedida,
      formula: producto.indicador.formula,
      linea_base: producto.indicador.lineaBase,
      meta_2030: producto.indicador.meta2030,
      programacion_fisica: producto.indicador.fisica,
      presupuesto_inversion_total: totales.inversionTotal,
      presupuesto_corriente_total: totales.corrienteTotal,
      ...this.montosPorGestion(producto.indicador.inversion, producto.indicador.corriente),
    };
  }

  private montosPorGestion(
    inversion: Record<string, number | null>,
    corriente: Record<string, number | null>,
  ): Record<string, number> {
    const montos: Record<string, number> = {};
    for (const anio of this.gestiones) {
      montos[`inversion_${anio}`] = Number(inversion[anio]) || 0;
      montos[`corriente_${anio}`] = Number(corriente[anio]) || 0;
    }
    return montos;
  }

  private detalleError(err: any): string {
    const cuerpo = err?.error ?? err;
    if (cuerpo && typeof cuerpo === 'object') {
      const detalles = Object.entries(cuerpo)
        .map(([campo, valor]) => `${campo}: ${Array.isArray(valor) ? valor.join(', ') : valor}`);
      if (detalles.length) return detalles.join(' · ');
    }
    return err?.message || 'No se pudo registrar la matriz PEI.';
  }

  // --- Carga de catálogos ---------------------------------------------------


  /**
   * Catálogo maestro de acuerdos internacionales. La API pagina de a 25 y no
   * acepta `page_size`, así que hay que recorrer las páginas.
   */
  private cargarAcuerdos(pagina = 1, acumulado: any[] = []): void {
    this.api.get<any>('/articulacion/acuerdos/', { page: pagina, activo: true }).subscribe({
      next: (r: any) => {
        const lote = r?.results || (Array.isArray(r) ? r : []);
        const total = [...acumulado, ...lote];
        if (r?.next) {
          this.cargarAcuerdos(pagina + 1, total);
        } else {
          this.acuerdos = total;
          this.cdr.markForCheck();
        }
      },
      error: () => { this.acuerdos = acumulado; this.cdr.markForCheck(); },
    });
  }

  private porTipo(tipo: string): any[] {
    return this.acuerdos
      .filter(a => a.tipo_acuerdo === tipo)
      .sort((a, b) => String(a.codigo).localeCompare(String(b.codigo), 'es', { numeric: true }));
  }

  get catalogoOds(): any[] { return this.porTipo('ODS'); }
  get catalogoNdc(): any[] { return this.porTipo('NDC'); }
  get catalogoNdt(): any[] { return this.porTipo('NDT'); }
  get catalogo3030(): any[] { return this.porTipo('COMPROMISO_3030'); }

  private cargarResultadosPad(): void {
    this.api.get<any>('/articulacion/resultados-pad/').subscribe({
      next: (r: any) => { this.resultadosPad = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.resultadosPad = [];         this.cdr.markForCheck();
      },
    });
  }

  private cargarSectores(): void {
    this.api.get<any>('/pad/sectores-pad/').subscribe({
      next: (r: any) => { this.sectores = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.sectores = [];         this.cdr.markForCheck();
      },
    });
  }
}
