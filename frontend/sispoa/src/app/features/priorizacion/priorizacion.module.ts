import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { ActaFormComponent } from './acta-form.component';
import { ActaOficialComponent } from './acta-oficial.component';
import { ActasListadoComponent } from './actas-listado.component';
import { MatricesPriorizacionComponent } from './matrices-priorizacion.component';

const routes: Routes = [
  { path: '', redirectTo: 'actas', pathMatch: 'full' },
  { path: 'actas', component: ActasListadoComponent },
  // Antes de ':id', si no 'nueva' se toma como identificador.
  { path: 'actas/nueva', component: ActaFormComponent },
  { path: 'actas/:id', component: ActaFormComponent },
  { path: 'actas/:id/acta', component: ActaOficialComponent },
  { path: 'matrices', component: MatricesPriorizacionComponent },
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
