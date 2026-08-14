import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatrizPlanificacionComponent } from './matriz-planificacion.component';
import { ArticulacionComponent } from './articulacion.component';

const routes: Routes = [
  { path: 'matriz', component: MatrizPlanificacionComponent },
  { path: 'articulacion', component: ArticulacionComponent },
  { path: '', redirectTo: 'articulacion', pathMatch: 'full' },
];

@NgModule({
  declarations: [MatrizPlanificacionComponent, ArticulacionComponent],
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule.forChild(routes)],
})
export class PlanificacionModule { }
