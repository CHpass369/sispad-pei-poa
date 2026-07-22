import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { LayoutComponent } from '../layout/layout.component';
import { LayoutModule } from '../layout/layout.module';
import { AuthGuard } from '../core/guards/auth.guard';

const routes: Routes = [
  {
    path: '',
    component: LayoutComponent,
    canActivate: [AuthGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', loadChildren: () => import('../features/dashboard/dashboard.module').then(m => m.DashboardModule) },
      { path: 'gestion', loadChildren: () => import('../features/gestion/gestion.module').then(m => m.GestionModule) },
      { path: 'organizacion', loadChildren: () => import('../features/organizacion/organizacion.module').then(m => m.OrganizacionModule) },
      { path: 'catalogos', loadChildren: () => import('../features/catalogos/catalogos.module').then(m => m.CatalogosModule) },
      { path: 'planificacion', loadChildren: () => import('../features/planificacion/planificacion.module').then(m => m.PlanificacionModule) },
      { path: 'indicadores', loadChildren: () => import('../features/indicadores/indicadores.module').then(m => m.IndicadoresModule) },
      { path: 'presupuesto', loadChildren: () => import('../features/presupuesto/presupuesto.module').then(m => m.PresupuestoModule) },
      { path: 'techos', loadChildren: () => import('../features/techos/techos.module').then(m => m.TechosModule) },
      { path: 'inversion', loadChildren: () => import('../features/inversion/inversion.module').then(m => m.InversionModule) },
      { path: 'territorio', loadChildren: () => import('../features/territorio/territorio.module').then(m => m.TerritorioModule) },
      { path: 'workflow', loadChildren: () => import('../features/workflow/workflow.module').then(m => m.WorkflowModule) },
      { path: 'reportes', loadChildren: () => import('../features/reportes/reportes.module').then(m => m.ReportesModule) },
      { path: 'articulacion', loadChildren: () => import('../features/articulacion/articulacion.module').then(m => m.ArticulacionModule) },
      { path: 'articulador', loadChildren: () => import('../features/pad/pad.module').then(m => m.PadModule) },
      { path: 'poau', loadChildren: () => import('../features/poau/poau.module').then(m => m.PoauModule) },
      { path: 'auditoria', loadChildren: () => import('../features/auditoria/auditoria.module').then(m => m.AuditoriaModule) },
      { path: 'admin-usuarios', loadChildren: () => import('../features/admin-usuarios/admin-usuarios.module').then(m => m.AdminUsuariosModule) },
      { path: 'seguimiento', loadChildren: () => import('../features/seguimiento/seguimiento.module').then(m => m.SeguimientoModule) },
      { path: 'evaluacion', loadChildren: () => import('../features/evaluacion/evaluacion.module').then(m => m.EvaluacionModule) },
      { path: 'modificaciones', loadChildren: () => import('../features/modificaciones/modificaciones.module').then(m => m.ModificacionesModule) },
      { path: 'consolidacion', loadChildren: () => import('../features/consolidacion/consolidacion.module').then(m => m.ConsolidacionModule) },
      { path: 'notificaciones', loadChildren: () => import('../features/notificaciones/notificaciones.module').then(m => m.NotificacionesModule) },
      { path: 'documentos', loadChildren: () => import('../features/documentos/documentos.module').then(m => m.DocumentosModule) },
      { path: 'normativa', loadChildren: () => import('../features/normativa/normativa.module').then(m => m.NormativaModule) },
      { path: 'recursos', loadChildren: () => import('../features/recursos/recursos.module').then(m => m.RecursosModule) },
    ],
  },
];

@NgModule({
  imports: [CommonModule, LayoutModule, RouterModule.forChild(routes)],
})
export class MainModule {}