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
      { path: '', redirectTo: 'sistemas', pathMatch: 'full' },
      { path: 'sistemas', loadChildren: () => import('../features/sistemas/sistemas.module').then(m => m.SistemasModule) },
      { path: 'dashboard', loadChildren: () => import('../features/dashboard/dashboard.module').then(m => m.DashboardModule) },
      { path: 'sis-pe', loadChildren: () => import('../features/sis-pe/sis-pe.module').then(m => m.SisPeModule) },
      { path: 'sis-poa', loadChildren: () => import('../features/sis-poa/sis-poa.module').then(m => m.SisPoaModule) },
      { path: 'sis-pro', loadChildren: () => import('../features/sis-pro/sis-pro.module').then(m => m.SisProModule) },
      { path: 'gestion', loadChildren: () => import('../features/gestion/gestion.module').then(m => m.GestionModule) },
      { path: 'organizacion', loadChildren: () => import('../features/organizacion/organizacion.module').then(m => m.OrganizacionModule) },
      { path: 'catalogos', loadChildren: () => import('../features/catalogos/catalogos.module').then(m => m.CatalogosModule) },
      { path: 'planificacion', loadChildren: () => import('../features/planificacion/planificacion.module').then(m => m.PlanificacionModule) },
      { path: 'presupuesto', loadChildren: () => import('../features/presupuesto/presupuesto.module').then(m => m.PresupuestoModule) },
      { path: 'techos', loadChildren: () => import('../features/techos/techos.module').then(m => m.TechosModule) },
      { path: 'inversion', loadChildren: () => import('../features/inversion/inversion.module').then(m => m.InversionModule) },
      { path: 'workflow', loadChildren: () => import('../features/workflow/workflow.module').then(m => m.WorkflowModule) },
      { path: 'reportes', loadChildren: () => import('../features/reportes/reportes.module').then(m => m.ReportesModule) },
      { path: 'articulacion', loadChildren: () => import('../features/articulacion/articulacion.module').then(m => m.ArticulacionModule) },
      { path: 'matrices-pad', loadChildren: () => import('../features/matrices-pad/matrices-pad.module').then(m => m.MatricesPadModule) },
      { path: 'articulador', loadChildren: () => import('../features/pad/pad.module').then(m => m.PadModule) },
      { path: 'auditoria', loadChildren: () => import('../features/auditoria/auditoria.module').then(m => m.AuditoriaModule) },
      { path: 'admin-usuarios', loadChildren: () => import('../features/admin-usuarios/admin-usuarios.module').then(m => m.AdminUsuariosModule) },
      { path: 'notificaciones', loadChildren: () => import('../features/notificaciones/notificaciones.module').then(m => m.NotificacionesModule) },
      { path: 'documentos', loadChildren: () => import('../features/documentos/documentos.module').then(m => m.DocumentosModule) },
      { path: 'normativa', loadChildren: () => import('../features/normativa/normativa.module').then(m => m.NormativaModule) },
    ],
  },
];

@NgModule({
  imports: [CommonModule, LayoutModule, RouterModule.forChild(routes)],
})
export class MainModule {}