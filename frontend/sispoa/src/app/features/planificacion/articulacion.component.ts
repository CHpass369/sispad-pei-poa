import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-articulacion',
  standalone: false,
  template: `
    <div class="builder-page">
      <div class="page-header">
        <h2>Constructor de Articulación</h2>
        <p class="text-secondary">PDES → PTDI → PEI → POA</p>
      </div>

      <!-- Step builder: 4 niveles en paralelo -->
      <div class="builder-layout">
        <!-- Nivel 1: PDES -->
        <div class="level-panel">
          <div class="panel-header" style="background:#1B5E3B">
            <h3>PDES</h3>
            <small>Acción PDES</small>
          </div>
          <div class="panel-body">
            <div class="selector">
              <input [(ngModel)]="pdesSearch" (input)="filtrarPdes()" 
                     class="form-control" placeholder="Buscar acción PDES...">
            </div>
            <div class="item-list">
              <div *ngFor="let n of pdesFiltrados" class="item" 
                   [class.selected]="pdesSelected?.id === n.id"
                   (click)="seleccionarPdes(n)">
                <strong>{{ n.codigo }}</strong>
                <span class="item-desc">{{ n.nombre | slice:0:60 }}</span>
                <span class="item-count" *ngIf="n.pei_count > 0">{{ n.pei_count }} PEI</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Nivel 2: PTDI (Acción PEI vinculada) -->
        <div class="level-panel">
          <div class="panel-header" style="background:#2E7D4F">
            <h3>PTDI / PEI</h3>
            <small>Acción de Mediano Plazo</small>
          </div>
          <div class="panel-body">
            <div class="selector">
              <button class="btn btn-accent btn-sm btn-full" (click)="crearAmp()">
                + Nueva AMP
              </button>
            </div>
            <div class="item-list">
              <div *ngFor="let amp of ampsVinculadas" class="item" 
                   [class.selected]="ampSelected?.id === amp.id"
                   (click)="seleccionarAmp(amp)">
                <strong>{{ amp.codigo }}</strong>
                <span class="item-desc">{{ amp.nombre | slice:0:60 }}</span>
                <span class="item-count" *ngIf="amp.poa_count > 0">{{ amp.poa_count }} POA</span>
              </div>
              <div *ngIf="ampsVinculadas.length === 0" class="empty-hint">
                Seleccione una acción PDES
              </div>
            </div>
          </div>
        </div>

        <!-- Nivel 3: POA por año -->
        <div class="level-panel">
          <div class="panel-header" style="background:#C7952E">
            <h3>POA</h3>
            <small>Acción de Corto Plazo</small>
          </div>
          <div class="panel-body">
            <div class="selector">
              <button class="btn btn-accent btn-sm btn-full" (click)="crearAcp()">
                + Nueva ACP
              </button>
            </div>
            <div class="item-list">
              <div *ngFor="let acp of acpsVinculadas" class="item"
                   [class.selected]="acpSelected?.id === acp.id">
                <strong>{{ acp.codigo }}</strong>
                <span class="item-year">{{ acp.gestion }}</span>
                <span class="item-desc">{{ acp.nombre | slice:0:50 }}</span>
              </div>
              <div *ngIf="acpsVinculadas.length === 0" class="empty-hint">
                Seleccione una AMP
              </div>
            </div>
          </div>
        </div>

        <!-- Vincular panel -->
        <div class="level-panel vincular-panel">
          <div class="panel-header" style="background:#1565C0">
            <h3>Vincular</h3>
            <small>Crear articulación</small>
          </div>
          <div class="panel-body">
            <div class="vinculacion-form">
              <label>Tipo de vínculo:</label>
              <select [(ngModel)]="tipoVinculo" class="form-control">
                <option value="pdes_pei">PDES → PEI (AMP)</option>
                <option value="pei_poa">PEI → POA (ACP)</option>
              </select>

              <div *ngIf="tipoVinculo === 'pdes_pei'" class="vinculacion-step">
                <label>Acción PDES origen:</label>
                <div class="selected-item">{{ pdesSelected?.codigo || '—' }}</div>
                <label>Acción PEI destino:</label>
                <select [(ngModel)]="ampAVincular" class="form-control">
                  <option value="">Seleccione AMP...</option>
                  <option *ngFor="let a of ampsDisponibles" [value]="a.id">{{ a.codigo }} - {{ a.nombre | slice:0:40 }}</option>
                </select>
                <button class="btn btn-primary btn-full" (click)="vincularPdesPei()" 
                        [disabled]="!pdesSelected || !ampAVincular">
                  Vincular PDES → PEI
                </button>
              </div>

              <div *ngIf="tipoVinculo === 'pei_poa'" class="vinculacion-step">
                <label>Acción PEI origen:</label>
                <div class="selected-item">{{ ampSelected?.codigo || '—' }}</div>
                <label>Acción POA destino (y año):</label>
                <select [(ngModel)]="acpAVincular" class="form-control">
                  <option value="">Seleccione ACP...</option>
                  <option *ngFor="let a of acpsDisponibles" [value]="a.id">{{ a.codigo }} ({{ a.gestion }})</option>
                </select>
                <button class="btn btn-primary btn-full" (click)="vincularPeiPoa()"
                        [disabled]="!ampSelected || !acpAVincular">
                  Vincular PEI → POA
                </button>
              </div>

              <div *ngIf="mensaje" class="msg" [class.error]="mensajeError">
                {{ mensaje }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vista resumen -->
      <div class="card resumen-card" *ngIf="pdesSelected">
        <h4>Cadena: {{ pdesSelected.codigo }} — {{ pdesSelected.nombre | slice:0:60 }}</h4>
        <div class="cadena">
          <div class="eslabon" *ngFor="let amp of ampsVinculadas">
            <div class="eslabon-cabecera">{{ amp.codigo }} — {{ amp.nombre | slice:0:50 }}</div>
          </div>
          <div *ngIf="ampsVinculadas.length === 0" class="empty-hint">
            Sin PEI vinculadas — use el panel Vincular
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .builder-page { padding-bottom: 2rem; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; }
    .builder-layout { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.5rem; }
    .level-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
    .panel-header { color: white; padding: 0.625rem 0.75rem; }
    .panel-header h3 { font-size: 0.8125rem; margin: 0; }
    .panel-header small { font-size: 0.6875rem; opacity: 0.8; }
    .panel-body { padding: 0.5rem; flex: 1; display: flex; flex-direction: column; }
    .selector { margin-bottom: 0.5rem; }
    .selector input { font-size: 0.75rem; padding: 0.375rem; }
    .item-list { flex: 1; overflow-y: auto; max-height: 350px; }
    .item { padding: 0.5rem; border-bottom: 1px solid var(--border); cursor: pointer; transition: background 0.1s; }
    .item:hover { background: #F0F7F3; }
    .item.selected { background: #E8F5E9; border-left: 3px solid var(--primary); }
    .item strong { display: block; font-size: 0.75rem; }
    .item-desc { display: block; font-size: 0.6875rem; color: var(--text-secondary); margin-top: 0.125rem; }
    .item-year { float: right; font-size: 0.6875rem; background: #E3F2FD; padding: 0.125rem 0.375rem; border-radius: 3px; }
    .item-count { float: right; font-size: 0.625rem; background: var(--primary); color: white; padding: 0.125rem 0.375rem; border-radius: 3px; }
    .empty-hint { text-align: center; color: var(--text-secondary); font-size: 0.75rem; padding: 1rem; }
    .btn-full { width: 100%; justify-content: center; margin-top: 0.25rem; }
    .btn-sm { font-size: 0.75rem; padding: 0.375rem; }
    .vincular-panel .panel-body { background: #F8FBFF; }
    .vinculacion-form label { display: block; font-size: 0.6875rem; margin: 0.5rem 0 0.25rem; color: var(--text-secondary); }
    .vinculacion-form select { font-size: 0.75rem; padding: 0.375rem; }
    .selected-item { font-size: 0.8125rem; font-weight: 600; padding: 0.375rem; background: var(--bg); border-radius: 4px; }
    .vinculacion-step { margin-top: 0.5rem; }
    .msg { margin-top: 0.5rem; padding: 0.375rem; border-radius: 4px; font-size: 0.75rem; background: #E8F5E9; color: var(--success); }
    .msg.error { background: #FFEBEE; color: var(--warn); }
    .resumen-card { padding: 1rem; }
    .resumen-card h4 { font-size: 0.875rem; margin-bottom: 0.75rem; }
    .cadena { display: flex; flex-direction: column; gap: 0.5rem; }
    .eslabon { border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
    .eslabon-cabecera { background: var(--bg); padding: 0.375rem 0.625rem; font-weight: 600; font-size: 0.75rem; }
    .eslabon-body { padding: 0.375rem 0.625rem; display: flex; flex-wrap: wrap; gap: 0.25rem; }
    .eslabon-hijo { display: flex; align-items: center; gap: 0.25rem; }
    .acp-tag { font-size: 0.6875rem; background: #E3F2FD; padding: 0.125rem 0.375rem; border-radius: 3px; }
    @media (max-width: 900px) { .builder-layout { grid-template-columns: 1fr 1fr; } }
  `]
})
export class ArticulacionComponent implements OnInit {
  // PDES
  pdesNodos: any[] = [];
  pdesFiltrados: any[] = [];
  pdesSelected: any = null;
  pdesSearch = '';

