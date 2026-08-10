import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { SisProDashboardComponent } from './sis-pro-dashboard.component';
import { SisProDetalleComponent } from './sis-pro-detalle.component';
import { SisProListComponent } from './sis-pro-list.component';

const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    component: SisProDashboardComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'proyectos',
    component: SisProListComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'proyectos/:id',
    component: SisProDetalleComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
];

@NgModule({
  declarations: [
    SisProDashboardComponent,
    SisProListComponent,
    SisProDetalleComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class SisProModule {}
