import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { RecursosListaComponent } from './recursos-lista.component';
import { RecursosFormComponent } from './recursos-form.component';

const routes: Routes = [
  { path: '', component: RecursosListaComponent },
  { path: 'nuevo', component: RecursosFormComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class RecursosRoutingModule {}
