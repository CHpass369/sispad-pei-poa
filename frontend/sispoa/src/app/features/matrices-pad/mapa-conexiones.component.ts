import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatricesPadService } from './matrices-pad.service';

export interface NodoMapa {
  nivel: number;
  titulo: string;
  codigo: string;
  detalle: string;
}

export interface CadenaMapa {
  id: string;
  titulo: string;
  nodos: NodoMapa[];
}

/**
 * Mapa de conexiones de la Matriz B (VISTA DE PRESENTACIÓN — solo lectura).
 *
 * Una fila de la Matriz B = una cadena PGDESA → PDESA → acuerdos → sector →
 * resultado sectorial → CGEO/ETA/lineamiento → resultado territorial PAD →
 * productos. El mapa renderiza cada cadena como NODOS conectados por niveles
 * (CSS puro, sin dependencias), para presentación a autoridades:
 *
 *   Nivel 1: Eje PGDESA + Objetivo Impacto
 *   Nivel 2: Componente PDESA + Objetivo Efecto
 *   Nivel 3: Acuerdos (ODS / NDC / NDT / 30-30)
 *   Nivel 4: Sector + Resultado Sectorial
 *   Nivel 5: CGEO + ETA + Lineamiento
 *   Nivel 6: Resultado Territorial PAD (código + denominación)
 *   Nivel 7: Productos (código + denominación), un nodo por producto
 *
 * Selector de cadena arriba (dropdown) + botón "Ver todas" que apila todas
 * las cadenas lado a lado con scroll horizontal.
 */
