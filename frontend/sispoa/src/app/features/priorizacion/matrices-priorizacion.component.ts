import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs';
import { PriorizacionService } from './priorizacion.service';

@Component({
  selector: 'app-matrices-priorizacion',
  standalone: false,
  template: `
    <div class="lienzo lienzo-datos">
      <div class="encabezado-pantalla">
        <div>
          <h2>Matriz acumulativa de priorización</h2>
          <p class="sub">
            Todo lo priorizado, consolidado por distrito, gestión {{ gestion }}.
          </p>
        </div>
        <div class="encabezado-acciones">
          <input class="form-control filtro" type="number" [(ngModel)]="gestion"
                 (change)="cargar()">
          <button class="btn btn-sm btn-excel" (click)="exportar()"
                  [disabled]="!filas.length">⬇ Excel</button>
        </div>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>
      <div class="sin-datos" *ngIf="cargando"><span>Cargando…</span></div>

      <ng-container *ngIf="!cargando">
        <div class="tabla-caja resumen" *ngIf="resumen.length">
          <table class="tabla tabla-compacta">
            <thead>
              <tr>
                <th>Distrito</th><th class="num">Actas</th>
                <th class="num">Proyectos</th><th class="num">Monto Bs</th>
                <th class="num">% del total</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let r of resumen">
                <td class="fuerte">{{ r.distrito }}</td>
                <td class="num">{{ r.actas }}</td>
                <td class="num">{{ r.proyectos }}</td>
                <td class="num">{{ r.monto | number:'1.0-0' }}</td>
                <td class="num">{{ porcentaje(r.monto) | number:'1.1-1' }}%</td>
              </tr>
              <tr class="total">
                <td>TOTAL</td>
                <td class="num">{{ totalActas }}</td>
                <td class="num">{{ filas.length }}</td>
                <td class="num">{{ totalMonto | number:'1.0-0' }}</td>
                <td class="num">100.0%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="tabla-caja detalle">
          <table class="tabla tabla-compacta">
            <thead>
              <tr>
                <th>Distrito</th><th>OTB / Junta vecinal</th><th>N°</th>
                <th>Proyecto</th><th>SISIN</th><th>Categoría programática</th>
                <th class="num">Monto Bs</th><th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let f of filas">
                <td>{{ f.distrito }}</td>
                <td>{{ f.otb }}</td>
                <td class="num">{{ f.orden }}</td>
                <td>{{ f.proyecto }}</td>
                <td>{{ f.sisin || '—' }}</td>
                <td>{{ f.categoria_programatica || '—' }}</td>
                <td class="num">{{ f.monto | number:'1.0-0' }}</td>
                <td><span class="estado" [ngClass]="'e-' + f.estado">{{ f.estado }}</span></td>
              </tr>
              <tr *ngIf="!filas.length">
                <td colspan="8">
                  <div class="sin-datos">
                    <span class="sin-datos-icono">📊</span>
                    <strong>Todavía no hay nada priorizado en la gestión {{ gestion }}</strong>
                    <span>La matriz se arma sola a medida que se registran las actas.</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </ng-container>
    </div>
  `,
  styles: [`
    .filtro { max-width: 130px; font-size: 0.8125rem; }
    .num { text-align: right; }
    .fuerte { font-weight: 600; }
    .resumen { margin-bottom: var(--e-3, 1.2rem); }
    .detalle { max-height: 60vh; overflow: auto; }
    tr.total td { font-weight: 700; background: var(--realce); }
    .estado { font-size: 0.5625rem; font-weight: 700; padding: 0.05rem 0.35rem; border-radius: 999px; }
    .e-BORRADOR { background: #E0E0E0; color: #37474F; }
    .e-VALIDADO { background: #BBDEFB; color: #0D47A1; }
    .e-OBSERVADO { background: #FFE0B2; color: #E65100; }
    .e-APROBADO { background: #C8E6C9; color: #1B5E20; }
    .btn-excel { background: #1B5E20; color: #fff; border: none; }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
  `],
})
export class MatricesPriorizacionComponent implements OnInit {
  filas: any[] = [];
  resumen: any[] = [];
  totalMonto = 0;
  gestion = 2027;
  cargando = true;
  error = '';

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void { this.cargar(); }

  get totalActas(): number {
    return this.resumen.reduce((t, r) => t + r.actas, 0);
  }

  porcentaje(monto: number): number {
    return this.totalMonto ? (monto * 100) / this.totalMonto : 0;
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.api.matrices(this.gestion)
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: (d: any) => {
          this.filas = d.filas ?? [];
          this.resumen = d.resumen ?? [];
          this.totalMonto = d.total_monto ?? 0;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudo cargar la matriz.';
          this.cdr.markForCheck();
        },
      });
  }

  private escapar(v: any): string {
    return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  }

  exportar(): void {
    const columnas = ['distrito', 'otb', 'presidente', 'fecha', 'orden',
                      'proyecto', 'sisin', 'categoria_programatica', 'monto',
                      'estado'];
    const cabecera = columnas.map(c =>
      `<th bgcolor="#1B5E20" style="background-color:#1B5E20;color:#FFFFFF;` +
      `mso-pattern:#1B5E20 none;padding:5px;font-size:10px">` +
      `${c.replace(/_/g, ' ').toUpperCase()}</th>`).join('');
    const cuerpo = this.filas.map(f =>
      '<tr>' + columnas.map(c =>
        `<td style="border:1px solid #ccc;padding:3px;font-size:9px">` +
        `${this.escapar(f[c])}</td>`).join('') + '</tr>').join('');
    const html = `<html xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="utf-8"></head><body>
      <table><tr><td style="font-size:12px;font-weight:bold">
        MATRIZ ACUMULATIVA DE PRIORIZACIÓN · POA ${this.gestion}</td></tr></table>
      <table style="border-collapse:collapse;font-family:Arial">
        <thead><tr>${cabecera}</tr></thead><tbody>${cuerpo}</tbody></table>
      </body></html>`;
    const url = URL.createObjectURL(
      new Blob(['﻿', html], { type: 'application/vnd.ms-excel;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `matriz-priorizacion-${this.gestion}.xls`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
