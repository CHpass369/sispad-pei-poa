import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ModificacionesListaComponent } from './modificaciones-lista.component';
import { ModificacionFormComponent } from './modificacion-form.component';
import { ModificacionDetalleComponent } from './modificacion-detalle.component';

const routes: Routes = [
  { path: '', component: ModificacionesListaComponent },
  { path: 'nueva', component: ModificacionFormComponent },
  { path: ':id', component: ModificacionDetalleComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ModificacionesRoutingModule {}
