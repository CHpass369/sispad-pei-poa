import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { RevisionListaComponent } from './revision-lista.component';
import { ObservacionListaComponent } from './observacion-lista.component';
import { AprobacionListaComponent } from './aprobacion-lista.component';
import { BandejaTareasComponent } from './bandeja-tareas.component';

const routes: Routes = [
  { path: '', component: RevisionListaComponent },
  { path: 'bandeja', component: BandejaTareasComponent },
  { path: 'observaciones', component: ObservacionListaComponent },
  { path: 'aprobaciones', component: AprobacionListaComponent },
];

@NgModule({
  declarations: [
    RevisionListaComponent,
    ObservacionListaComponent,
    AprobacionListaComponent,
    BandejaTareasComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
  ],
})
export class WorkflowModule { }
