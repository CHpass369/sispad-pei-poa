import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { environment } from '../../../environments/environment';
import {
  SisPoaService,
  TechoV2,
  RecursoTechoV2,
  GastoObligatorioV2,
  ResumenTecho,
} from './sis-poa.service';
import { HttpClient } from '@angular/common/http';

interface FuenteV1 { id: string; codigo: string; denominacion: string; }
interface OrganismoV1 { id: string; codigo: string; denominacion: string; }
interface GestionV1 { id: string; anio: number; estado: string; }

@Component({
  standalone: false,
  selector: 'app-sis-poa-techos',
  template: `
    <div class="page-header">
      <h2>Techos Presupuestarios</h2>
      <p class="text-secondary">Parámetro madre del año fiscal — recursos, gastos obligatorios y control de distribución</p>
    </div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <!-- Gestión fiscal -->
    <div class="card">
      <h3>Gestión fiscal</h3>
      <div class="fila">
        <div class="campo">
          <label>Gestión actual</label>
          <select [(ngModel)]="gestionSeleccionada" (change)="cargarTechos()" class="input">
            <option *ngFor="let g of gestiones" [value]="g.anio">{{ g.anio }} ({{ g.estado }})</option>
          </select>
        </div>
        <div class="campo" *ngIf="puedeGestionar">
          <label>Año nueva gestión</label>
          <input [(ngModel)]="nuevaGestion" type="number" class="input" placeholder="2028" />
        </div>
        <div class="campo" *ngIf="puedeGestionar">
          <label>&nbsp;</label>
          <button class="btn btn-outline" (click)="crearGestion()">+ Crear gestión</button>
        </div>
      </div>
    </div>

    <!-- Crear techo -->
    <form *ngIf="puedeGestionar" (ngSubmit)="crearTecho()" class="card">
      <h3>Nuevo techo — gestión {{ gestionSeleccionada }}</h3>
      <div class="fila">
        <div class="campo">
          <label>Monto total (Bs)</label>
          <input [(ngModel)]="formTecho.monto_total" name="mt" type="number" required class="input" />
        </div>
        <div class="campo">
          <label>Fuente</label>
          <select [(ngModel)]="formTecho.fuente" name="fuente" required class="input">
            <option *ngFor="let f of fuentes" [value]="f.id">{{ f.codigo }} — {{ f.denominacion }}</option>
          </select>
        </div>
        <div class="campo">
          <label>Concepto</label>
          <input [(ngModel)]="formTecho.concepto" name="concepto" class="input" placeholder="Techo POA" />
        </div>
        <div class="campo">
          <label>&nbsp;</label>
          <button type="submit" class="btn btn-primary">+ Techo</button>
        </div>
      </div>
    </form>

    <!-- Listado de techos -->
    <div class="card" *ngIf="techos.length">
      <h3>Techos de la gestión {{ gestionSeleccionada }}</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Fuente</th><th>Concepto</th><th>Monto total</th>
            <th>Gastos oblig.</th><th>Distribuido</th><th>Saldo disponible</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let t of techos" [class.seleccionado]="techoSeleccionado?.id === t.id"
              (click)="seleccionarTecho(t)">
            <td>{{ t.fuente_codigo }} — {{ t.fuente_nombre }}</td>
            <td>{{ t.concepto || '—' }}</td>
            <td>Bs {{ t.monto_total }}</td>
            <td>Bs {{ t.total_gastos_obligatorios ?? '0' }}</td>
            <td>Bs {{ t.monto_distribuido ?? '0' }}</td>
            <td><strong class="{{ (t.saldo_disponible ?? 0) < 0 ? 'excede' : 'ok' }}">Bs {{ t.saldo_disponible ?? '0' }}</strong></td>
            <td>
              <button class="btn btn-sm" *ngIf="puedeGestionar" (click)="eliminarTecho(t); $event.stopPropagation()">🗑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div *ngIf="!cargando && techos.length === 0" class="empty">
      Sin techos para la gestión {{ gestionSeleccionada }}
    </div>

    <!-- Detalle del techo -->
    <div class="card" *ngIf="techoSeleccionado">
      <h3>Detalle del techo — Bs {{ techoSeleccionado.monto_total }}</h3>
      <div class="resumen">
        <div class="chip verde">Saldo disponible: Bs {{ resumen?.saldo_disponible ?? techoSeleccionado.saldo_disponible }}</div>
        <div class="chip gris">Gastos obligatorios: Bs {{ resumen?.total_gastos_obligatorios ?? '0' }}</div>
        <div class="chip gris">Distribuido: Bs {{ resumen?.monto_distribuido ?? '0' }}</div>
      </div>

      <h4>Recursos (ingresos del techo)</h4>
      <div class="mini-fila" *ngIf="puedeGestionar">
        <input [(ngModel)]="formRecurso.rubro" placeholder="Rubro" class="input input-sm" />
        <input [(ngModel)]="formRecurso.rubro_descripcion" placeholder="Descripción rubro" class="input input-sm" />
        <select [(ngModel)]="formRecurso.organismo" class="input input-sm">
          <option *ngFor="let o of organismos" [value]="o.id">{{ o.codigo }} — {{ o.denominacion }}</option>
        </select>
        <input [(ngModel)]="formRecurso.concepto" placeholder="Concepto" class="input input-sm" />
        <input [(ngModel)]="formRecurso.monto" type="number" placeholder="Monto" class="input input-sm" />
        <button class="btn btn-primary btn-sm" (click)="crearRecurso()">+ Recurso</button>
      </div>
      <table class="data-table" *ngIf="recursos.length">
        <thead><tr><th>Rubro</th><th>Concepto</th><th>Organismo</th><th>Monto</th><th></th></tr></thead>
        <tbody>
          <tr *ngFor="let r of recursos">
            <td>{{ r.rubro }} — {{ r.rubro_descripcion }}</td>
            <td>{{ r.concepto }}</td>
            <td>{{ r.organismo_codigo }}</td>
            <td>Bs {{ r.monto }}</td>
            <td><button class="btn btn-sm" *ngIf="puedeGestionar" (click)="eliminarRecurso(r)">🗑</button></td>
          </tr>
        </tbody>
      </table>

      <h4>Gastos obligatorios (reservas)</h4>
      <div class="mini-fila" *ngIf="puedeGestionar">
        <input [(ngModel)]="formGasto.denominacion" placeholder="Denominación" class="input input-sm" />
        <input [(ngModel)]="formGasto.base_legal" placeholder="Base legal" class="input input-sm" />
        <select [(ngModel)]="formGasto.organismo" class="input input-sm">
          <option *ngFor="let o of organismos" [value]="o.id">{{ o.codigo }} — {{ o.denominacion }}</option>
        </select>
        <input [(ngModel)]="formGasto.monto" type="number" placeholder="Monto" class="input input-sm" />
        <button class="btn btn-primary btn-sm" (click)="crearGastoObligatorio()">+ Gasto obligatorio</button>
      </div>
      <table class="data-table" *ngIf="gastosObligatorios.length">
        <thead><tr><th>Denominación</th><th>Base legal</th><th>Organismo</th><th>Monto</th><th></th></tr></thead>
        <tbody>
          <tr *ngFor="let g of gastosObligatorios">
            <td>{{ g.denominacion }}</td>
            <td>{{ g.base_legal }}</td>
            <td>{{ g.organismo }}</td>
            <td>Bs {{ g.monto }}</td>
            <td><button class="btn btn-sm" *ngIf="puedeGestionar" (click)="eliminarGastoObligatorio(g)">🗑</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .card h4 { margin: 1rem 0 0.5rem; font-size: 0.875rem; }
    .fila, .mini-fila { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: flex-end; }
    .mini-fila { margin-bottom: 0.5rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 160px; }
    .input-sm { min-width: 120px; padding: 0.375rem; font-size: 0.8125rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-outline { background: transparent; border: 1px solid var(--primary); color: var(--primary); }
    .btn-sm { background: #FFEBEE; color: #C62828; padding: 0.25rem 0.5rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.5rem 0.625rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .data-table tbody tr { cursor: pointer; }
    .data-table tbody tr:hover td { background: #F0F7F3; }
    .seleccionado td { background: #E3F2FD !important; }
    .resumen { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
    .chip { padding: 0.25rem 0.625rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .verde { background: #E8F5E9; color: #2E7D32; }
    .gris { background: #F5F5F5; color: var(--text-secondary); }
    .ok { color: #2E7D32; }
    .excede { color: #C62828; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class SisPoaTechosComponent implements OnInit {
  gestiones: GestionV1[] = [];
  gestionSeleccionada = 2027;
  nuevaGestion = 2028;
  fuentes: FuenteV1[] = [];
  organismos: OrganismoV1[] = [];
  techos: TechoV2[] = [];
  techoSeleccionado: TechoV2 | null = null;
  recursos: RecursoTechoV2[] = [];
  gastosObligatorios: GastoObligatorioV2[] = [];
  resumen: ResumenTecho | null = null;
  cargando = true;
  error = '';
  mensaje = '';

  formTecho: { monto_total: number | null; fuente: string; concepto: string } = {
    monto_total: null, fuente: '', concepto: '',
  };
  formRecurso: { rubro: string; rubro_descripcion: string; organismo: string; concepto: string; monto: number | null } = {
    rubro: '', rubro_descripcion: '', organismo: '', concepto: '', monto: null,
  };
  formGasto: { denominacion: string; base_legal: string; organismo: string; monto: number | null } = {
    denominacion: '', base_legal: '', organismo: '', monto: null,
  };

  constructor(
    private service: SisPoaService,
    private http: HttpClient,
    private permissions: PermissionsService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage', 'sis_poa.formulate']);
  }

  ngOnInit(): void {
    this.cargarGestiones();
    this.http.get<{ results: FuenteV1[] }>(`${environment.apiUrl}/fuentes/`).subscribe({
      next: (data) => { this.fuentes = data.results ?? []; },
      error: () => undefined,
    });
    this.http.get<{ results: OrganismoV1[] }>(`${environment.apiUrl}/organismos/`).subscribe({
      next: (data) => { this.organismos = data.results ?? []; },
      error: () => undefined,
    });
  }

  cargarGestiones(): void {
    this.http.get<{ results: GestionV1[] }>(`${environment.apiUrl}/gestiones/`).subscribe({
      next: (data) => {
        this.gestiones = data.results ?? [];
        if (this.gestiones.length) {
          this.gestionSeleccionada = this.gestiones[0].anio;
        }
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al cargar gestiones'; this.cargando = false; },
    });
  }

  crearGestion(): void {
    if (!this.nuevaGestion) { this.error = 'Indique el año de la nueva gestión'; return; }
    if (this.gestiones.some(g => g.anio === this.nuevaGestion)) {
      this.error = `La gestión ${this.nuevaGestion} ya existe`;
      return;
    }
    this.error = '';
    this.http.post<GestionV1>(`${environment.apiUrl}/gestiones/`, { anio: this.nuevaGestion }).subscribe({
      next: () => {
        this.mensaje = `Gestión ${this.nuevaGestion} creada`;
        this.cargarGestiones();
      },
      error: () => { this.error = 'Error al crear la gestión'; },
    });
  }

  cargarTechos(): void {
    this.cargando = true;
    this.techoSeleccionado = null;
    this.service.listarTechos({ gestion: this.gestionSeleccionada }).subscribe({
      next: (data) => {
        this.techos = data.results;
        this.cargando = false;
        if (this.techos.length) this.seleccionarTecho(this.techos[0]);
      },
      error: () => { this.error = 'Error al cargar techos'; this.cargando = false; },
    });
  }

  crearTecho(): void {
    const { monto_total, fuente, concepto } = this.formTecho;
    if (!monto_total || !fuente) {
      this.error = 'Monto y fuente son requeridos';
      return;
    }
    this.error = '';
    this.service.crearTecho({
      gestion: this.gestionSeleccionada,
      monto_total: String(monto_total),
      fuente,
      concepto,
    } as Partial<TechoV2>).subscribe({
      next: (t) => {
        this.mensaje = 'Techo registrado';
        this.formTecho = { monto_total: null, fuente: '', concepto: '' };
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al crear el techo'; },
    });
  }

  eliminarTecho(t: TechoV2): void {
    if (!confirm(`¿Eliminar el techo de ${t.gestion} (${t.fuente_codigo})?`)) return;
    this.service.eliminarTecho(t.id).subscribe({
      next: () => { this.mensaje = 'Techo eliminado'; this.cargarTechos(); },
      error: () => { this.error = 'Error al eliminar el techo'; },
    });
  }

  seleccionarTecho(t: TechoV2): void {
    this.techoSeleccionado = t;
    this.cargarRecursos(t.id);
    this.cargarGastos(t.id);
    this.cargarResumen(t.id);
  }

  cargarResumen(id: string): void {
    this.service.resumenTecho(id).subscribe({
      next: (r) => { this.resumen = r; },
      error: () => undefined,
    });
  }

  cargarRecursos(techoId: string): void {
    this.service.listarRecursos({ techo: techoId }).subscribe({
      next: (r) => { this.recursos = r; },
      error: () => undefined,
    });
  }

  crearRecurso(): void {
    if (!this.techoSeleccionado) return;
    const { rubro, rubro_descripcion, organismo, concepto, monto } = this.formRecurso;
    if (!concepto || !monto) { this.error = 'Concepto y monto son requeridos'; return; }
    this.error = '';
    const fuente = this.techoSeleccionado.fuente;
    this.service.crearRecurso({
      techo: this.techoSeleccionado.id, rubro, rubro_descripcion,
      organismo, concepto, monto: String(monto), fuente,
    } as Partial<RecursoTechoV2>).subscribe({
      next: () => {
        this.mensaje = 'Recurso agregado';
        this.formRecurso = { rubro: '', rubro_descripcion: '', organismo: '', concepto: '', monto: null };
        this.cargarRecursos(this.techoSeleccionado!.id);
        this.cargarResumen(this.techoSeleccionado!.id);
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al agregar recurso'; },
    });
  }

  eliminarRecurso(r: RecursoTechoV2): void {
    this.service.eliminarRecurso(r.id).subscribe({
      next: () => {
        this.cargarRecursos(this.techoSeleccionado!.id);
        this.cargarResumen(this.techoSeleccionado!.id);
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al eliminar recurso'; },
    });
  }

  cargarGastos(techoId: string): void {
    this.service.listarGastosObligatorios({ techo: techoId }).subscribe({
      next: (g) => { this.gastosObligatorios = g; },
      error: () => undefined,
    });
  }

  crearGastoObligatorio(): void {
    if (!this.techoSeleccionado) return;
    const { denominacion, base_legal, organismo, monto } = this.formGasto;
    if (!denominacion || !monto) { this.error = 'Denominación y monto son requeridos'; return; }
    this.error = '';
    const fuente = this.techoSeleccionado.fuente;
    this.service.crearGastoObligatorio({
      techo: this.techoSeleccionado.id, denominacion, base_legal,
      organismo, monto: String(monto), fuente,
    } as Partial<GastoObligatorioV2>).subscribe({
      next: () => {
        this.mensaje = 'Gasto obligatorio agregado';
        this.formGasto = { denominacion: '', base_legal: '', organismo: '', monto: null };
        this.cargarGastos(this.techoSeleccionado!.id);
        this.cargarResumen(this.techoSeleccionado!.id);
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al agregar gasto obligatorio'; },
    });
  }

  eliminarGastoObligatorio(g: GastoObligatorioV2): void {
    this.service.eliminarGastoObligatorio(g.id).subscribe({
      next: () => {
        this.cargarGastos(this.techoSeleccionado!.id);
        this.cargarResumen(this.techoSeleccionado!.id);
        this.cargarTechos();
      },
      error: () => { this.error = 'Error al eliminar gasto obligatorio'; },
    });
  }
}
