import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EvaluacionListaComponent } from './evaluacion-lista.component';
import { EvaluacionFormComponent } from './evaluacion-form.component';
import { EvaluacionDetalleComponent } from './evaluacion-detalle.component';

const routes: Routes = [
  { path: '', component: EvaluacionListaComponent },
  { path: 'nueva', component: EvaluacionFormComponent },
  { path: ':id', component: EvaluacionDetalleComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class EvaluacionRoutingModule {}
