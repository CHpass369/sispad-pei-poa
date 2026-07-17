import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SeguimientoRoutingModule } from './seguimiento-routing.module';
import { SeguimientoDashboardComponent } from './seguimiento-dashboard.component';
import { RegistroSeguimientoComponent } from './registro-seguimiento.component';
import { AlertasListaComponent } from './alertas-lista.component';
import { SeguimientoService } from './seguimiento.service';

@NgModule({
  declarations: [
    SeguimientoDashboardComponent,
    RegistroSeguimientoComponent,
    AlertasListaComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    SeguimientoRoutingModule,
  ],
  providers: [SeguimientoService],
})
export class SeguimientoModule {}
