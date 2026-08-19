import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  PreinversionService, TDR, TDRActividad, TDRItemPresupuesto, TDRPersonal, TDRProducto,
} from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-tdr',
  template: `
    <div class="page-header">
      <a [routerLink]="['/sis-pro/preinversion', proyectoId]" class="volver">← Expediente</a>
      <h2>Asistente TDR — Términos de Referencia del EDTP</h2>
      <p class="text-secondary">Parte B del ITCP · presupuesto referencial con memorias de cálculo</p>
    </div>
    @if (cargando) {
      <div class="loading">Cargando TDR...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (tdr && !cargando) {
      <div class="card">
        <h3>Información general <span class="badge">{{ tdr.estado }}</span> v{{ tdr.version }}</h3>
        <div class="grid">
          <label>Justificación
            <textarea [(ngModel)]="tdr.justificacion" name="j" rows="2" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Objetivos
            <textarea [(ngModel)]="tdr.objetivos" name="o" rows="2" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Alcance
            <textarea [(ngModel)]="tdr.alcance" name="a" rows="2" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Actores y responsabilidades
            <textarea [(ngModel)]="tdr.actores_responsabilidades" name="ar" rows="2" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Metodología
            <textarea [(ngModel)]="tdr.metodologia" name="m" rows="2" class="input" (change)="guardar()"></textarea>
          </label>
          <div class="fila">
            <label>Duración (días)
              <input type="number" [(ngModel)]="tdr.duracion_dias" name="d" class="input" (change)="guardar()" />
            </label>
            <label>Presupuesto referencial (Bs)
              <input type="number" [(ngModel)]="tdr.presupuesto_referencial" name="pr" class="input" (change)="guardar()" />
            </label>
          </div>
        </div>
      </div>
    }
    
    @if (tdr && !cargando) {
      <div class="card">
        <h3>Actividades</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarActividad()" class="form-inline">
            <input [(ngModel)]="actividad.codigo" name="ac" placeholder="Código" required class="input" />
            <input [(ngModel)]="actividad.descripcion" name="ad" placeholder="Descripción" required class="input" />
            <input [(ngModel)]="actividad.duracion_dias" name="add" type="number" placeholder="Días" class="input" />
            <button type="submit" class="btn btn-primary">+ Actividad</button>
          </form>
        }
        <table class="data-table">
          <tbody>
            @for (a of tdr.actividades; track a) {
              <tr>
                <td><span class="badge">{{ a.codigo }}</span></td>
                <td>{{ a.descripcion }}</td>
                <td>{{ a.duracion_dias }} días</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (tdr && !cargando) {
      <div class="card">
        <h3>Productos</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarProducto()" class="form-inline">
            <input [(ngModel)]="producto.codigo" name="pc" placeholder="Código" required class="input" />
            <input [(ngModel)]="producto.nombre" name="pn" placeholder="Nombre" required class="input" />
            <input [(ngModel)]="producto.dia_entrega" name="pd" type="number" placeholder="Día entrega" class="input" />
            <button type="submit" class="btn btn-primary">+ Producto</button>
          </form>
        }
        <table class="data-table">
          <tbody>
            @for (p of tdr.productos; track p) {
              <tr>
                <td><span class="badge">{{ p.codigo }}</span></td>
                <td>{{ p.nombre }}</td>
                <td>día {{ p.dia_entrega }}</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (tdr && !cargando) {
      <div class="card">
        <h3>Personal técnico</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarPersonal()" class="form-inline">
            <input [(ngModel)]="personal.rol" name="prr" placeholder="Rol" required class="input" />
            <input [(ngModel)]="personal.cantidad" name="prc" type="number" placeholder="Cantidad" class="input" />
            <input [(ngModel)]="personal.meses" name="prm" type="number" placeholder="Meses" class="input" />
            <input [(ngModel)]="personal.tarifa_mensual" name="prt" type="number" placeholder="Tarifa mensual" class="input" />
            <button type="submit" class="btn btn-primary">+ Personal</button>
          </form>
        }
        <table class="data-table">
          <thead>
            <tr><th>Rol</th><th>Cant.</th><th>Meses</th><th>Tarifa</th><th>Subtotal</th></tr>
          </thead>
          <tbody>
            @for (p of tdr.personal; track p) {
              <tr>
                <td>{{ p.rol }}</td><td>{{ p.cantidad }}</td><td>{{ p.meses }}</td>
                <td>Bs {{ p.tarifa_mensual }}</td><td><strong>Bs {{ p.subtotal }}</strong></td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (tdr && !cargando) {
      <div class="card">
        <h3>Presupuesto referencial</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarItem()" class="form-inline">
            <input [(ngModel)]="item.categoria" name="ic" placeholder="Categoría" required class="input" />
            <input [(ngModel)]="item.descripcion" name="id" placeholder="Descripción" required class="input" />
            <input [(ngModel)]="item.cantidad" name="iq" type="number" placeholder="Cantidad" class="input" />
            <input [(ngModel)]="item.unidad" name="iu" placeholder="Unidad" class="input" />
            <input [(ngModel)]="item.costo_unitario" name="icu" type="number" placeholder="Costo unitario" class="input" />
            <button type="submit" class="btn btn-primary">+ Item</button>
          </form>
        }
        <table class="data-table">
          <thead>
            <tr><th>Categoría</th><th>Descripción</th><th>Cant.</th><th>Unidad</th><th>C.U.</th><th>Subtotal</th></tr>
          </thead>
          <tbody>
            @for (i of tdr.items_presupuesto; track i) {
              <tr>
                <td>{{ i.categoria }}</td><td>{{ i.descripcion }}</td><td>{{ i.cantidad }}</td>
                <td>{{ i.unidad }}</td><td>Bs {{ i.costo_unitario }}</td>
                <td><strong>Bs {{ i.subtotal }}</strong></td>
              </tr>
            }
          </tbody>
        </table>
        <div class="total"><strong>Total referencial: Bs {{ totalReferencial }}</strong></div>
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .volver { display: inline-block; font-size: 0.8125rem; color: var(--text-secondary); text-decoration: none; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; }
    .grid label, .fila label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }
    .fila { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; font-family: inherit; }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .data-table th, 
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .total { margin-top: 0.75rem; font-size: 0.875rem; text-align: right; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class PreinversionTdrComponent implements OnInit {
  proyectoId = '';
  tdr: TDR | null = null;
  cargando = true;
  error = '';
  mensaje = '';
  actividad: Partial<TDRActividad> = { duracion_dias: 0 };
  producto: Partial<TDRProducto> = { dia_entrega: 0 };
  personal: Partial<TDRPersonal> = { cantidad: 1, meses: '1', tarifa_mensual: '0' };
  item: Partial<TDRItemPresupuesto> = { cantidad: '1', unidad: 'global', costo_unitario: '0' };

  constructor(
    private route: ActivatedRoute,
    public service: PreinversionService,
    private permissions: PermissionsService,
  ) {}

  get puedeEditar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.project.create', 'sis_pro.project.edit']);
  }

  get totalReferencial(): string {
    return this.tdr?.items_presupuesto.reduce((s, i) => s + (Number(i.subtotal) || 0), 0).toFixed(2) ?? '0.00';
  }

  ngOnInit(): void {
    this.proyectoId = this.route.snapshot.paramMap.get('id')!;
    this.service.listarTdrs({ proyecto: this.proyectoId }).subscribe({
      next: (data) => {
        const tdr = data.results[0];
        if (!tdr) {
          this.error = 'Este proyecto no tiene TDR. Inicialícelo desde el expediente.';
          this.cargando = false;
          return;
        }
        this.tdr = tdr;
        this.cargando = false;
      },
      error: () => { this.error = 'Error al cargar el TDR'; this.cargando = false; },
    });
  }

  private notificar(msg: string): void {
    this.mensaje = msg;
    if (this.tdr) {
      this.service.obtenerTdr(this.tdr.id).subscribe({
        next: (tdr) => { this.tdr = tdr; },
        error: () => undefined,
      });
    }
  }

  guardar(): void {
    if (!this.tdr) return;
    this.service.actualizarTdr(this.tdr.id, {
      justificacion: this.tdr.justificacion,
      objetivos: this.tdr.objetivos,
      alcance: this.tdr.alcance,
      actores_responsabilidades: this.tdr.actores_responsabilidades,
      metodologia: this.tdr.metodologia,
      duracion_dias: this.tdr.duracion_dias,
      presupuesto_referencial: this.tdr.presupuesto_referencial,
    }).subscribe({
      next: () => { this.mensaje = 'TDR guardado'; },
      error: () => this.error = 'Error al guardar el TDR',
    });
  }

  agregarActividad(): void {
    if (!this.tdr || !this.actividad.codigo || !this.actividad.descripcion) return;
    this.service.crearActividadTdr({
      tdr: this.tdr.id, codigo: this.actividad.codigo,
      descripcion: this.actividad.descripcion, duracion_dias: this.actividad.duracion_dias ?? 0,
    }).subscribe({
      next: () => {
        this.actividad = { duracion_dias: 0 };
        this.notificar('Actividad agregada');
      },
      error: () => this.error = 'Error al agregar la actividad',
    });
  }

  agregarProducto(): void {
    if (!this.tdr || !this.producto.codigo || !this.producto.nombre) return;
    this.service.crearProductoTdr({
      tdr: this.tdr.id, codigo: this.producto.codigo,
      nombre: this.producto.nombre, dia_entrega: this.producto.dia_entrega ?? 0,
    }).subscribe({
      next: () => {
        this.producto = { dia_entrega: 0 };
        this.notificar('Producto agregado');
      },
      error: () => this.error = 'Error al agregar el producto',
    });
  }

  agregarPersonal(): void {
    if (!this.tdr || !this.personal.rol) return;
    this.service.crearPersonalTdr({
      tdr: this.tdr.id, rol: this.personal.rol,
      cantidad: this.personal.cantidad ?? 1,
      meses: String(this.personal.meses ?? '1'),
      tarifa_mensual: String(this.personal.tarifa_mensual ?? '0'),
    }).subscribe({
      next: () => {
        this.personal = { cantidad: 1, meses: '1', tarifa_mensual: '0' };
        this.notificar('Personal agregado');
      },
      error: () => this.error = 'Error al agregar personal',
    });
  }

  agregarItem(): void {
    if (!this.tdr || !this.item.descripcion || !this.item.categoria) return;
    this.service.crearItemPresupuestoTdr({
      tdr: this.tdr.id, categoria: this.item.categoria,
      descripcion: this.item.descripcion,
      cantidad: String(this.item.cantidad ?? '1'),
      unidad: this.item.unidad ?? 'global',
      costo_unitario: String(this.item.costo_unitario ?? '0'),
    }).subscribe({
      next: () => {
        this.item = { cantidad: '1', unidad: 'global', costo_unitario: '0' };
        this.notificar('Item de presupuesto agregado');
      },
      error: () => this.error = 'Error al agregar el item',
    });
  }
}
