import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../../core/guards/capability.guard';
import { BudgetService } from './budget.service';
import { DirectiveCeilingComponent } from './directive-ceiling.component';
import { DistributionComponent } from './distribution.component';
import { FiscalYearComponent } from './fiscal-year.component';
import { ImportsComponent } from './imports.component';
import { MonedaPipe } from './moneda.pipe';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';
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
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'categorias-programaticas',
    component: ProgrammaticCategoriesComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'distribucion',
    component: DistributionComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'distribucion-territorial',
    component: TerritorialComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
  },
  {
    path: 'importaciones',
    component: ImportsComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.budget.import'] },
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
    MonedaPipe,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
  providers: [BudgetService],
})
export class BudgetModule {}
