import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { Subscription, filter } from 'rxjs';

export interface Breadcrumb {
  label: string;
  url: string;
}

@Component({
  standalone: false,
  selector: 'app-breadcrumbs',
  template: `
    <nav class="breadcrumbs" *ngIf="breadcrumbs.length > 0">
      <ol class="breadcrumbs-list">
        <li *ngFor="let crumb of breadcrumbs; let last = last"
            class="breadcrumbs-item"
            [class.breadcrumbs-active]="last">
          <a *ngIf="!last" [routerLink]="crumb.url" class="breadcrumbs-link">{{ crumb.label }}</a>
          <span *ngIf="last" class="breadcrumbs-current">{{ crumb.label }}</span>
          <span *ngIf="!last" class="breadcrumbs-separator">/</span>
        </li>
      </ol>
    </nav>
  `,
  styles: [`
    .breadcrumbs {
      padding: 0.5rem 0;
      margin-bottom: 0.5rem;
    }
    .breadcrumbs-list {
      display: flex;
      align-items: center;
      list-style: none;
      margin: 0;
      padding: 0;
      flex-wrap: wrap;
    }
    .breadcrumbs-item {
      display: inline-flex;
      align-items: center;
      font-size: 0.8125rem;
    }
    .breadcrumbs-link {
      color: var(--primary, #1a237e);
      text-decoration: none;
      transition: color 0.15s;
    }
    .breadcrumbs-link:hover {
      text-decoration: underline;
      color: var(--primary-dark, #0d1642);
    }
    .breadcrumbs-current {
      color: var(--text-secondary, #666);
      font-weight: 500;
    }
    .breadcrumbs-separator {
      margin: 0 0.5rem;
      color: var(--text-secondary, #999);
    }
  `]
})
export class BreadcrumbsComponent implements OnInit, OnDestroy {
  breadcrumbs: Breadcrumb[] = [];
  private subscription!: Subscription;

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.subscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.buildBreadcrumbs(this.activatedRoute.root);
      });
    this.buildBreadcrumbs(this.activatedRoute.root);
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  private buildBreadcrumbs(route: ActivatedRoute, url: string = '', breadcrumbs: Breadcrumb[] = []): void {
    const children: ActivatedRoute[] = route.children;

    if (children.length === 0) {
      this.breadcrumbs = breadcrumbs;
      return;
    }

    for (const child of children) {
      const routeURL = child.snapshot.url.map(segment => segment.path).join('/');
      if (routeURL) {
        url += `/${routeURL}`;
      }

      let label = child.snapshot.data['breadcrumb'];
      if (!label) {
        label = this.getDefaultLabel(routeURL);
      }

      if (label) {
        breadcrumbs.push({ label, url });
      }

      this.buildBreadcrumbs(child, url, breadcrumbs);
    }
  }

  private getDefaultLabel(segment: string): string {
    const labels: Record<string, string> = {
      'dashboard': 'Dashboard',
      'gestion': 'Gestión Fiscal',
      'organizacion': 'Organización',
      'catalogos': 'Catálogos',
      'planificacion': 'Planificación',
      'indicadores': 'Indicadores',
      'presupuesto': 'Presupuesto',
      'techos': 'Techos',
      'inversion': 'Inversión',
      'territorio': 'Territorio',
      'workflow': 'Workflow',
      'reportes': 'Reportes',
      'articulador': 'Articulador PAD',
      'poau': 'POAU',
      'auditoria': 'Auditoría',
      'admin-usuarios': 'Administración de Usuarios',
      'seguimiento': 'Seguimiento',
      'evaluacion': 'Evaluación',
      'modificaciones': 'Modificaciones',
      'consolidacion': 'Consolidación',
      'notificaciones': 'Notificaciones',
      'portal': 'Portal Público',
      'nuevo': 'Nuevo',
      'nueva': 'Nueva',
      'editar': 'Editar',
      'registrar': 'Registrar',
      'alertas': 'Alertas',
      'observaciones': 'Observaciones',
      'aprobaciones': 'Aprobaciones',
      'mapa': 'Mapa de Inversiones',
      'planes': 'Planes',
      'estadisticas': 'Estadísticas',
    };
    return labels[segment] || segment;
  }
}
