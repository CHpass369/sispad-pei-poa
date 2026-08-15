import { Routes } from '@angular/router';
import { ShellComponent } from './core/layout/shell.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { SystemOverviewComponent } from './pages/system-overview/system-overview.component';
import { ModulePageComponent } from './pages/module-page/module-page.component';

export const routes: Routes = [
  {
    path: '',
    component: ShellComponent,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', component: DashboardComponent, title: 'PIP SACABA' },
      { path: 'sis-pe', component: SystemOverviewComponent, data: { system: 'pe' }, title: 'SIS-PE' },
      { path: 'sis-poa', component: SystemOverviewComponent, data: { system: 'poa' }, title: 'SIS-POA' },
      { path: 'sis-pro', component: SystemOverviewComponent, data: { system: 'pro' }, title: 'SIS-PRO' },
      { path: 'sis-pe/articulacion', component: ModulePageComponent, data: { title: 'Articulación Estratégica', area: 'SIS-PE', kind: 'articulacion' } },
      { path: 'sis-pe/pad', component: ModulePageComponent, data: { title: 'Matriz PAD', area: 'SIS-PE', kind: 'pad' } },
      { path: 'sis-pe/pei', component: ModulePageComponent, data: { title: 'Matriz PEI', area: 'SIS-PE', kind: 'pei' } },
      { path: 'sis-poa/gestion-fiscal', component: ModulePageComponent, data: { title: 'Gestión Fiscal', area: 'SIS-POA', kind: 'fiscal' } },
      { path: 'sis-poa/techos', component: ModulePageComponent, data: { title: 'Techos Presupuestarios', area: 'SIS-POA', kind: 'techos' } },
      { path: 'sis-poa/distribucion', component: ModulePageComponent, data: { title: 'Distribución Presupuestaria', area: 'SIS-POA', kind: 'distribucion' } },
      { path: 'sis-poa/poa', component: ModulePageComponent, data: { title: 'Formulación POA', area: 'SIS-POA', kind: 'poa' } },
      { path: 'sis-poa/poau', component: ModulePageComponent, data: { title: 'Programación POAU', area: 'SIS-POA', kind: 'poau' } },
      { path: 'sis-poa/seguimiento', component: ModulePageComponent, data: { title: 'Seguimiento POA', area: 'SIS-POA', kind: 'seguimiento' } },
      { path: 'sis-pro/cartera', component: ModulePageComponent, data: { title: 'Cartera de Proyectos', area: 'SIS-PRO', kind: 'cartera' } },
      { path: 'sis-pro/condiciones-previas', component: ModulePageComponent, data: { title: 'Condiciones Previas', area: 'SIS-PRO', kind: 'condiciones' } },
      { path: 'sis-pro/preinversion', component: ModulePageComponent, data: { title: 'Preinversión', area: 'SIS-PRO', kind: 'preinversion' } },
      { path: 'sis-pro/contratacion', component: ModulePageComponent, data: { title: 'Contratación', area: 'SIS-PRO', kind: 'contratacion' } },
      { path: 'sis-pro/ejecucion', component: ModulePageComponent, data: { title: 'Ejecución y Seguimiento', area: 'SIS-PRO', kind: 'ejecucion' } },
      { path: 'catalogos', component: ModulePageComponent, data: { title: 'Catálogos Maestros', area: 'PIP', kind: 'catalogos' } },
      { path: 'administracion', component: ModulePageComponent, data: { title: 'Administración y Seguridad', area: 'PIP', kind: 'admin' } }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
