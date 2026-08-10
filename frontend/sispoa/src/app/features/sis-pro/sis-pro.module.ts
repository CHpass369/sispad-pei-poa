import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { modulosPendientes } from '../sistemas/modulos-pendientes';
import { PreinversionDetalleComponent } from './preinversion-detalle.component';
import { PreinversionEdtpComponent } from './preinversion-edtp.component';
import { PreinversionItcpComponent } from './preinversion-itcp.component';
import { PreinversionListComponent } from './preinversion-list.component';
import { PreinversionTdrComponent } from './preinversion-tdr.component';
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
  // Preinversión (SISPRE / RM 115) — ITCP · TDR · EDTP
  {
    path: 'preinversion',
    component: PreinversionListComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'preinversion/:id',
    component: PreinversionDetalleComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'preinversion/:id/itcp',
    component: PreinversionItcpComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'preinversion/:id/tdr',
    component: PreinversionTdrComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  {
    path: 'preinversion/:id/edtp',
    component: PreinversionEdtpComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pro.project.read'] },
  },
  // Módulos del plan maestro (§18.1 SIS-PRO) en desarrollo
  ...modulosPendientes(
    [
      { ruta: 'formulacion', nombre: 'Formulación técnica' },
      { ruta: 'contratacion', nombre: 'Contratación' },
      { ruta: 'ejecucion', nombre: 'Ejecución' },
      { ruta: 'supervision', nombre: 'Supervisión / Fiscalización' },
      { ruta: 'seguimiento', nombre: 'Seguimiento de proyectos' },
    ],
    'SIS-PRO',
    '/sis-pro/dashboard',
    ['sis_pro.project.read'],
  ),
];

@NgModule({
  declarations: [
    SisProDashboardComponent,
    SisProListComponent,
    SisProDetalleComponent,
    PreinversionListComponent,
    PreinversionDetalleComponent,
    PreinversionItcpComponent,
    PreinversionTdrComponent,
    PreinversionEdtpComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class SisProModule {}
