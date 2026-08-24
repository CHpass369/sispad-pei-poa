import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { GestionHabilitadaGuard } from '../../core/guards/gestion-habilitada.guard';
import { ActaFormComponent } from './acta-form.component';
import { ActaOficialComponent } from './acta-oficial.component';
import { ActasListadoComponent } from './actas-listado.component';
import { MatricesPriorizacionComponent } from './matrices-priorizacion.component';

// La priorizacion es de la gestion habilitada: sin candado no se entra (ADR-007).
const candado = [GestionHabilitadaGuard];

const routes: Routes = [
  { path: '', redirectTo: 'actas', pathMatch: 'full' },
  { path: 'actas', component: ActasListadoComponent, canActivate: candado },
  // Antes de ':id', si no 'nueva' se toma como identificador.
  { path: 'actas/nueva', component: ActaFormComponent, canActivate: candado },
  { path: 'actas/:id', component: ActaFormComponent, canActivate: candado },
  { path: 'actas/:id/acta', component: ActaOficialComponent, canActivate: candado },
  { path: 'matrices', component: MatricesPriorizacionComponent, canActivate: candado },
];

@NgModule({
  declarations: [
    ActasListadoComponent,
    ActaFormComponent,
    ActaOficialComponent,
    MatricesPriorizacionComponent,
  ],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class PriorizacionModule {}
