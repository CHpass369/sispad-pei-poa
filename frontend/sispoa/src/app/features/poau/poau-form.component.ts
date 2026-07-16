import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-poau-form',
  standalone: false,
  template: `
    <div class="poau-form">
      <div class="page-header">
        <h2>{{ esNuevo ? 'Nuevo POAU' : 'Editar POAU' }}</h2>
      </div>

      <!-- POAU Header Card -->
      <div class="card">
        <div class="form-2col">
          <div class="field"><label>Código</label><input [(ngModel)]="form.codigo" class="form-control"></div>
          <div class="field"><label>Gestión</label><input [(ngModel)]="form.gestion" type="number" class="form-control" value="2026"></div>
        </div>
        <div class="field"><label>Nombre del POAU</label><input [(ngModel)]="form.nombre" class="form-control"></div>
        <div class="field"><label>Descripción</label><textarea [(ngModel)]="form.descripcion" class="form-control" rows="2"></textarea></div>
        <div class="form-2col">
          <div class="field"><label>Unidad Responsable</label>
            <select [(ngModel)]="form.unidad" class="form-control">
              <option *ngFor="let u of unidades" [value]="u.id">{{ u.sigla || u.codigo }} — {{ u.nombre }}</option>
            </select>
          </div>
          <div class="field"><label>Producto Territorial (del PAD)</label>
            <select [(ngModel)]="form.producto_territorial" class="form-control">
              <option value="">— Ninguno —</option>
              <option *ngFor="let p of productos" [value]="p.id">{{ p.codigo }} — {{ p.nombre | slice:0:50 }}</option>
            </select>
          </div>
        </div>
        <div class="step-nav">
          <a routerLink="/poau" class="btn btn-outline">← Volver</a>
          <button class="btn btn-primary" [disabled]="!form.nombre" (click)="guardar()">Guardar POAU</button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass==='error'">{{ msg }}</div>
      </div>

      <!-- Actividades trimestrales card -->
      <div class="card" *ngIf="!esNuevo && form.actividades?.length">
        <h3 class="card-title">Actividades — Programación Trimestral</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th class="col-q">Q1</th>
                <th class="col-q">Q2</th>
                <th class="col-q">Q3</th>
                <th class="col-q">Q4</th>
                <th class="col-total">Total</th>
                <th class="col-avance">% Avance</th>
                <th class="col-accion">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let act of form.actividades">
                <td><strong>{{ act.codigo }}</strong></td>
                <td class="cell-nombre">{{ act.nombre | slice:0:60 }}</td>
                <td><input type="number" min="0" step="0.0001"
                      [(ngModel)]="act.meta_q1" (ngModelChange)="act._total = sumaTrimestres(act)"
                      class="form-control input-q"></td>
                <td><input type="number" min="0" step="0.0001"
                      [(ngModel)]="act.meta_q2" (ngModelChange)="act._total = sumaTrimestres(act)"
                      class="form-control input-q"></td>
                <td><input type="number" min="0" step="0.0001"
                      [(ngModel)]="act.meta_q3" (ngModelChange)="act._total = sumaTrimestres(act)"
                      class="form-control input-q"></td>
                <td><input type="number" min="0" step="0.0001"
                      [(ngModel)]="act.meta_q4" (ngModelChange)="act._total = sumaTrimestres(act)"
                      class="form-control input-q"></td>
                <td class="cell-total">{{ act._total | number:'1.2-2' }}</td>
                <td class="cell-avance">{{ act.avance }}%</td>
                <td>
                  <button class="btn btn-primary btn-sm"
                          (click)="guardarActividad(act)"
                          [disabled]="act._guardando">
                    {{ act._guardando ? 'Guardando…' : 'Guardar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div *ngIf="actividadesMsg" class="msg-box" [class.error]="actividadesMsgClase==='error'"
             [class.success]="actividadesMsgClase==='success'">{{ actividadesMsg }}</div>
      </div>
      <div class="card" *ngIf="!esNuevo && (!form.actividades || form.actividades.length === 0)">
        <p class="text-secondary">Este POAU no tiene actividades registradas. Agréguelas desde el detalle del POAU.</p>
      </div>
    </div>
  `,
  styles: [`
    .poau-form { max-width:960px; margin:0 auto; }
    .page-header { margin-bottom:1rem; }
    .form-2col { display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; }
    .field { margin-bottom:0.75rem; }
    .field label { display:block; font-size:0.75rem; font-weight:500; color:var(--text-secondary); margin-bottom:0.25rem; }
    .step-nav { display:flex; justify-content:space-between; margin-top:1rem; }
    .card-title { font-size:1rem; font-weight:600; margin-bottom:0.75rem; }
    .table-wrap { overflow-x:auto; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:0.4rem 0.5rem; text-align:left; border-bottom:1px solid var(--border); font-size:0.8125rem; }
    th { font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase; white-space:nowrap; }
    .col-q { width:90px; text-align:center; }
    .col-total { width:90px; text-align:center; }
    .col-avance { width:80px; text-align:center; }
    .col-accion { width:90px; text-align:center; }
    .cell-nombre { max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .input-q { width:80px; text-align:right; font-size:0.8125rem; padding:0.25rem 0.4rem; }
    .cell-total { text-align:right; font-weight:600; }
    .cell-avance { text-align:center; }
    .msg-box { margin-top:0.5rem; padding:0.5rem; border-radius:4px; font-size:0.8125rem; }
    .msg-box.error { background:#FFEBEE; color:var(--warn); }
    .msg-box.success { background:#E8F5E9; color:var(--success); }
    .btn-sm { font-size:0.75rem; padding:0.25rem 0.5rem; }
  `]
})
export class PoauFormComponent implements OnInit {
  esNuevo = true;
  form: any = { codigo:'', nombre:'', descripcion:'', gestion:2026, unidad:'', producto_territorial:'', actividades:[] };
  unidades: any[] = [];
  productos: any[] = [];
  msg = ''; msgClass = '';
  actividadesMsg = ''; actividadesMsgClase = '';

