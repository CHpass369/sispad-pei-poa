import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { POAU_CAPABILITIES } from '../../core/config/poau-capabilities';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { GestionHabilitadaGuard } from '../../core/guards/gestion-habilitada.guard';
import { modulosPendientes } from '../sistemas/modulos-pendientes';
import { SisPoaDashboardComponent } from './sis-poa-dashboard.component';
import { PoaWizardComponent } from './poa/poa-wizard.component';
import { PoaMatrizViewerComponent } from './poa/poa-matriz-viewer.component';
import { PoaHomeComponent } from './poa/poa-home.component';
import { PoaRegistrosComponent } from './poa/poa-registros.component';
import { SisPoaPresupuestoComponent } from './sis-poa-presupuesto.component';
import { SisPoaTechosComponent } from './sis-poa-techos.component';
import { PresupuestoRecursosComponent } from './presupuesto-recursos.component';
import { PresupuestoGastosComponent } from './presupuesto-gastos.component';
import { MatrizPoauComponent } from './matriz-poau.component';

const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    component: SisPoaDashboardComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'poas',
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
    children: [
      { path: '', component: PoaHomeComponent },
      { path: 'nuevo', component: PoaWizardComponent },
      { path: 'nuevo/:id', component: PoaWizardComponent },
      { path: 'registros', component: PoaRegistrosComponent },
    ],
  },
  {
    // Antes que 'poaus', para que la ruta específica gane.
    path: 'poaus/editar/:accion',
    loadChildren: () => import('../poau/poau.module').then(m => m.PoauModule),
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: POAU_CAPABILITIES },
  },
  {
    path: 'poaus',
    component: MatrizPoauComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: POAU_CAPABILITIES },
  },
  {
    path: 'presupuesto-gastos',
    component: PresupuestoGastosComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'presupuesto-recursos',
    component: PresupuestoRecursosComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'presupuesto',
    component: SisPoaPresupuestoComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'techos',
    component: SisPoaTechosComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'budget',
    loadChildren: () => import('./budget/budget.module').then(m => m.BudgetModule),
  },
  // Módulos del plan maestro (§18.1 SIS-POA) en desarrollo
  ...modulosPendientes(
    [
      { ruta: 'poau', nombre: 'POAU por unidad' },
      { ruta: 'recursos', nombre: 'Recursos' },
      { ruta: 'seguimiento', nombre: 'Seguimiento y Evaluación' },
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
    PoaHomeComponent,
    PoaWizardComponent,
    PoaRegistrosComponent,
    PoaMatrizViewerComponent,
    SisPoaPresupuestoComponent,
    SisPoaTechosComponent,
    PresupuestoRecursosComponent,
    PresupuestoGastosComponent,
    MatrizPoauComponent,
  ],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class SisPoaModule {}
