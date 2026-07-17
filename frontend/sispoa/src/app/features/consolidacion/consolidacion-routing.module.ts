import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ConsolidacionDashboardComponent } from './consolidacion-dashboard.component';
import { ConsolidacionDetalleComponent } from './consolidacion-detalle.component';

const routes: Routes = [
  { path: '', component: ConsolidacionDashboardComponent },
  { path: ':gestion_id', component: ConsolidacionDetalleComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ConsolidacionRoutingModule {}
