import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NotificacionesRoutingModule } from './notificaciones-routing.module';
import { NotificacionesListaComponent } from './notificaciones-lista.component';
import { NotificacionesPreferenciasComponent } from './notificaciones-preferencias.component';
import { NotificacionesService } from './notificaciones.service';

@NgModule({
  declarations: [
    NotificacionesListaComponent,
    NotificacionesPreferenciasComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    NotificacionesRoutingModule,
  ],
  providers: [NotificacionesService],
})
export class NotificacionesModule {}
