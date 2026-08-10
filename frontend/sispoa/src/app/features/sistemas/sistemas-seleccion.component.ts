import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';

interface Sistema {
  codigo: string;
  nombre: string;
  sigla: string;
  descripcion: string;
  icono: string;
  ruta: string;
  capacidades: string[];
  color: string;
}

@Component({
  standalone: false,
  selector: 'app-sistemas-seleccion',
  template: `
    <div class="seleccion">
      <div class="header">
        <h1>Plataforma Integral de Planificación</h1>
        <p class="subtitle">PIP-GAMS — Gobierno Autónomo Municipal de Sacaba</p>
      </div>
      <div class="grid">
        <a *ngFor="let sis of sistemas" [routerLink]="sis.ruta" class="card {{ sis.color }}">
          <div class="icono">{{ sis.icono }}</div>
          <h2>{{ sis.sigla }}</h2>
          <h3>{{ sis.nombre }}</h3>
          <p>{{ sis.descripcion }}</p>
          <div class="modulos">
            <span class="chip" *ngFor="let m of sis.modulos">{{ m }}</span>
          </div>
          <div class="entrar">Ingresar →</div>
        </a>
      </div>
      <div class="nota" *ngIf="sinAcceso">
        <p>No tienes acceso a ningún sistema. Contacta al administrador.</p>
      </div>
    </div>
  `,
  styles: [`
    .seleccion { padding: 2rem; max-width: 1100px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 2.5rem; }
    .header h1 { font-size: 1.75rem; margin-bottom: 0.25rem; color: var(--primary); }
    .subtitle { color: var(--text-secondary); font-size: 0.9rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
    .card {
      display: block; text-decoration: none; color: var(--text-primary);
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 1.75rem; transition: transform 0.15s, box-shadow 0.15s;
    }
    .card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .icono { font-size: 2.5rem; }
    .card h2 { font-size: 1.5rem; margin: 0.75rem 0 0.125rem; }
    .card h3 { font-size: 1rem; margin: 0 0 0.5rem; }
    .card p { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5; }
    .modulos { display: flex; flex-wrap: wrap; gap: 0.375rem; margin: 0.875rem 0; }
    .chip {
      font-size: 0.6875rem; padding: 0.125rem 0.5rem; border-radius: 999px;
      background: #F5F5F5; color: var(--text-secondary);
    }
    .entrar { font-weight: 700; font-size: 0.875rem; }
    .sis-pe .entrar { color: #1565C0; }
    .sis-poa .entrar { color: #2E7D32; }
    .sis-pro .entrar { color: #E65100; }
    .nota { text-align: center; margin-top: 1.5rem; color: var(--warn); font-size: 0.875rem; }
  `],
})
export class SistemasSeleccionComponent implements OnInit {
  sistemas: (Sistema & { modulos: string[] })[] = [];
  sinAcceso = false;

  constructor(private permissions: PermissionsService) {}

  ngOnInit(): void {
    const config = [
      {
        codigo: 'sis-pe',
        sigla: 'SIS-PE',
        nombre: 'Planificación Estratégica',
        descripcion: 'Instrumentos y metodologías, marco nacional, PAD, PEI, articulación estratégica, indicadores, territorialización y evaluación.',
        icono: '🏛️',
        ruta: '/sis-pe/dashboard',
        capacidades: ['sis_pe.instrumento.read'],
        color: 'sis-pe',
        modulos: ['Instrumentos', 'PAD', 'PEI', 'Articulación', 'Indicadores', 'Territorio'],
      },
      {
        codigo: 'sis-poa',
        sigla: 'SIS-POA',
        nombre: 'Planificación Operativa Anual',
        descripcion: 'POA institucional y POAU, acciones de corto plazo, operaciones, actividades, tareas, techos, presupuesto y seguimiento.',
        icono: '📊',
        ruta: '/sis-poa/dashboard',
        capacidades: ['sis_poa.formulate'],
        color: 'sis-poa',
        modulos: ['POA', 'POAU', 'Recursos', 'Techos', 'Presupuesto', 'Seguimiento'],
      },
      {
        codigo: 'sis-pro',
        sigla: 'SIS-PRO',
        nombre: 'Ciclo del Proyecto',
        descripcion: 'Cartera, condiciones previas, preinversión, formulación, costos, contratación, ejecución, supervisión y cierre.',
        icono: '🚧',
        ruta: '/sis-pro/dashboard',
        capacidades: ['sis_pro.project.read'],
        color: 'sis-pro',
        modulos: ['Cartera', 'Preinversión', 'Formulación', 'Contratación', 'Ejecución'],
      },
    ];
    this.sistemas = config.filter(sis =>
      this.permissions.hasAnyCapability(sis.capacidades),
    );
    this.sinAcceso = this.sistemas.length === 0;
  }
}
