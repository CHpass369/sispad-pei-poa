import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PortalInicioComponent } from './portal-inicio.component';
import { PortalPlanesComponent } from './portal-planes.component';
import { PortalIndicadoresComponent } from './portal-indicadores.component';
import { PortalEstadisticasComponent } from './portal-estadisticas.component';

const routes: Routes = [
  { path: '', component: PortalInicioComponent },
  { path: 'planes', component: PortalPlanesComponent },
  { path: 'indicadores', component: PortalIndicadoresComponent },
  { path: 'estadisticas', component: PortalEstadisticasComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PortalPublicoRoutingModule {}
