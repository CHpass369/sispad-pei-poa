import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { MatricesPadService } from './matrices-pad.service';

export interface NodoAcumulado {
  nivel: number;
  titulo: string;
  codigo: string;
  detalle: string;
}

export interface CadenaAcumulada {
  id: string;
  titulo: string;
  nodos: NodoAcumulado[];
}

/**
 * VISTA ACUMULADA DE MATRICES PAD (gestión completa).
 *
 * Acumula TODOS los resultados/productos materializados de la GESTIÓN
 * (todos los borradores COMPLETO + cualquier ResultadoPAD existente con
 * vigencia_desde=gestion) en una sola Matriz A (27 columnas) y una sola
 * Matriz B (34 columnas): el PAD completo de la gestión en una vista.
 *
 * Tabs:
 *  - Matriz A completa: tabla de 27 columnas (mismo look que el visualizador).
 *  - Matriz B completa: tabla de 34 columnas.
 *  - Mapa: cadenas PGDESA → PDESA → acuerdos → sector → territorio →
 *    resultado PAD → productos, agrupadas por código de resultado (misma
 *    lógica del Mapa de Conexiones por borrador, aplicada a la gestión).
 *
 * Selector de gestión (default 2026). Estados de carga / vacío / error.
 */
@Component({
  selector: 'app-matriz-acumulada',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <div>
          <h2>📊 Matrices acumuladas de la gestión</h2>
          <p class="text-secondary">
            PAD completo de la gestión en una sola vista: acumula TODOS los
            resultados y productos materializados (borradores COMPLETO +
            ResultadoPAD existentes de la gestión) en una única Matriz A
            (27 columnas) y una única Matriz B (34 columnas).
          </p>
        </div>
        <div class="header-actions">
          <label class="control-label">Gestión:</label>
          <select class="form-control select-gestion" [(ngModel)]="gestion"
            (ngModelChange)="cargar()">
            @for (g of gestiones; track g) {
              <option [ngValue]="g">{{ g }}</option>
            }
          </select>
          @if (!cargando && totalFilas) {
            <span class="badge badge-info">
              {{ totalFilas }} fila(s) · {{ fecha }}
            </span>
          }
          <a routerLink="/matrices-pad" class="btn btn-sm btn-outline">← Volver</a>
        </div>
      </div>
    
      <div class="tabs">
        <button type="button" class="tab" [class.tab-active]="tab === 'a'"
        (click)="cambiarTab('a')">Matriz A completa</button>
        <button type="button" class="tab" [class.tab-active]="tab === 'b'"
        (click)="cambiarTab('b')">Matriz B completa</button>
        <button type="button" class="tab" [class.tab-active]="tab === 'mapa'"
        (click)="cambiarTab('mapa')">Mapa</button>
      </div>
    
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <!-- ===================== TAB: MATRIZ A ===================== -->
      @if (tab === 'a') {
        <div class="card table-card">
          <div class="table-scroll">
            <table class="matriz-table">
              <thead>
                <tr>
                  <th class="sticky-col">Sector</th>
                  <th>CGEO</th>
                  <th>Política</th>
                  <th>Lineamiento</th>
                  <th>Código Resultado</th>
                  <th>Resultado</th>
                  <th>Código Producto</th>
                  <th>Producto</th>
                  <th>Territorialización</th>
                  <th>Responsable</th>
                  <th>Indicador</th>
                  <th>Fórmula</th>
                  <th>Unidad</th>
                  <th>Línea Base</th>
                  <th>Meta 2030</th>
                  @for (y of quinquenio; track y) {
                    <th class="pf-col">Prog. Física {{ y }}</th>
                  }
                  <th>¿Financ.?</th>
                  <th>Presupuesto Total</th>
                  @for (y of quinquenio; track y) {
                    <th class="pf-col">Ppto. {{ y }}</th>
                  }
                </tr>
              </thead>
              <tbody>
                @for (f of filasA; track f) {
                  <tr
                    [class.fila-producto]="f.tipo_fila === 'producto'">
                    <td class="sticky-col">{{ f.sector || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_geografico || '—' }}</span></td>
                    <td class="cell-desc">{{ f.politica || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_lineamiento_pad || '—' }}</span></td>
                    <td><span class="codigo">{{ f.codigo_resultado_pad || '—' }}</span></td>
                    <td class="cell-desc">{{ f.resultado_pad || '—' }}</td>
                    <td><span class="codigo">{{ f.codigo_producto_pad || '—' }}</span></td>
                    <td class="cell-desc">{{ f.producto_pad || '—' }}</td>
                    <td class="cell-desc">{{ f.territorializacion || '—' }}</td>
                    <td class="cell-desc">{{ f.responsable_pad || '—' }}</td>
                    <td class="cell-desc">{{ f.indicador || '—' }}</td>
                    <td class="cell-desc">{{ f.formula || '—' }}</td>
                    <td>{{ f.unidad_medida || '—' }}</td>
                    <td class="num">{{ f.linea_base !== '' ? f.linea_base : '—' }}</td>
                    <td class="num">{{ f.meta_2030 !== '' ? f.meta_2030 : '—' }}</td>
                    @for (y of quinquenio; track y) {
                      <td class="num">{{ f['pf_' + y] !== '' ? f['pf_' + y] : '—' }}</td>
                    }
                    <td>
                      <span class="badge" [class.badge-success]="f.cuenta_con_financiamiento"
                        [class.badge-muted]="!f.cuenta_con_financiamiento">
                        {{ f.cuenta_con_financiamiento ? 'SÍ' : 'NO' }}
                      </span>
                    </td>
                    <td class="num">{{ f.presupuesto_total !== '' ? f.presupuesto_total : '—' }}</td>
                    @for (y of quinquenio; track y) {
                      <td class="num">{{ f['presupuesto_' + y] !== '' ? f['presupuesto_' + y] : '—' }}</td>
                    }
                  </tr>
                }
                @if (cargando) {
                  <tr>
                    <td colspan="27" class="empty-cell">Cargando Matriz A acumulada...</td>
                  </tr>
                }
                @if (!cargando && filasA.length === 0) {
                  <tr>
                    <td colspan="27" class="empty-cell">
                      Sin resultados materializados para la gestión {{ gestion }}.
                      Materialice al menos un borrador Matriz PAD de la gestión.
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }
    
      <!-- ===================== TAB: MATRIZ B ===================== -->
      @if (tab === 'b') {
        <div class="card table-card">
          <div class="table-scroll">
            <table class="matriz-table">
              <thead>
                <tr>
                  <th>Eje PGDESA</th>
                  <th>Impacto</th>
                  <th>Componente</th>
                  <th>Efecto</th>
                  <th>ODS</th>
                  <th>NDC</th>
                  <th>NDT</th>
                  <th>30/30</th>
                  <th>Cod. Sector</th>
                  <th>Sector</th>
                  <th>Cod. RS</th>
                  <th>Resultado Sectorial</th>
                  <th>CGEO</th>
                  <th>ETA</th>
                  <th>Lineamiento</th>
                  <th>Cod. Resultado</th>
                  <th>Resultado</th>
                  <th>Cod. Producto</th>
                  <th>Producto</th>
                  <th>Indicador</th>
                  <th>Fórmula</th>
                  <th>Unidad</th>
                  <th>LB</th>
                  <th>Meta 2030</th>
                  @for (y of quinquenio; track y) {
                    <th class="pf-col">Prog. Física {{ y }}</th>
                  }
                  <th>Presupuesto Referencial</th>
                  @for (y of quinquenio; track y) {
                    <th class="pf-col">Ppto. {{ y }}</th>
                  }
                </tr>
              </thead>
              <tbody>
                @for (f of filasB; track f) {
                  <tr
                    [class.fila-producto]="f.tipo_fila === 'producto'">
                    <td><span class="codigo">{{ f.cod_eje_pgdesa || '—' }}</span></td>
                    <td class="cell-desc">{{ f.objetivo_impacto || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_componente_pdesa || '—' }}</span></td>
                    <td class="cell-desc">{{ f.objetivo_efecto || '—' }}</td>
                    <td>{{ f.ods || '—' }}</td>
                    <td>{{ f.ndc || '—' }}</td>
                    <td>{{ f.ndt || '—' }}</td>
                    <td>{{ f.compromiso_3030 || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_sector || '—' }}</span></td>
                    <td class="cell-desc">{{ f.sector || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_resultado_pds || '—' }}</span></td>
                    <td class="cell-desc">{{ f.resultado_pds || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_geografico || '—' }}</span></td>
                    <td class="cell-desc">{{ f.eta || '—' }}</td>
                    <td><span class="codigo">{{ f.cod_lineamiento_pad || '—' }}</span></td>
                    <td><span class="codigo">{{ f.codigo_resultado_pad || '—' }}</span></td>
                    <td class="cell-desc">{{ f.resultado_pad || '—' }}</td>
                    <td><span class="codigo">{{ f.codigo_producto_pad || '—' }}</span></td>
                    <td class="cell-desc">{{ f.producto_pad || '—' }}</td>
                    <td class="cell-desc">{{ f.indicador || '—' }}</td>
                    <td class="cell-desc">{{ f.formula || '—' }}</td>
                    <td>{{ f.unidad_medida || '—' }}</td>
                    <td class="num">{{ f.linea_base !== '' ? f.linea_base : '—' }}</td>
                    <td class="num">{{ f.meta_2030 !== '' ? f.meta_2030 : '—' }}</td>
                    @for (y of quinquenio; track y) {
                      <td class="num">{{ f['pf_' + y] !== '' ? f['pf_' + y] : '—' }}</td>
                    }
                    <td class="num">{{ f.presupuesto_total !== '' ? f.presupuesto_total : '—' }}</td>
                    @for (y of quinquenio; track y) {
                      <td class="num">{{ f['presupuesto_' + y] !== '' ? f['presupuesto_' + y] : '—' }}</td>
                    }
                  </tr>
                }
                @if (cargando) {
                  <tr>
                    <td colspan="34" class="empty-cell">Cargando Matriz B acumulada...</td>
                  </tr>
                }
                @if (!cargando && filasB.length === 0) {
                  <tr>
                    <td colspan="34" class="empty-cell">
                      Sin resultados materializados para la gestión {{ gestion }}.
                      Materialice al menos un borrador Matriz PAD de la gestión.
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }
    
      <!-- ===================== TAB: MAPA ===================== -->
      @if (tab === 'mapa') {
        @if (!cargando && cadenas.length) {
          <div class="card mapa-card">
            <div class="mapa-controles">
              <label class="control-label">Mostrar:</label>
              <select class="form-control select-cadena" [(ngModel)]="seleccion"
                (ngModelChange)="cdr.detectChanges()">
                <option [ngValue]="null">Todas las cadenas ({{ cadenas.length }})</option>
                @for (c of cadenas; track c; let i = $index) {
                  <option [ngValue]="i">
                    {{ i + 1 }}. {{ c.titulo }}
                  </option>
                }
              </select>
              <button type="button" class="btn btn-sm btn-outline" (click)="verTodas()">Ver todas</button>
              @if (seleccion !== null) {
                <span class="control-note">
                  Cadena {{ (seleccion ?? 0) + 1 }} de {{ cadenas.length }}
                </span>
              }
            </div>
            <div class="mapa-scroll">
              <div class="mapa-todas" [class.mapa-sola]="seleccion !== null">
                @for (cadena of cadenasVisibles; track cadena; let ci = $index) {
                  <div class="mapa-cadena">
                    @if (seleccion === null) {
                      <div class="cadena-titulo">
                        Cadena {{ ci + 1 }} — <span class="codigo">{{ cadena.titulo }}</span>
                      </div>
                    }
                    <div class="cadena-nodos">
                      @for (nodo of cadena.nodos; track nodo; let ni = $index) {
                        <div class="nodo nivel-{{ nodo.nivel }}">
                          <div class="nodo-cab">{{ nodo.titulo }}</div>
                          <div class="nodo-codigo">{{ nodo.codigo || '—' }}</div>
                          <div class="nodo-detalle">{{ nodo.detalle || '—' }}</div>
                        </div>
                        @if (ni < cadena.nodos.length - 1) {
                          <div class="conector">
                            <div class="conector-linea"></div>
                          </div>
                        }
                      }
                    </div>
                  </div>
                }
              </div>
            </div>
            <div class="mapa-leyenda">
              <span class="leyenda-item nivel-1-dot">1. PGDESA</span>
              <span class="leyenda-item nivel-2-dot">2. PDESA</span>
              <span class="leyenda-item nivel-3-dot">3. Acuerdos</span>
              <span class="leyenda-item nivel-4-dot">4. Sector</span>
              <span class="leyenda-item nivel-5-dot">5. Territorio</span>
              <span class="leyenda-item nivel-6-dot">6. Resultado PAD</span>
              <span class="leyenda-item nivel-7-dot">7. Productos</span>
            </div>
          </div>
        }
        @if (!cargando && cadenas.length === 0) {
          <div class="card mapa-card">
            <p class="empty-state">
              Sin cadenas para mostrar. Materialice al menos un borrador Matriz PAD
              de la gestión {{ gestion }}.
            </p>
          </div>
        }
      }
    </div>
    `,
  styles: [`
    .matriz-page { padding-bottom: 2rem; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }
    .header-actions { display: flex; align-items: center; gap: 0.5rem; white-space: nowrap; }
    .control-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); }
    .select-gestion { width: auto; min-width: 96px; font-size: 0.75rem; }

    /* Tabs */
    .tabs { display: flex; gap: 0.25rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); }
    .tab { border: none; background: transparent; padding: 0.5rem 1rem; font-size: 0.8125rem; font-weight: 600; color: var(--text-secondary); cursor: pointer; border-bottom: 2px solid transparent; }
    .tab:hover { color: var(--primary); }
    .tab-active { color: var(--primary); border-bottom-color: var(--primary); }

    /* Tablas (mismo look que los visualizadores por borrador) */
    .table-card { padding: 0; overflow: hidden; }
    .table-scroll { overflow-x: auto; max-height: 70vh; overflow-y: auto; }
    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; }
    .matriz-table th { position: sticky; top: 0; z-index: 2; text-align: left; padding: 0.5rem 0.625rem; background: var(--bg); color: var(--text-secondary); font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.03em; border-bottom: 1px solid var(--border); white-space: nowrap; }
    .matriz-table td { padding: 0.5rem 0.625rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .sticky-col { position: sticky; left: 0; background: #fff; z-index: 1; min-width: 130px; }
    .matriz-table th.sticky-col { z-index: 3; }
    .fila-producto { background: #FAFBFC; }
    .cell-desc { min-width: 150px; max-width: 240px; }
    .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; }
    .pf-col { min-width: 90px; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 1.5rem; }

    .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #8D6E2F; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-muted { background: #F1F1F1; color: #757575; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    /* Mapa (mismo estilo que el Mapa de Conexiones por borrador) */
    .mapa-card { padding: 1rem; }
    .mapa-controles { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .select-cadena { width: auto; min-width: 320px; max-width: 100%; font-size: 0.75rem; }
    .control-note { font-size: 0.6875rem; color: var(--text-secondary); }
    .mapa-scroll { overflow-x: auto; padding-bottom: 0.5rem; }
    .mapa-todas { display: flex; gap: 2.5rem; align-items: stretch; min-width: 760px; }
    .mapa-todas.mapa-sola { min-width: 0; }
    .mapa-cadena { flex: 0 0 auto; width: 340px; max-width: 100%; display: flex; flex-direction: column; }
    .cadena-titulo { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .cadena-nodos { display: flex; flex-direction: column; align-items: stretch; }
    .nodo { background: #fff; border: 1px solid var(--border); border-top-width: 5px; border-radius: 8px; padding: 0.5rem 0.625rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .nivel-1 { border-top-color: #1B5E20; }
    .nivel-2 { border-top-color: var(--mdc-blue-800); }
    .nivel-3 { border-top-color: #6A1B9A; }
    .nivel-4 { border-top-color: #E65100; }
    .nivel-5 { border-top-color: #00838F; }
    .nivel-6 { border-top-color: var(--mdc-red-800); }
    .nivel-7 { border-top-color: #37474F; }
    .nodo-cab { font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-secondary); font-weight: 700; margin-bottom: 0.15rem; }
    .nodo-codigo { font-family: monospace; font-weight: 700; font-size: 0.8125rem; color: var(--primary-dark); line-height: 1.3; white-space: pre-line; }
    .nivel-1 .nodo-codigo { color: #1B5E20; }
    .nivel-2 .nodo-codigo { color: var(--mdc-blue-800); }
    .nivel-3 .nodo-codigo { color: #6A1B9A; }
    .nivel-4 .nodo-codigo { color: #E65100; }
    .nivel-5 .nodo-codigo { color: #00838F; }
    .nivel-6 .nodo-codigo { color: var(--mdc-red-800); }
    .nivel-7 .nodo-codigo { color: #37474F; }
    .nodo-detalle { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem; line-height: 1.35; }
    .conector { height: 26px; display: flex; justify-content: center; }
    .conector-linea { width: 2px; height: 100%; background: #B0BEC5; }
    .mapa-leyenda { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
    .leyenda-item { font-size: 0.6875rem; color: var(--text-secondary); display: inline-flex; align-items: center; gap: 0.375rem; }
    .leyenda-item::before { content: ''; width: 12px; height: 4px; border-radius: 2px; display: inline-block; }
    .nivel-1-dot::before { background: #1B5E20; }
    .nivel-2-dot::before { background: var(--mdc-blue-800); }
    .nivel-3-dot::before { background: #6A1B9A; }
    .nivel-4-dot::before { background: #E65100; }
    .nivel-5-dot::before { background: #00838F; }
    .nivel-6-dot::before { background: var(--mdc-red-800); }
    .nivel-7-dot::before { background: #37474F; }
    .empty-state { text-align: center; color: var(--text-secondary); padding: 1.5rem; font-size: 0.8125rem; }

    @media (max-width: 768px) {
      .page-header { flex-direction: column; }
      .select-cadena { min-width: 220px; }
    }
  `],
})
export class MatrizAcumuladaComponent implements OnInit {
  gestiones = [2026, 2027, 2028, 2029, 2030];
  gestion = 2026;
  tab: 'a' | 'b' | 'mapa' = 'a';

  filasA: any[] = [];
  filasB: any[] = [];
  cadenas: CadenaAcumulada[] = [];
  seleccion: number | null = null;

  quinquenio = [2026, 2027, 2028, 2029, 2030];
  cargando = false;
  mensajeError = '';
  fecha = '';
  totalFilas = 0;

  constructor(
    private service: MatricesPadService,
    public cdr: ChangeDetectorRef,
  ) {}

  get cadenasVisibles(): CadenaAcumulada[] {
    if (this.seleccion === null) return this.cadenas;
    const cadena = this.cadenas[this.seleccion];
    return cadena ? [cadena] : [];
  }

  ngOnInit(): void {
    this.cargar();
  }

  cambiarTab(tab: 'a' | 'b' | 'mapa'): void {
    this.tab = tab;
    this.cdr.detectChanges();
  }

  verTodas(): void {
    this.seleccion = null;
    this.cdr.detectChanges();
  }

  cargar(): void {
    this.cargando = true;
    this.mensajeError = '';
    this.seleccion = null;

    this.service.matrizAGestion(this.gestion).subscribe({
      next: (r) => {
        this.filasA = r?.filas || [];
        this.totalFilas = r?.total_filas ?? this.filasA.length;
        this.fecha = r?.fecha || '';
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando Matriz A acumulada', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la Matriz A acumulada de la gestión.';
        this.cdr.detectChanges();
      },
    });

    this.service.matrizBGestion(this.gestion).subscribe({
      next: (r) => {
        this.filasB = r?.filas || [];
        this.cadenas = this.construirCadenas(this.filasB);
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando Matriz B acumulada', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la Matriz B acumulada de la gestión.';
        this.cdr.detectChanges();
      },
    });
  }

  // -------------------------------------------------------------------------
  // Cadenas del Mapa: cada resultado PAD (y sus productos) = 1 cadena
  // (misma lógica del Mapa de Conexiones por borrador, aplicada a la gestión)
  // -------------------------------------------------------------------------

  private construirCadenas(filas: any[]): CadenaAcumulada[] {
    const grupos = new Map<string, any[]>();
    filas.forEach((f, idx) => {
      const key = f.codigo_resultado_pad ? String(f.codigo_resultado_pad) : `fila-${idx}`;
      if (!grupos.has(key)) grupos.set(key, []);
      grupos.get(key)!.push(f);
    });

    const cadenas: CadenaAcumulada[] = [];
    for (const [key, rows] of grupos) {
      const principal = rows.find((r) => r.tipo_fila !== 'producto') || rows[0];
      const productos = rows.filter(
        (r) => r.tipo_fila === 'producto' && r.codigo_producto_pad,
      );
      cadenas.push({
        id: key,
        titulo: principal && principal.codigo_resultado_pad
          ? `${principal.codigo_resultado_pad} — ${principal.resultado_pad || 'Sin denominación'}`
          : key,
        nodos: this.nodosDe(principal, productos),
      });
    }
    return cadenas;
  }

  private nodosDe(principal: any, productos: any[]): NodoAcumulado[] {
    const p = principal || {};
    return [
      {
        nivel: 1,
        titulo: 'Eje PGDESA',
        codigo: p.cod_eje_pgdesa || '—',
        detalle: p.objetivo_impacto || 'Objetivo de impacto no definido',
      },
      {
        nivel: 2,
        titulo: 'Componente PDESA',
        codigo: p.cod_componente_pdesa || '—',
        detalle: p.objetivo_efecto || 'Objetivo de efecto no definido',
      },
      {
        nivel: 3,
        titulo: 'Acuerdos Internacionales',
        codigo: this.codigosAcuerdos(p),
        detalle: 'ODS · NDC · NDT · 30/30',
      },
      {
        nivel: 4,
        titulo: 'Sector / Resultado Sectorial',
        codigo: p.cod_sector ? `${p.cod_sector} · ${p.cod_resultado_pds || ''}`.trim() : '—',
        detalle: p.sector
          ? `${p.sector}${p.resultado_pds ? ' — ' + p.resultado_pds : ''}`
          : 'Sector no definido',
      },
      {
        nivel: 5,
        titulo: 'CGEO · ETA · Lineamiento',
        codigo: p.cod_geografico ? `${p.cod_geografico} · ${p.cod_lineamiento_pad || ''}`.trim() : '—',
        detalle: p.eta || 'ETA no definida',
      },
      {
        nivel: 6,
        titulo: 'Resultado Territorial PAD',
        codigo: p.codigo_resultado_pad || '—',
        detalle: p.resultado_pad || 'Sin denominación',
      },
      ...(productos.length
        ? productos.map((prod) => ({
            nivel: 7,
            titulo: 'Producto PAD',
            codigo: prod.codigo_producto_pad || '—',
            detalle: prod.producto_pad || 'Sin denominación',
          }))
        : [{
            nivel: 7,
            titulo: 'Productos PAD',
            codigo: '—',
            detalle: 'Sin productos registrados',
          }]),
    ];
  }

  /** Códigos de acuerdos apilados: ODS / NDC / NDT / 30-30. */
  private codigosAcuerdos(p: any): string {
    const partes: string[] = [];
    if (p.ods) partes.push(`ODS ${p.ods}`);
    if (p.ndc) partes.push(`NDC ${p.ndc}`);
    if (p.ndt) partes.push(`NDT ${p.ndt}`);
    if (p.compromiso_3030) partes.push(`30/30 ${p.compromiso_3030}`);
    return partes.length ? partes.join('\n') : '—';
  }
}
