import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { modulosPendientes } from '../sistemas/modulos-pendientes';
import { SisPoaDashboardComponent } from './sis-poa-dashboard.component';
import { PoaWizardComponent } from './poa/poa-wizard.component';
import { PoaMatrizViewerComponent } from './poa/poa-matriz-viewer.component';
import { SisPoaPresupuestoComponent } from './sis-poa-presupuesto.component';
import { SisPoaTechosComponent } from './sis-poa-techos.component';

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
    component: PoaWizardComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'presupuesto',
    component: SisPoaPresupuestoComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'techos',
    component: SisPoaTechosComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'budget',
    loadChildren: () => import('./budget/budget.module').then(m => m.BudgetModule),
  },
  // Módulos del plan maestro (§18.1 SIS-POA) en desarrollo
  ...modulosPendientes(
    [
      { ruta: 'presupuesto-recursos', nombre: 'Presupuesto General de Recursos' },
      { ruta: 'presupuesto-gastos', nombre: 'Presupuesto General de Gastos' },
      { ruta: 'poaus', nombre: 'POAUs' },
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
    PoaWizardComponent,
    PoaMatrizViewerComponent,
    SisPoaPresupuestoComponent,
    SisPoaTechosComponent,
  ],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class SisPoaModule {}
