import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConsolidacionRoutingModule } from './consolidacion-routing.module';
import { ConsolidacionDashboardComponent } from './consolidacion-dashboard.component';
import { ConsolidacionDetalleComponent } from './consolidacion-detalle.component';
import { ConsolidacionService } from './consolidacion.service';

@NgModule({
  declarations: [
    ConsolidacionDashboardComponent,
    ConsolidacionDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    ConsolidacionRoutingModule,
  ],
  providers: [ConsolidacionService],
})
export class ConsolidacionModule {}
