import {
  Component,
  Input,
  Output,
  EventEmitter,
  ChangeDetectorRef,
} from '@angular/core';

export interface IndicadorDraft {
  indicador: string;
  formula: string;
  unidad_medida: string;
  linea_base: number | null;
  meta_2030: number | null;
}

export interface ProductoDraft {
  denominacion: string;
  territorializacion: string;
  responsable: string;
  cuenta_con_financiamiento: boolean;
  indicador: IndicadorDraft;
  programacion_fisica: Record<string, number | null>;
  presupuesto_total: number | null;
  presupuesto_anual: Record<string, number | null>;
}

export interface ResultadoDraft {
  denominacion: string;
  territorializacion: string;
  responsable: string;
  cuenta_con_financiamiento: boolean;
  indicador: IndicadorDraft;
  programacion_fisica: Record<string, number | null>;
  presupuesto_total: number | null;
  presupuesto_anual: Record<string, number | null>;
  productos: ProductoDraft[];
}

/**
 * Tabla jerárquica expandible con edición INLINE (vista de captura del paso 6).
 *
 * Cada resultado PAD es una fila padre expandible (▼/▶) y sus productos son
 * filas hijas indentadas, en un formato tipo Excel con cabecera fija:
 *   Código | Resultado/Producto | Territorialización | Responsable | Financ. | Acciones
 *
 * - Los códigos compuestos se autogeneran EN VIVO y son readonly:
 *     resultado = CGEO.lineamiento.(correlativoBase + i)
 *     producto  = CGEO.lineamiento.resultado.(j + 1)
 * - Cualquier cambio (campo, agregar, eliminar, duplicar) emite ``cambio``;
 *   el padre (wizard) responde con el PATCH de la sección "resultados"
 *   (lista completa, guardado incremental).
 * - La colección se muta por referencia (la misma que mantiene el wizard),
 *   de modo que los pasos 8-10 (indicadores/financiera) siguen operando sobre
 *   la misma ``resultados``.
 * - Validación visual: la fila queda marcada si falta la denominación.
 */
@Component({
  selector: 'app-tabla-jerarquica',
  standalone: false,
  template: `
    <div class="tj-scroll">
      <div class="tj-grid tj-header">
        <div class="tj-col col-codigo">Código</div>
        <div class="tj-col col-desc">Resultado / Producto</div>
        <div class="tj-col col-terr">Territorialización</div>
        <div class="tj-col col-resp">Responsable</div>
        <div class="tj-col col-fin">Financ.</div>
        <div class="tj-col col-acciones">Acciones</div>
      </div>
    
      <div class="tj-body">
        @for (res of resultados; track res; let i = $index) {
          <!-- ===== Fila padre: Resultado ===== -->
          <div class="tj-grid tj-row fila-resultado"
            [class.fila-incompleta]="tieneFaltaDenominacion(res)">
            <div class="tj-col col-codigo">
              <button type="button" class="btn-toggle"
                [attr.aria-label]="expandido(i) ? 'Contraer' : 'Expandir'"
                (click)="toggle(i)">
                {{ expandido(i) ? '▼' : '▶' }}
              </button>
              <span class="codigo" [title]="codigoResultado(i)">{{ codigoResultado(i) || '—' }}</span>
            </div>
            <div class="tj-col col-desc">
              <input class="form-control tj-input"
                [(ngModel)]="res.denominacion"
                (ngModelChange)="onCampoCambio()"
                placeholder="Denominación del resultado PAD">
              </div>
              <div class="tj-col col-terr">
                <input class="form-control tj-input"
                  [(ngModel)]="res.territorializacion"
                  (ngModelChange)="onCampoCambio()"
                  placeholder="Ej: COMUNIDAD 1, DISTRITO 4,5">
                </div>
                <div class="tj-col col-resp">
                  <input class="form-control tj-input"
                    [(ngModel)]="res.responsable"
                    (ngModelChange)="onCampoCambio()"
                    placeholder="Entidad responsable">
                  </div>
                  <div class="tj-col col-fin">
                    <label class="check-fin" [class.check-on]="res.cuenta_con_financiamiento">
                      <input type="checkbox"
                        [(ngModel)]="res.cuenta_con_financiamiento"
                        (ngModelChange)="onCampoCambio()">
                        <span>SÍ</span>
                      </label>
                    </div>
                    <div class="tj-col col-acciones">
                      <button type="button" class="btn btn-sm btn-primary"
                      (click)="agregarProducto(i)">+ Producto</button>
                      <button type="button" class="btn btn-sm btn-outline"
                      (click)="duplicarResultado(i)">Duplicar</button>
                      <button type="button" class="btn btn-sm btn-outline-danger"
                        (click)="eliminarResultado(i)"
                      [disabled]="resultados.length <= 1">Eliminar</button>
                    </div>
                  </div>
                  <!-- ===== Filas hijas: Productos ===== -->
                  @if (expandido(i)) {
                    @for (prod of res.productos; track prod; let j = $index) {
                      <div class="tj-grid tj-row fila-producto"
                        [class.fila-incompleta]="tieneFaltaDenominacion(prod)"
                        >
                        <div class="tj-col col-codigo">
                          <span class="codigo child" [title]="codigoProducto(i, j)">{{ codigoProducto(i, j) || '—' }}</span>
                        </div>
                        <div class="tj-col col-desc">
                          <input class="form-control tj-input"
                            [(ngModel)]="prod.denominacion"
                            (ngModelChange)="onCampoCambio()"
                            placeholder="Bien, servicio o intervención (producto PAD)">
                          </div>
                          <div class="tj-col col-terr">
                            <input class="form-control tj-input"
                              [(ngModel)]="prod.territorializacion"
                              (ngModelChange)="onCampoCambio()"
                              placeholder="Ej: COMUNIDAD 1, DISTRITO 4,5">
                            </div>
                            <div class="tj-col col-resp">
                              <input class="form-control tj-input"
                                [(ngModel)]="prod.responsable"
                                (ngModelChange)="onCampoCambio()"
                                placeholder="Entidad responsable">
                              </div>
                              <div class="tj-col col-fin">
                                <label class="check-fin" [class.check-on]="prod.cuenta_con_financiamiento">
                                  <input type="checkbox"
                                    [(ngModel)]="prod.cuenta_con_financiamiento"
                                    (ngModelChange)="onCampoCambio()">
                                    <span>SÍ</span>
                                  </label>
                                </div>
                                <div class="tj-col col-acciones">
                                  <button type="button" class="btn btn-sm btn-outline"
                                  (click)="duplicarProducto(i, j)">Duplicar</button>
                                  <button type="button" class="btn btn-sm btn-outline-danger"
                                    (click)="eliminarProducto(i, j)"
                                  [disabled]="res.productos.length <= 1">Eliminar</button>
                                </div>
                              </div>
                            }
                          }
                        }
    
                        <!-- Fila final: agregar resultado (tipo Excel) -->
                        <div class="tj-grid tj-row tj-row-add">
                          <div class="tj-col tj-add-cell">
                            <button type="button" class="btn btn-sm btn-primary" (click)="agregarResultado()">
                              + Agregar Resultado
                            </button>
                          </div>
                          <div class="tj-col tj-add-hint">
                            Los códigos se actualizan en vivo al agregar o eliminar filas.
                          </div>
                        </div>
                      </div>
                    </div>
    
                    @if (resultados.length) {
                      <div class="tj-resumen">
                        Total: {{ resultados.length }} resultado(s), {{ totalProductos() }} producto(s)
                        → {{ totalFilas() }} fila(s) en la matriz.
                      </div>
                    }
    `,
  styles: [`
    .tj-scroll { overflow-x: auto; max-height: 62vh; overflow-y: auto; border: 1px solid var(--border); border-radius: 8px; background: #fff; }
    .tj-grid { display: grid; grid-template-columns: minmax(150px, 200px) minmax(260px, 1fr) minmax(140px, 180px) minmax(140px, 180px) 84px minmax(240px, auto); min-width: 940px; }
    .tj-header { position: sticky; top: 0; z-index: 3; background: var(--bg); border-bottom: 2px solid var(--border); }
    .tj-header .tj-col { font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-secondary); font-weight: 700; }
    .tj-row { border-bottom: 1px solid var(--border); }
    .tj-row:last-child { border-bottom: none; }
    .tj-col { padding: 0.375rem 0.5rem; display: flex; align-items: center; gap: 0.25rem; min-width: 0; }
    .tj-header .tj-col { padding-top: 0.5rem; padding-bottom: 0.5rem; }

    .fila-resultado { background: #fff; }
    .fila-resultado:hover { background: #F4F9F4; }
    .fila-producto { background: #FAFBFC; box-shadow: inset 3px 0 0 #B0BEC5; }
    .fila-producto:hover { background: #F1F5F8; }

    .tj-input { height: 30px; font-size: 0.75rem; padding: 0.25rem 0.5rem; width: 100%; }
    .tj-input:focus { border-color: var(--primary); }

    .btn-toggle { background: none; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; font-size: 0.625rem; line-height: 1; padding: 0.25rem 0.3rem; color: var(--primary-dark); flex: none; }
    .btn-toggle:hover { background: #E8F5E9; }

    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; font-size: 0.75rem; }
    .codigo.child { color: #00695C; }

    .check-fin { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.75rem; color: var(--text-secondary); cursor: pointer; }
    .check-fin input { cursor: pointer; }
    .check-fin.check-on { color: #1B5E3B; font-weight: 600; }

    .btn-outline-danger { color: #C62828; border-color: #EF9A9A; background: #fff; }
    .btn-outline-danger:hover { background: #FFEBEE; }
    .btn-sm { font-size: 0.6875rem; padding: 0.25rem 0.5rem; white-space: nowrap; }
    .col-acciones { gap: 0.375rem; flex-wrap: wrap; }

    .fila-incompleta { background: #FFF8E1; }
    .fila-incompleta:hover { background: #FFF3D6; }
    .fila-incompleta .tj-input { border-color: #F9A825; }

    .tj-row-add { cursor: pointer; }
    .tj-add-cell { padding: 0.5rem; }
    .tj-add-hint { font-size: 0.6875rem; color: var(--text-secondary); justify-content: flex-end; }

    .tj-resumen { margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-secondary); }
  `],
})
export class TablaJerarquicaComponent {
  /** Colección completa de resultados (misma referencia que mantiene el wizard). */
  @Input() resultados: ResultadoDraft[] = [];
  /** Objeto CGEO seleccionado (aporta el prefijo del código). */
  @Input() cgeo: any = null;
  /** Objeto lineamiento PAD seleccionado (aporta el segundo segmento del código). */
  @Input() lineamiento: any = null;
  /** Correlativo base del primer resultado dentro del lineamiento. */
  @Input() correlativoBase = 1;
  /** Se emite ante CUALQUIER cambio (edición de campo, agregar, eliminar, duplicar). */
  @Output() cambio = new EventEmitter<void>();