  // PEI
  ampsVinculadas: any[] = [];
  ampsDisponibles: any[] = [];
  ampSelected: any = null;
  ampAVincular = '';

  // POA
  acpsVinculadas: any[] = [];
  acpsDisponibles: any[] = [];
  acpSelected: any = null;
  acpAVincular = '';

  // Vincular
  tipoVinculo = 'pdes_pei';
  mensaje = '';
  mensajeError = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarPdes();
    this.cargarAmps();
    this.cargarAcps();
  }

  cargarPdes(): void {
    this.api.get<any>('/nodos-planificacion/', { nivel: 'accion_pdes' }).subscribe({
      next: (r: any) => {
        this.pdesNodos = r.results || r;
        this.filtrarPdes();
      },
    });
  }

  cargarAmps(): void {
    this.api.get<any>('/acciones-mediano-plazo/').subscribe({
      next: (r: any) => {
        this.ampsDisponibles = r.results || r;
      },
    });
  }

  cargarAcps(): void {
    this.api.get<any>('/acciones-corto-plazo/', { gestion: 2026 }).subscribe({
      next: (r: any) => {
        this.acpsDisponibles = r.results || r;
      },
    });
  }

  filtrarPdes(): void {
    const t = this.pdesSearch.toLowerCase();
    this.pdesFiltrados = this.pdesNodos.filter((n: any) =>
      !t || n.codigo?.toLowerCase().includes(t) || n.nombre?.toLowerCase().includes(t)
    );
  }

  seleccionarPdes(nodo: any): void {
    this.pdesSelected = nodo;
    this.mensaje = '';
    // Cargar AMPs vinculadas a este PDES
    this.api.get<any>('/acciones-mediano-plazo/', { 
      nodo_planificacion: nodo.id 
    }).subscribe({
      next: (r: any) => {
        this.ampsVinculadas = r.results || r;
        // Marcar cuántas POA tiene cada AMP
        this.ampsVinculadas.forEach((amp: any) => {
          this.api.get<any>('/acciones-corto-plazo/', { accion_mediano_plazo: amp.id })
            .subscribe((acps: any) => {
              amp.poa_count = (acps.results || acps).length;
            });
        });
      },
    });
  }

  seleccionarAmp(amp: any): void {
    this.ampSelected = amp;
    this.mensaje = '';
    this.api.get<any>('/acciones-corto-plazo/', { accion_mediano_plazo: amp.id })
      .subscribe({
        next: (r: any) => {
          this.acpsVinculadas = r.results || r;
        },
      });
  }

  crearAmp(): void {
    if (!this.pdesSelected) {
      this.mensaje = 'Seleccione una acción PDES primero';
      this.mensajeError = true;
      return;
    }
    const codigo = prompt('Código de la nueva AMP (ej: AMP-NUEVA-001):');
    if (!codigo) return;
    const nombre = prompt('Nombre de la AMP:');
    if (!nombre) return;

    this.api.post('/acciones-mediano-plazo/', {
      codigo, nombre,
      nodo_planificacion: this.pdesSelected.id,
      gestion_inicio: 2021,
      gestion_fin: 2025,
    }).subscribe({
      next: () => {
        this.mensaje = 'AMP creada correctamente';
        this.mensajeError = false;
        this.cargarAmps();
        this.seleccionarPdes(this.pdesSelected);
      },
      error: (e) => {
        this.mensaje = 'Error: ' + (e.message || e);
        this.mensajeError = true;
      },
    });
  }

  crearAcp(): void {
    if (!this.ampSelected) {
      this.mensaje = 'Seleccione una AMP primero';
      this.mensajeError = true;
      return;
    }
    const codigo = prompt('Código de la nueva ACP (ej: ACP-NUEVA-001):');
    if (!codigo) return;
    const nombre = prompt('Nombre de la ACP:');
    if (!nombre) return;
    const gestion = prompt('Gestión/año (ej: 2026):') || '2026';

    this.api.post('/acciones-corto-plazo/', {
      codigo, nombre, gestion: parseInt(gestion),
      accion_mediano_plazo: this.ampSelected.id,
    }).subscribe({
      next: () => {
        this.mensaje = 'ACP creada correctamente';
        this.mensajeError = false;
        this.cargarAcps();
        this.seleccionarAmp(this.ampSelected);
      },
      error: (e) => {
        this.mensaje = 'Error: ' + (e.message || e);
        this.mensajeError = true;
      },
    });
  }

  vincularPdesPei(): void {
    if (!this.pdesSelected || !this.ampAVincular) return;
    this.api.post('/articular/vincular/', {
      nodo_id: this.pdesSelected.id,
      amp_id: this.ampAVincular,
    }).subscribe({
      next: () => {
        this.mensaje = 'Vinculación PDES → PEI creada';
        this.mensajeError = false;
        this.seleccionarPdes(this.pdesSelected);
      },
      error: (e) => {
        this.mensaje = 'Error: ' + (e.message || e);
        this.mensajeError = true;
      },
    });
  }

  vincularPeiPoa(): void {
    if (!this.ampSelected || !this.acpAVincular) return;
    // Ya existe la FK accion_mediano_plazo en ACP
    this.api.patch('/acciones-corto-plazo/' + this.acpAVincular + '/', {
      accion_mediano_plazo: this.ampSelected.id,
    }).subscribe({
      next: () => {
        this.mensaje = 'Vinculación PEI → POA creada';
        this.mensajeError = false;
        this.seleccionarAmp(this.ampSelected);
      },
      error: (e) => {
        this.mensaje = 'Error: ' + (e.message || e);
        this.mensajeError = true;
      },
    });
  }

}
