import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import { NodoV2, SisPeService, VersionV2 } from './sis-pe.service';

@Component({
  standalone: false,
  selector: 'app-sis-pe-version',
  template: `
    <div class="page-header">
      <h2>Versión de Instrumento</h2>
      <p class="text-secondary" *ngIf="version">
        {{ version.instrumento_codigo }} v{{ version.numero }} — {{ version.etiqueta }}
      </p>
    </div>

    <div *ngIf="cargando" class="loading">Cargando versión...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <div class="card" *ngIf="version && !cargando">
      <div class="info-grid">
        <div><strong>Estado:</strong> <span class="badge">{{ version.estado }}</span></div>
        <div><strong>Metodología:</strong> {{ version.metodologia_nombre }}</div>
        <div><strong>Nodos:</strong> {{ version.nodos_count }}</div>
        <div><strong>Vínculos:</strong> {{ version.vinculos_count }}</div>
        <div *ngIf="version.inmutable">
          <strong>Inmutable:</strong> ✓ aprobada
          <div class="checksum">{{ version.checksum }}</div>
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-sm" (click)="verificar()">Verificar checksum</button>
        <button
          *ngIf="!version.inmutable && puedeAprobar"
          class="btn btn-sm btn-approve"
          (click)="aprobar()">Aprobar</button>
      </div>
      <div *ngIf="verificacion" class="verify-box">
        Checksum {{ verificacion.consistente ? '✅ consistente' : '⚠️ INCONSISTENTE' }}
      </div>
    </div>

    <h3 class="section-title" *ngIf="!cargando && version">Árbol de nodos</h3>
    <div class="card" *ngIf="!cargando && version">
      <app-sis-pe-arbol [nodos]="arbol"></app-sis-pe-arbol>
      <div *ngIf="arbol.length === 0" class="empty">Sin nodos</div>
    </div>
  `,
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.875rem; }
    .checksum { font-family: monospace; font-size: 0.6875rem; color: var(--text-secondary); word-break: break-all; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .actions { margin-top: 1rem; display: flex; gap: 0.5rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-sm { background: #E3F2FD; color: #1565C0; }
    .btn-approve { background: #2E7D32; color: white; }
    .verify-box { margin-top: 0.75rem; font-size: 0.8125rem; }
    .section-title { margin: 1.25rem 0 0.5rem; font-size: 1rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 1rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class SisPeVersionComponent implements OnInit {
  version: VersionV2 | null = null;
  arbol: NodoV2[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  verificacion: { consistente: boolean } | null = null;

  constructor(
    private route: ActivatedRoute,
    private service: SisPeService,
    private permissions: PermissionsService,
  ) {}

  get puedeAprobar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pe.approve', 'sis_pe.pad.validate']);
  }

  ngOnInit(): void {
    const instrumentoId = this.route.snapshot.paramMap.get('instrumentoId');
    const versionId = this.route.snapshot.paramMap.get('id');
    if (versionId) {
      this.cargarVersion(versionId);
    } else if (instrumentoId) {
      this.cargarVersionesInstrumento(instrumentoId);
    }
  }

  private cargarVersion(id: string): void {
    this.service.obtenerVersion(id).subscribe({
      next: (v) => {
        this.version = v;
        this.cargarNodos(id);
      },
      error: () => { this.error = 'Error al cargar la versión'; this.cargando = false; },
    });
  }

  private cargarVersionesInstrumento(instrumentoId: string): void {
    this.service.versionesDeInstrumento(instrumentoId).subscribe({
      next: (versiones) => {
        if (versiones.length) {
          this.cargarVersion(versiones[versiones.length - 1].id);
        } else {
          this.cargando = false;
        }
      },
      error: () => { this.error = 'Error al cargar versiones'; this.cargando = false; },
    });
  }

  private cargarNodos(versionId: string): void {
    this.service.nodosDeVersion(versionId).subscribe({
      next: (nodos) => {
        this.arbol = this.construirArbol(nodos);
        this.cargando = false;
      },
      error: () => { this.error = 'Error al cargar nodos'; this.cargando = false; },
    });
  }

  private construirArbol(nodos: NodoV2[]): NodoV2[] {
    const porId = new Map<string, NodoV2>(nodos.map(n => [n.id, { ...n, hijos: [] }]));
    const raices: NodoV2[] = [];
    porId.forEach(n => {
      if (n.padre && porId.has(n.padre)) {
        porId.get(n.padre)!.hijos!.push(n);
      } else {
        raices.push(n);
      }
    });
    const ordenar = (lista: NodoV2[]) => {
      lista.sort((a, b) => a.orden - b.orden || a.codigo.localeCompare(b.codigo));
      lista.forEach(n => ordenar(n.hijos || []));
    };
    ordenar(raices);
    return raices;
  }

  verificar(): void {
    if (!this.version) return;
    this.service.verificarVersion(this.version.id).subscribe({
      next: (v) => { this.verificacion = v; },
      error: () => { this.error = 'Error al verificar checksum'; },
    });
  }

  aprobar(): void {
    if (!this.version) return;
    this.service.aprobarVersion(this.version.id, 'Aprobado desde SIS-PE V2').subscribe({
      next: (v) => {
        this.version = v;
        this.mensaje = 'Versión aprobada e inmutable';
        this.cargarNodos(v.id);
      },
      error: () => { this.error = 'Error al aprobar la versión'; },
    });
  }
}