  private expandidos: boolean[] = [];

  constructor(private cdr: ChangeDetectorRef) {}

  // -------------------------------------------------------------------------
  // Códigos compuestos autogenerados (readonly, en vivo)
  // -------------------------------------------------------------------------

  codigoResultado(i: number): string {
    if (!this.cgeo || !this.lineamiento) return '';
    return `${this.cgeo.codigo}.${this.lineamiento.codigo}.${this.correlativoBase + i}`;
  }

  codigoProducto(i: number, j: number): string {
    const base = this.codigoResultado(i);
    return base ? `${base}.${j + 1}` : '';
  }

  // -------------------------------------------------------------------------
  // Expansión / contracción de filas padre
  // -------------------------------------------------------------------------

  /** Estado por defecto: expandido (no se requiere sincronizar el arreglo). */
  expandido(i: number): boolean {
    return this.expandidos[i] !== false;
  }

  toggle(i: number): void {
    this.expandidos[i] = this.expandido(i) ? false : true;
    this.cdr.detectChanges();
  }

  // -------------------------------------------------------------------------
  // Fábricas (iguales a las del wizard: la colección es compartida)
  // -------------------------------------------------------------------------

  private nuevoIndicador(): IndicadorDraft {
    return { indicador: '', formula: '', unidad_medida: '', linea_base: null, meta_2030: null };
  }