  constructor(
    private api: ApiService, private route: ActivatedRoute, private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarUnidades();
    this.cargarProductos();
    const id = this.route.snapshot.params['id'];
    if (id) { this.esNuevo = false; this.cargar(id); }
  }

  cargarUnidades(): void {
    this.api.get<any>('/unidades/', { gestion: 2026, activo: true }).subscribe({
      next: (r: any) => this.unidades = r.results || r
    });
  }
  cargarProductos(): void {
    this.api.get<any>('/pad/productos-territoriales/').subscribe({
      next: (r: any) => this.productos = r.results || r
    });
  }
  cargar(id: string): void {
    this.api.get<any>('/poau/poaus/' + id + '/').subscribe({
      next: (r: any) => {
        this.form = r;
        // Inicializar _total por fila para el binding reactivo
        if (this.form.actividades) {
          this.form.actividades.forEach((a: any) => {
            a._total = this.sumaTrimestres(a);
          });
        }
      }
    });
  }
  guardar(): void {
    const req = this.esNuevo
      ? this.api.post('/poau/poaus/', this.form)
      : this.api.put('/poau/poaus/' + this.route.snapshot.params['id'] + '/', this.form);
    req.subscribe({
      next: () => { this.router.navigate(['/poau']); },
      error: (e: any) => { this.msg = 'Error: ' + (e.message || e); this.msgClass = 'error'; }
    });
  }

  sumaTrimestres(act: any): number {
    const q1 = parseFloat(act.meta_q1) || 0;
    const q2 = parseFloat(act.meta_q2) || 0;
    const q3 = parseFloat(act.meta_q3) || 0;
    const q4 = parseFloat(act.meta_q4) || 0;
    return q1 + q2 + q3 + q4;
  }

  guardarActividad(act: any): void {
    act._guardando = true;
    this.actividadesMsg = '';
    const payload: any = {};
    if (act.meta_q1 !== undefined) payload.meta_q1 = act.meta_q1;
    if (act.meta_q2 !== undefined) payload.meta_q2 = act.meta_q2;
    if (act.meta_q3 !== undefined) payload.meta_q3 = act.meta_q3;
    if (act.meta_q4 !== undefined) payload.meta_q4 = act.meta_q4;
    if (act.accion_corto_plazo !== undefined) payload.accion_corto_plazo = act.accion_corto_plazo;

    this.api.patch('/poau/actividades/' + act.id + '/', payload).subscribe({
      next: (r: any) => {
        act._guardando = false;
        // Actualizar con datos frescos del server
        act.meta_q1 = r.meta_q1;
        act.meta_q2 = r.meta_q2;
        act.meta_q3 = r.meta_q3;
        act.meta_q4 = r.meta_q4;
        act.avance = r.avance;
        act._total = this.sumaTrimestres(act);
        this.actividadesMsg = 'Actividad ' + act.codigo + ' guardada correctamente';
        this.actividadesMsgClase = 'success';
        setTimeout(() => this.actividadesMsg = '', 3000);
      },
      error: (e: any) => {
        act._guardando = false;
        const detail = e.error && (e.error.detail || JSON.stringify(e.error));
        this.actividadesMsg = 'Error en ' + act.codigo + ': ' + (detail || e.message || e);
        this.actividadesMsgClase = 'error';
      }
    });
  }
}
