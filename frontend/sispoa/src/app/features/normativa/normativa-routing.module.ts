import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { NormativaListaComponent } from './normativa-lista.component';
import { NormativaDetalleComponent } from './normativa-detalle.component';

const routes: Routes = [
  { path: '', component: NormativaListaComponent },
  { path: ':id', component: NormativaDetalleComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class NormativaRoutingModule {}