  private nuevoProgramacionFisica(): Record<string, number | null> {
    return [2026, 2027, 2028, 2029, 2030].reduce((acc, y) => {
      acc[String(y)] = null;
      return acc;
    }, {} as Record<string, number | null>);
  }

  private nuevoPresupuestoAnual(): Record<string, number | null> {
    return [2026, 2027, 2028, 2029, 2030].reduce((acc, y) => {
      acc[String(y)] = null;
      return acc;
    }, {} as Record<string, number | null>);
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

  // -------------------------------------------------------------------------
  // Clonado profundo (duplicar incluye indicadores y programación)
  // -------------------------------------------------------------------------

  private clonar<T>(obj: T): T {
    return JSON.parse(JSON.stringify(obj)) as T;
  }

  private clonarResultado(original: ResultadoDraft): ResultadoDraft {
    const clon = this.clonar(original);
    clon.denominacion = original.denominacion.trim()
      ? `${original.denominacion} (copia)`
      : '';
    return clon;
  }

  private clonarProducto(original: ProductoDraft): ProductoDraft {
    const clon = this.clonar(original);
    clon.denominacion = original.denominacion.trim()
      ? `${original.denominacion} (copia)`
      : '';
    return clon;
  }

  // -------------------------------------------------------------------------
  // Operaciones de la colección
  // -------------------------------------------------------------------------

  agregarResultado(): void {
    this.resultados.push(this.nuevoResultado());
    this.expandidos[this.resultados.length - 1] = true;
    this.notificarCambio();
  }

  eliminarResultado(i: number): void {
    if (this.resultados.length <= 1) return;
    this.resultados.splice(i, 1);
    this.expandidos.splice(i, 1);
    this.notificarCambio();
  }

  agregarProducto(i: number): void {
    this.resultados[i].productos.push(this.nuevoProducto());
    this.expandidos[i] = true;
    this.notificarCambio();
  }

  eliminarProducto(i: number, j: number): void {
    const res = this.resultados[i];
    if (!res || res.productos.length <= 1) return;
    res.productos.splice(j, 1);
    this.notificarCambio();
  }

  duplicarResultado(i: number): void {
    if (!this.resultados[i]) return;
    const clon = this.clonarResultado(this.resultados[i]);
    this.resultados.splice(i + 1, 0, clon);
    this.expandidos.splice(i + 1, 0, true);
    this.notificarCambio();
  }

  duplicarProducto(i: number, j: number): void {
    const res = this.resultados[i];
    if (!res || !res.productos[j]) return;
    const clon = this.clonarProducto(res.productos[j]);
    res.productos.splice(j + 1, 0, clon);
    this.notificarCambio();
  }

  // -------------------------------------------------------------------------
  // Totales y validación visual
  // -------------------------------------------------------------------------

  totalProductos(): number {
    return this.resultados.reduce((acc, r) => acc + r.productos.length, 0);
  }

  totalFilas(): number {
    return this.resultados.length + this.totalProductos();
  }

  tieneFaltaDenominacion(item: ResultadoDraft | ProductoDraft): boolean {
    return !(item.denominacion || '').trim();
  }

  onCampoCambio(): void {
    this.cdr.detectChanges();
    this.cambio.emit();
  }

  private notificarCambio(): void {
    this.cdr.detectChanges();
    this.cambio.emit();
  }
}
