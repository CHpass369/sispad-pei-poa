import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { modulosPendientes } from '../sistemas/modulos-pendientes';
import { SisPoaDashboardComponent } from './sis-poa-dashboard.component';
import { SisPoaDetalleComponent } from './sis-poa-detalle.component';
import { SisPoaListComponent } from './sis-poa-list.component';

const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    component: SisPoaDashboardComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'poas',
    component: SisPoaListComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'poas/:id',
    component: SisPoaDetalleComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  // Módulos del plan maestro (§18.1 SIS-POA) en desarrollo
  ...modulosPendientes(
    [
      { ruta: 'poau', nombre: 'POAU por unidad' },
      { ruta: 'recursos', nombre: 'Recursos' },
      { ruta: 'techos', nombre: 'Techos' },
      { ruta: 'presupuesto', nombre: 'Presupuesto' },
      { ruta: 'seguimiento', nombre: 'Seguimiento operativo' },
      { ruta: 'modificaciones', nombre: 'Modificaciones' },
    ],
    'SIS-POA',
    '/sis-poa/dashboard',
    ['sis_poa.formulate'],
  ),
];

@NgModule({
  declarations: [
    SisPoaDashboardComponent,
    SisPoaListComponent,
    SisPoaDetalleComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class SisPoaModule {}