@Component({
  selector: 'app-mapa-conexiones',
  standalone: false,
  template: `
    <div class="mapa-page">
      <div class="page-header">
        <div>
          <h2>🗺 Mapa de Conexiones — Matriz B</h2>
          <p class="text-secondary">
            Cadena completa PGDESA → PDESA → acuerdos internacionales → sector →
            resultado sectorial → CGEO/ETA/lineamiento → resultado territorial PAD
            → productos. Vista de presentación (solo lectura) para autoridades.
          </p>
        </div>
        <div class="header-actions">
          <span class="badge" [class.badge-success]="materializada"
            [class.badge-warning]="!materializada">
            {{ materializada ? 'Materializada' : 'Borrador' }}
          </span>
          @if (!cargando && cadenas.length) {
            <span class="badge badge-info">
              {{ cadenas.length }} cadena(s)
            </span>
          }
          <a routerLink="../" class="btn btn-sm btn-outline">← Matriz B</a>
        </div>
      </div>
    
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      @if (!cargando && cadenas.length) {
        <div class="card mapa-card">
          <!-- Selector de cadena -->
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
          <!-- Cadenas apiladas (scroll horizontal) -->
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
          <!-- Leyenda de niveles -->
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
            Sin cadenas para mostrar. Complete el wizard y materialice la Matriz B
            (o registre resultados y productos en el paso 6 del wizard).
          </p>
        </div>
      }
    </div>
    `,
  styles: [`
    .mapa-page { padding-bottom: 2rem; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }
    .header-actions { display: flex; align-items: center; gap: 0.5rem; white-space: nowrap; }
    .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #8D6E2F; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    .mapa-card { padding: 1rem; }
    .mapa-controles { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .control-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); }
    .select-cadena { width: auto; min-width: 320px; max-width: 100%; font-size: 0.75rem; }
    .control-note { font-size: 0.6875rem; color: var(--text-secondary); }

    .mapa-scroll { overflow-x: auto; padding-bottom: 0.5rem; }
    .mapa-todas { display: flex; gap: 2.5rem; align-items: stretch; min-width: 760px; }
    .mapa-todas.mapa-sola { min-width: 0; }

    .mapa-cadena { flex: 0 0 auto; width: 340px; max-width: 100%; display: flex; flex-direction: column; }
    .cadena-titulo { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); white-space: nowrap; }

    .cadena-nodos { display: flex; flex-direction: column; align-items: stretch; }

    /* Nodo: caja blanca con borde superior de color por nivel */
    .nodo { background: #fff; border: 1px solid var(--border); border-top-width: 5px; border-radius: 8px; padding: 0.5rem 0.625rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .nivel-1 { border-top-color: var(--ok-tinta); }
    .nivel-2 { border-top-color: var(--mdc-blue-800); }
    .nivel-3 { border-top-color: #6A1B9A; }
    .nivel-4 { border-top-color: #E65100; }
    .nivel-5 { border-top-color: #00838F; }
    .nivel-6 { border-top-color: var(--mdc-red-800); }
    .nivel-7 { border-top-color: #37474F; }

    .nodo-cab { font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-secondary); font-weight: 700; margin-bottom: 0.15rem; }
    .nodo-codigo { font-family: monospace; font-weight: 700; font-size: 0.8125rem; color: var(--primary-dark); line-height: 1.3; }
    .nivel-1 .nodo-codigo { color: var(--ok-tinta); }
    .nivel-2 .nodo-codigo { color: var(--mdc-blue-800); }
    .nivel-3 .nodo-codigo { color: #6A1B9A; }
    .nivel-4 .nodo-codigo { color: #E65100; }
    .nivel-5 .nodo-codigo { color: #00838F; }
    .nivel-6 .nodo-codigo { color: var(--mdc-red-800); }
    .nivel-7 .nodo-codigo { color: #37474F; }
    .nodo-detalle { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem; line-height: 1.35; }

    /* Conector vertical entre nodos (CSS puro) */
    .conector { height: 26px; display: flex; justify-content: center; }
    .conector-linea { width: 2px; height: 100%; background: #B0BEC5; }

    .mapa-leyenda { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
    .leyenda-item { font-size: 0.6875rem; color: var(--text-secondary); display: inline-flex; align-items: center; gap: 0.375rem; }
    .leyenda-item::before { content: ''; width: 12px; height: 4px; border-radius: 2px; display: inline-block; }
    .nivel-1-dot::before { background: var(--ok-tinta); }
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
export class MapaConexionesComponent implements OnInit {
  /** Selección de cadena: null = todas, número = índice de cadena. */
  seleccion: number | null = null;

  filas: any[] = [];
  cadenas: CadenaMapa[] = [];
  cargando = false;
  materializada = false;
  mensajeError = '';

  constructor(
    private service: MatricesPadService,
    private route: ActivatedRoute,
    private router: Router,
    public cdr: ChangeDetectorRef,
  ) {}

  get cadenasVisibles(): CadenaMapa[] {
    if (this.seleccion === null) return this.cadenas;
    const cadena = this.cadenas[this.seleccion];
    return cadena ? [cadena] : [];
  }

  verTodas(): void {
    this.seleccion = null;
    this.cdr.detectChanges();
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.mensajeError = 'Falta el identificador del borrador.';
      return;
    }
    this.service.obtener(id).subscribe({
      next: (b) => {
        this.materializada = b.estado === 'COMPLETO';
        this.cdr.detectChanges();
      },
      error: () => { /* se ignora: el mapa puede no requerir el detalle */ },
    });
    this.service.matrizB(id).subscribe({
      next: (filas) => {
        this.filas = filas || [];
        this.cadenas = this.construirCadenas(this.filas);
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando Matriz B para el mapa', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la Matriz B para el mapa de conexiones.';
        this.cdr.detectChanges();
      },
    });
  }

  // -------------------------------------------------------------------------
  // Construcción de cadenas: cada resultado PAD (y sus productos) = 1 cadena
  // -------------------------------------------------------------------------

  private construirCadenas(filas: any[]): CadenaMapa[] {
    const grupos = new Map<string, any[]>();
    filas.forEach((f, idx) => {
      const key = f.codigo_resultado_pad ? String(f.codigo_resultado_pad) : `fila-${idx}`;
      if (!grupos.has(key)) grupos.set(key, []);
      grupos.get(key)!.push(f);
    });

    const cadenas: CadenaMapa[] = [];
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

  private nodosDe(principal: any, productos: any[]): NodoMapa[] {
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
