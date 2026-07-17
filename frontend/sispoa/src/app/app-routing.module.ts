import { Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule),
  },
  {
    path: 'dashboard',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule),
  },
  {
    path: 'gestion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/gestion/gestion.module').then(m => m.GestionModule),
  },
  {
    path: 'organizacion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/organizacion/organizacion.module').then(m => m.OrganizacionModule),
  },
  {
    path: 'catalogos',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/catalogos/catalogos.module').then(m => m.CatalogosModule),
  },
  {
    path: 'planificacion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/planificacion/planificacion.module').then(m => m.PlanificacionModule),
  },
  {
    path: 'indicadores',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/indicadores/indicadores.module').then(m => m.IndicadoresModule),
  },
  {
    path: 'presupuesto',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/presupuesto/presupuesto.module').then(m => m.PresupuestoModule),
  },
  {
    path: 'techos',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/techos/techos.module').then(m => m.TechosModule),
  },
  {
    path: 'inversion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/inversion/inversion.module').then(m => m.InversionModule),
  },
  {
    path: 'territorio',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/territorio/territorio.module').then(m => m.TerritorioModule),
  },
  {
    path: 'workflow',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/workflow/workflow.module').then(m => m.WorkflowModule),
  },
  {
    path: 'reportes',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/reportes/reportes.module').then(m => m.ReportesModule),
  },
  {
    path: 'articulador',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/pad/pad.module').then(m => m.PadModule),
  },
  {
    path: 'poau',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/poau/poau.module').then(m => m.PoauModule),
  },
  {
    path: 'auditoria',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/auditoria/auditoria.module').then(m => m.AuditoriaModule),
  },
  {
    path: 'admin-usuarios',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/admin-usuarios/admin-usuarios.module').then(m => m.AdminUsuariosModule),
  },
  {
    path: 'seguimiento',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/seguimiento/seguimiento.module').then(m => m.SeguimientoModule),
  },
  {
    path: 'evaluacion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/evaluacion/evaluacion.module').then(m => m.EvaluacionModule),
  },
  {
    path: 'modificaciones',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/modificaciones/modificaciones.module').then(m => m.ModificacionesModule),
  },
  {
    path: 'consolidacion',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/consolidacion/consolidacion.module').then(m => m.ConsolidacionModule),
  },
  {
    path: 'notificaciones',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/notificaciones/notificaciones.module').then(m => m.NotificacionesModule),
  },
  {
    path: 'documentos',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/documentos/documentos.module').then(m => m.DocumentosModule),
    data: { breadcrumb: 'Documentos' }
  },
  {
    path: 'normativa',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/normativa/normativa.module').then(m => m.NormativaModule),
    data: { breadcrumb: 'Normativa' }
  },
  {
    path: 'recursos',
    canActivate: [AuthGuard],
    loadChildren: () => import('./features/recursos/recursos.module').then(m => m.RecursosModule),
    data: { breadcrumb: 'Recursos' }
  },
  {
    path: 'portal',
    loadChildren: () => import('./features/portal-publico/portal-publico.module').then(m => m.PortalPublicoModule),
  },
  { path: '**', redirectTo: '/dashboard' },
];
