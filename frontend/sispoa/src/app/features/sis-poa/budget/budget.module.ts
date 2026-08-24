import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../../core/guards/capability.guard';
import { GestionHabilitadaGuard } from '../../../core/guards/gestion-habilitada.guard';
import { AuditComponent } from './audit.component';
import { BudgetService } from './budget.service';
import { DirectiveCeilingComponent } from './directive-ceiling.component';
import { DistributionComponent } from './distribution.component';
import { FiscalYearComponent } from './fiscal-year.component';
import { ImportsComponent } from './imports.component';
import { MonedaPipe } from './moneda.pipe';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';
import { ReformsComponent } from './reforms.component';
import { TerritorialComponent } from './territorial.component';

const routes: Routes = [
  { path: '', redirectTo: 'gestion-fiscal', pathMatch: 'full' },
  {
    path: 'gestion-fiscal',
    component: FiscalYearComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
  {
    path: 'techo-directivo',
    component: DirectiveCeilingComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'categorias-programaticas',
    component: ProgrammaticCategoriesComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'distribucion',
    component: DistributionComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'distribucion-territorial',
    component: TerritorialComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'importaciones',
    component: ImportsComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.import'] },
  },
  {
    path: 'reformulaciones',
    component: ReformsComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.reform', 'sis_poa.formulate'] },
  },
  {
    path: 'auditoria',
    component: AuditComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: ['sis_poa.budget.audit_read'] },
  },
];

@NgModule({
  declarations: [
    FiscalYearComponent,
    DirectiveCeilingComponent,
    ProgrammaticCategoriesComponent,
    DistributionComponent,
    ImportsComponent,
    TerritorialComponent,
    ReformsComponent,
    AuditComponent,
    MonedaPipe,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
  providers: [BudgetService],
})
export class BudgetModule {}
