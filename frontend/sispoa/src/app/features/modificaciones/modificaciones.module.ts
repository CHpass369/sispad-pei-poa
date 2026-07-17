import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ModificacionesRoutingModule } from './modificaciones-routing.module';
import { ModificacionesListaComponent } from './modificaciones-lista.component';
import { ModificacionFormComponent } from './modificacion-form.component';
import { ModificacionDetalleComponent } from './modificacion-detalle.component';
import { ModificacionesService } from './modificaciones.service';

@NgModule({
  declarations: [
    ModificacionesListaComponent,
    ModificacionFormComponent,
    ModificacionDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    ModificacionesRoutingModule,
  ],
  providers: [ModificacionesService],
})
export class ModificacionesModule {}
