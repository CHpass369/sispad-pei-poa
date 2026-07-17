import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { NotificacionesListaComponent } from './notificaciones-lista.component';
import { NotificacionesPreferenciasComponent } from './notificaciones-preferencias.component';

const routes: Routes = [
  { path: '', component: NotificacionesListaComponent },
  { path: 'preferencias', component: NotificacionesPreferenciasComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class NotificacionesRoutingModule {}
