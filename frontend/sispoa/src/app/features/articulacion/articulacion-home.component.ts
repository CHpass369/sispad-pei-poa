import { Component } from '@angular/core';

interface CardLink {
  route: string;
  title: string;
  description: string;
  icon: string;
  color: string;
}

@Component({
  selector: 'app-articulacion-home',
  standalone: false,
  template: `
    <div class="art-home">
      <div class="page-header">
        <h2>Articulación PAD-PEI-POA-POAU</h2>
        <p class="text-secondary">
          Matrices de articulación del Sistema Integrado de Planificación Estratégica
        </p>
      </div>

      <div class="cards-grid">
        <a *ngFor="let card of cards"
           [routerLink]="card.route"
           class="card art-card"
           [style.--card-accent]="card.color">
          <div class="card-icon-wrapper" [style.background]="card.color + '18'">
            <span class="card-icon">{{ card.icon }}</span>
          </div>
          <div class="card-body">
            <h3>{{ card.title }}</h3>
            <p>{{ card.description }}</p>
          </div>
          <span class="card-arrow">→</span>
        </a>
      </div>

      <div class="info-card card">
        <div class="info-header">
          <span class="info-icon">ⓘ</span>
          <strong>¿Qué es la Articulación?</strong>
        </div>
        <p>
          Las matrices de articulación vinculan los instrumentos de planificación
          PAD (Plan de Acción Departamental), PEI (Plan Estratégico Institucional),
          POA (Plan Operativo Anual) y POAU (Plan Operativo Anual por Unidad)
          con el presupuesto y los objetos de gasto, asegurando coherencia
          estratégica en toda la cadena de planificación municipal.
        </p>
      </div>
    </div>
  `,
  styles: [`
    .art-home { padding-bottom: 2rem; }
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.35rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .art-card {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      padding: 1.25rem;
      text-decoration: none;
      color: var(--text);
      border-left: 4px solid var(--card-accent, var(--primary));
      transition: all 0.2s;
      position: relative;
    }
    .art-card:hover {
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      transform: translateY(-2px);
    }
    .art-card:hover .card-arrow {
      transform: translateX(4px);
      opacity: 1;
    }

    .card-icon-wrapper {
      width: 48px;
      height: 48px;
      min-width: 48px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
    }

    .card-body { flex: 1; }
    .card-body h3 {
      font-size: 0.9375rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
      color: var(--primary-dark);
    }
    .card-body p {
      font-size: 0.75rem;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    .card-arrow {
      font-size: 1.125rem;
      color: var(--primary);
      opacity: 0.4;
      transition: all 0.2s;
      align-self: center;
    }

    .info-card { padding: 1.25rem; }
    .info-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
    }
    .info-icon { font-size: 1.125rem; color: var(--primary); }
    .info-header strong { font-size: 0.875rem; color: var(--primary-dark); }
    .info-card p {
      font-size: 0.8125rem;
      color: var(--text-secondary);
      line-height: 1.6;
    }
  `],
})
export class ArticulacionHomeComponent {
  cards: CardLink[] = [
    {
      route: '/articulacion/pad-pei',
      title: 'Articulación PAD → PEI',
      description: 'Matriz de articulación entre resultados y productos del Plan de Acción Departamental y el Plan Estratégico Institucional',
      icon: '🔗',
      color: '#1B5E3B',
    },
    {
      route: '/articulacion/pei-poa',
      title: 'Articulación PEI → POA',
      description: 'Vinculación de acciones del POA con productos del PEI, indicadores, metas y presupuesto',
      icon: '📋',
      color: '#2E7D32',
    },
    {
      route: '/articulacion/poa-poau',
      title: 'Articulación POA → POAU',
      description: 'Despliegue jerárquico: Operaciones, Actividades y Tareas con programación mensual',
      icon: '📂',
      color: '#388E3C',
    },
    {
      route: '/articulacion/presupuesto-seguimiento',
      title: 'Presupuesto y Seguimiento',
      description: 'Matriz de seguimiento presupuestario con ejecución financiera, física e indicadores de eficacia',
      icon: '📊',
      color: '#43A047',
    },
    {
      route: '/articulacion/objetos-gasto',
      title: 'Objetos de Gasto',
      description: 'Asignaciones de objetos de gasto por actividad: código, grupo, fuente, organismo y monto',
      icon: '💰',
      color: '#4CAF50',
    },
  ];
}
