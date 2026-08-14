import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../../core/guards/capability.guard';
import { BudgetService } from './budget.service';
import { DirectiveCeilingComponent } from './directive-ceiling.component';
import { FiscalYearComponent } from './fiscal-year.component';
import { MonedaPipe } from './moneda.pipe';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';

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
];

@NgModule({
  declarations: [
    FiscalYearComponent,
    DirectiveCeilingComponent,
    ProgrammaticCategoriesComponent,
    MonedaPipe,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
  providers: [BudgetService],
})
export class BudgetModule {}
