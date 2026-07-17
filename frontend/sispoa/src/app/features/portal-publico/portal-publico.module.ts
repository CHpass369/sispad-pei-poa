import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalPublicoRoutingModule } from './portal-publico-routing.module';
import { PortalInicioComponent } from './portal-inicio.component';
import { PortalPlanesComponent } from './portal-planes.component';
import { PortalIndicadoresComponent } from './portal-indicadores.component';
import { PortalEstadisticasComponent } from './portal-estadisticas.component';
import { PortalPublicoService } from './portal-publico.service';

@NgModule({
  declarations: [
    PortalInicioComponent,
    PortalPlanesComponent,
    PortalIndicadoresComponent,
    PortalEstadisticasComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    PortalPublicoRoutingModule,
  ],
  providers: [PortalPublicoService],
})
export class PortalPublicoModule {}
