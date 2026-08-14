import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../../core/guards/capability.guard';
import { BudgetService } from './budget.service';
import { FiscalYearComponent } from './fiscal-year.component';

const routes: Routes = [
  { path: '', redirectTo: 'gestion-fiscal', pathMatch: 'full' },
  {
    path: 'gestion-fiscal',
    component: FiscalYearComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_poa.formulate'] },
  },
];

@NgModule({
  declarations: [FiscalYearComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
  providers: [BudgetService],
})
export class BudgetModule {}
