import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import {
  MatricesPadService,
  BorradorMatrizPAD,
} from './matrices-pad.service';

@Component({
  selector: 'app-matrices-pad-home',
  standalone: false,
  template: `
    <div class="mpx-page">
      <div class="page-header">
        <div>
          <h2>Matrices PAD</h2>
          <p class="text-secondary">
            Wizard de 11 pasos (sin articulación PEI) con guardado incremental
            por paso; los visualizadores Matriz A y Matriz B se llenan en vivo
            desde el backend.
          </p>
        </div>
        <div class="header-actions">
          <a routerLink="acumulada" class="btn btn-outline">📊 Matrices acumuladas (gestión)</a>
          <a routerLink="nuevo" class="btn btn-primary">+ Nueva Matriz PAD</a>
        </div>
      </div>
    
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card table-card">
        <div class="table-scroll">
          <table class="matriz-table">
            <thead>
              <tr>
                <th>Gestión</th>
                <th>Estado</th>
                <th>Fecha de creación</th>
                <th>Resultado materializado</th>
                <th class="actions-col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (b of borradores; track b) {
                <tr>
                  <td>{{ b.gestion }}</td>
                  <td>
                    <span class="badge"
                      [class.badge-success]="b.estado === 'COMPLETO'"
                      [class.badge-warning]="b.estado === 'BORRADOR'">
                      {{ b.estado }}
                    </span>
                  </td>
                  <td>{{ b.created_at ? (b.created_at | date: 'dd/MM/yyyy HH:mm') : '—' }}</td>
                  <td>
                    <span class="codigo">{{ b.id_resultado_pad ? (b.id_resultado_pad | slice: 0: 8) : '—' }}</span>
                  </td>
                  <td class="actions-col">
                    <a [routerLink]="['nuevo', b.id]" class="btn btn-sm btn-outline">Continuar</a>
                    <a [routerLink]="[b.id, 'matriz-a']" class="btn btn-sm btn-outline">Matriz A</a>
                    <a [routerLink]="[b.id, 'matriz-b']" class="btn btn-sm btn-outline">Matriz B</a>
                    <button class="btn btn-sm btn-danger-ghost" (click)="eliminar(b)" [disabled]="b.estado === 'COMPLETO'">
                      Eliminar
                    </button>
                  </td>
                </tr>
              }
              @if (cargando) {
                <tr>
                  <td colspan="5" class="empty-cell">Cargando borradores...</td>
                </tr>
              }
              @if (!cargando && borradores.length === 0) {
                <tr>
                  <td colspan="5" class="empty-cell">
                    No hay matrices PAD. Cree una nueva con "+ Nueva Matriz PAD".
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
    `,
  styles: [`
    .mpx-page { padding-bottom: 2rem; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }
    .header-actions { display: flex; align-items: center; gap: 0.5rem; white-space: nowrap; }

    .table-card { padding: 0; overflow: hidden; }
    .table-scroll { overflow-x: auto; }
    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .matriz-table th { text-align: left; padding: 0.625rem 0.75rem; background: var(--bg); color: var(--text-secondary); font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.03em; border-bottom: 1px solid var(--border); }
    .matriz-table td { padding: 0.625rem 0.75rem; border-bottom: 1px solid var(--border); }
    .actions-col { white-space: nowrap; }
    .actions-col .btn { margin-right: 0.25rem; }
    .codigo { font-family: monospace; font-weight: 600; color: var(--primary-dark); }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 1.5rem; }

    .badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #8D6E2F; }
    .btn-danger-ghost { color: var(--mdc-red-800); background: transparent; border: 1px solid #EF9A9A; }
    .btn-danger-ghost:hover:not(:disabled) { background: var(--mdc-red-50); }
    .btn-danger-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .page-header { flex-direction: column; }
    }
  `],
})
export class MatricesPadHomeComponent implements OnInit {
  borradores: BorradorMatrizPAD[] = [];
  cargando = false;
  mensajeError = '';

  constructor(
    private service: MatricesPadService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.mensajeError = '';
    this.service.listar().subscribe({
      next: (r) => {
        this.borradores = r?.results || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando borradores', err);
        this.cargando = false;
        this.mensajeError = 'No se pudo cargar la lista de matrices PAD.';
        this.cdr.detectChanges();
      },
    });
  }

  eliminar(b: BorradorMatrizPAD): void {
    if (b.estado === 'COMPLETO') return;
    if (!confirm(`¿Eliminar el borrador de gestión ${b.gestion}?`)) return;
    this.service.eliminar(b.id).subscribe({
      next: () => {
        this.borradores = this.borradores.filter((x) => x.id !== b.id);
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error eliminando borrador', err);
        this.mensajeError = 'No se pudo eliminar el borrador.';
        this.cdr.detectChanges();
      },
    });
  }
}
