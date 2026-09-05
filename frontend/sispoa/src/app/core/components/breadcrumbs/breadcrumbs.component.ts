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
    @if (breadcrumbs.length > 0) {
      <nav class="breadcrumbs">
        <ol class="breadcrumbs-list">
          @for (crumb of breadcrumbs; track crumb; let last = $last) {
            <li
              class="breadcrumbs-item"
              [class.breadcrumbs-active]="last">
              @if (!last) {
                <a [routerLink]="crumb.url" class="breadcrumbs-link">{{ crumb.label }}</a>
              }
              @if (last) {
                <span class="breadcrumbs-current">{{ crumb.label }}</span>
              }
              @if (!last) {
                <span class="breadcrumbs-separator">/</span>
              }
            </li>
          }
        </ol>
      </nav>
    }
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
      'matrices-pad': 'PAD',
      'poau': 'POAU',
      'auditoria': 'Auditoría',
      'admin-usuarios': 'Usuarios y permisos',
      'seguimiento': 'Seguimiento',
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
      // Sistemas y sus instrumentos.
      'sistemas': 'Selección de sistemas',
      'sis-pe': 'SIS-PE',
      'sis-poa': 'SIS-POA',
      'sis-pro': 'SIS-PRO',
      'pei': 'PEI',
      'pad': 'PAD',
      'poas': 'POA',
      'poaus': 'POAUs',
      'poau_recursos': 'POAU (Recursos)',
      'poau_saldos': 'Presupuesto por Unidad y Categoría',
      'poau-recursos': 'POAU (Recursos)',
      'budget': 'Presupuesto',
      'presupuesto-recursos': 'Presupuesto de Recursos',
      'presupuesto-gastos': 'Presupuesto de Gastos',
      'articulacion': 'Articulación',
      'registros': 'Registros',
      'formulacion': 'Formulación',
      'preinversion': 'Preinversión',
      'gestion-fiscal': 'Habilitación de Gestión',
    };
    if (labels[segment]) {
      return labels[segment];
    }
    // Sin entrada en el mapa, al menos no mostrar el nombre crudo de la ruta:
    // 'poau_recursos' se leia tal cual, con guion bajo incluido.
    return segment
      .replace(/[-_]+/g, ' ')
      .replace(/^./, c => c.toUpperCase());
  }
}
