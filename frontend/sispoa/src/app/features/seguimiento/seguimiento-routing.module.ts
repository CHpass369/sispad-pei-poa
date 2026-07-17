import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SeguimientoDashboardComponent } from './seguimiento-dashboard.component';
import { RegistroSeguimientoComponent } from './registro-seguimiento.component';
import { AlertasListaComponent } from './alertas-lista.component';

const routes: Routes = [
  { path: '', component: SeguimientoDashboardComponent },
  { path: 'registrar', component: RegistroSeguimientoComponent },
  { path: 'alertas', component: AlertasListaComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SeguimientoRoutingModule {}
