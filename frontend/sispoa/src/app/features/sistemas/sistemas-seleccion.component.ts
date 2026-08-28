import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { SIS_PE_CAPABILITIES } from '../../core/config/modules.config';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';

interface Sistema {
  codigo: string;
  nombre: string;
  sigla: string;
  descripcion: string;
  icono: string;
  ruta: string;
  capacidades: string[];
  color: string;
  progress: number;
  meta: string;
  caption: string;
  modulos: string[];
}

@Component({
  standalone: false,
  selector: 'app-sistemas-seleccion',
  template: `
    <div class="seleccion-page">
      <header class="seleccion-head">
        <div class="eyebrow">Gobierno Autónomo Municipal de Sacaba</div>
        <h1>Plataforma Integral de Planificación</h1>
        <p>Centro de mando para planificación estratégica, operativa y gestión del ciclo de proyectos.</p>
      </header>

      <main class="systems-grid">
        @for (sis of sistemas; track sis.codigo) {
          <a [routerLink]="sis.ruta" class="system-card {{ sis.color }}"
            [attr.aria-label]="'Ingresar a ' + sis.sigla">
            <div class="system-top">
              <span class="code">{{ sis.sigla }}</span>
              <lucide-angular [name]="sis.icono" [size]="18"></lucide-angular>
            </div>
            <h2>{{ sis.nombre }}</h2>
            <p>{{ sis.descripcion }}</p>
            <div class="meta mono">{{ sis.meta }}</div>
            <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100"
              [attr.aria-valuenow]="sis.progress" [attr.aria-label]="'Progreso ' + sis.sigla">
              <i [style.width.%]="sis.progress"></i>
            </div>
            <div class="progress-caption">
              <span>{{ sis.caption }}</span>
              <strong>{{ sis.progress }}%</strong>
            </div>
          </a>
        }
      </main>

      @if (capacidadesCargadas && sinAcceso) {
        <div class="nota">
          <p>No tienes acceso a ningún sistema. Contacta al administrador.</p>
          <button type="button" class="btn btn-outline logout-button" (click)="cerrarSesion()">
            <lucide-angular name="log-out" [size]="16"></lucide-angular>
            Cerrar sesión y volver al inicio
          </button>
        </div>
      }

      <footer class="foot">
        <span>Plataforma Integral de Planificación · GAM Sacaba</span>
        <span class="mono">Gestión {{ gestionAnio ?? 'sin habilitar' }} · pip_core</span>
      </footer>
    </div>
    `,
  styles: [`
    .seleccion-page {
      min-height: 100vh;
      display: flex; flex-direction: column;
      padding: 48px 26px 28px;
      max-width: 1100px; margin: 0 auto; width: 100%;
    }
    .seleccion-head { text-align: center; margin-bottom: 36px; }
    .eyebrow {
      font-size: 10.5px; letter-spacing: 1.8px; text-transform: uppercase;
      color: var(--pip-green-700); font-weight: 700; margin-bottom: 6px;
    }
    .seleccion-head h1 {
      font-family: var(--font-display);
      font-size: clamp(24px, 3vw, 32px); font-weight: 700; letter-spacing: -.5px;
    }
    .seleccion-head p { color: var(--pip-ink-soft); font-size: 13.5px; margin-top: 6px; }

    .systems-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 18px; margin-bottom: 24px;
    }
    .system-card {
      display: block; text-decoration: none; color: inherit;
      background: var(--pip-card);
      border: 1px solid var(--pip-line);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
      transition: transform .15s, box-shadow .15s;
      position: relative;
      overflow: hidden;
    }
    .system-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 28px rgba(19,32,25,.1);
      color: inherit;
    }
    .system-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    }
    .system-card.pe::before { background: #4A9FD8; }
    .system-card.poa::before { background: var(--pip-green-500); }
    .system-top {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 10px;
    }
    .system-top .code {
      font-family: var(--font-display); font-weight: 700; font-size: 15px; letter-spacing: .5px;
    }
    .system-card h2 {
      font-family: var(--font-display); font-size: 16.5px; font-weight: 600; margin-bottom: 4px;
    }
    .system-card p { font-size: 12.5px; color: var(--pip-ink-soft); margin-bottom: 12px; }
    .system-card .meta {
      font-family: var(--font-mono); font-size: 10.5px; color: var(--pip-green-700); margin-bottom: 12px;
    }
    .progress { height: 6px; background: #EDF1EE; border-radius: 20px; overflow: hidden; }
    .progress i { display: block; height: 100%; border-radius: 20px; background: var(--pip-green-700); }
    .system-card.pe .progress i { background: #4A9FD8; }
    .system-card.poa .progress i { background: var(--pip-green-500); }
    .progress-caption {
      display: flex; justify-content: space-between;
      font-size: 11px; color: var(--pip-ink-soft); margin-top: 5px;
    }
    .progress-caption strong { color: var(--pip-ink); font-family: var(--font-display); }

    .nota { text-align: center; margin: 1.5rem 0; color: var(--pip-warn); font-size: 0.875rem; }
    .nota p { margin-bottom: 0.75rem; }
    .logout-button { margin: 0 auto; }

    .foot {
      margin-top: auto; padding-top: 16px;
      border-top: 1px solid var(--pip-line);
      display: flex; justify-content: space-between; align-items: center;
      font-size: 11.5px; color: var(--pip-ink-soft); flex-wrap: wrap; gap: 8px;
    }

    @media (max-width: 640px) {
      .seleccion-page { padding: 32px 16px 24px; }
      .foot { justify-content: center; text-align: center; }
    }
  `],
})
export class SistemasSeleccionComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  sistemas: (Sistema & { modulos: string[] })[] = [];
  capacidadesCargadas = false;
  sinAcceso = false;

  constructor(
    private capabilities: CapabilitiesService,
    private auth: AuthService,
    private router: Router,
    private gestionActiva: GestionHabilitadaService,
  ) {}

  /** El pie mostraba «Gestión 2027 · RM N° 271/2026» fijo: al cambiar de
   *  gestión anunciaba la anterior, y la RM tampoco la seguía. */
  get gestionAnio(): number | null { return this.gestionActiva.anio(); }

  ngOnInit(): void {
    this.capabilities.cargadas$.pipe(
      filter(cargadas => cargadas),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(() => {
      this.capacidadesCargadas = true;
      this.recalcularSistemas();
    });
  }

  cerrarSesion(): void {
    this.auth.logout();
    void this.router.navigateByUrl('/auth/login', { replaceUrl: true });
  }

  private recalcularSistemas(): void {
    const config = [
      {
        codigo: 'sis-pe',
        sigla: 'SIS-PE',
        nombre: 'Planificación Estratégica',
        descripcion: 'Instrumentos y metodologías, marco nacional, PAD, PEI, articulación estratégica, indicadores, territorialización y evaluación.',
        icono: 'target',
        ruta: '/sis-pe/dashboard',
        capacidades: SIS_PE_CAPABILITIES,
        color: 'pe',
        progress: 68,
        meta: 'PGDESA → PDESA → PAD → PEI',
        caption: 'Instrumentos aprobados',
        modulos: ['Instrumentos', 'PAD', 'PEI', 'Articulación', 'Indicadores', 'Territorio'],
      },
      {
        codigo: 'sis-poa',
        sigla: 'SIS-POA',
        nombre: 'Planificación Operativa Anual',
        descripcion: 'POA institucional y POAU, acciones de corto plazo, operaciones, actividades, tareas, techos, presupuesto y seguimiento.',
        icono: 'layout-dashboard',
        ruta: '/sis-poa/dashboard',
        capacidades: ['sis_poa.formulate'],
        color: 'poa',
        progress: 54,
        meta: 'PEI → POA → POAU → Presupuesto',
        caption: 'Techo cargado · en revisión',
        modulos: ['POA', 'POAU', 'Recursos', 'Techos', 'Presupuesto', 'Seguimiento'],
      },
    ];
    this.sistemas = config.filter(sis =>
      this.capabilities.tieneAlguna(sis.capacidades),
    );
    this.sinAcceso = this.sistemas.length === 0;
  }
}
