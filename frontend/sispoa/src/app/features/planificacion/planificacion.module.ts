import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { FormulacionWizardComponent } from './formulacion-wizard.component';
import { MatrizPlanificacionComponent } from './matriz-planificacion.component';
import { ArticulacionComponent } from './articulacion.component';

const routes: Routes = [
  { path: 'formulacion', component: FormulacionWizardComponent },
  { path: 'formulacion/:unidadId', component: FormulacionWizardComponent },
  { path: 'matriz', component: MatrizPlanificacionComponent },
  { path: 'articulacion', component: ArticulacionComponent },
  { path: '', redirectTo: 'articulacion', pathMatch: 'full' },
];

@NgModule({
  declarations: [FormulacionWizardComponent, MatrizPlanificacionComponent, ArticulacionComponent],
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule.forChild(routes)],
})
export class PlanificacionModule { }
