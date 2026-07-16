import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { GestionListaComponent } from './gestion-lista.component';
import { GestionDetalleComponent } from './gestion-detalle.component';

const routes: Routes = [
  { path: '', component: GestionListaComponent },
  { path: ':id', component: GestionDetalleComponent },
];

@NgModule({
  declarations: [
    GestionListaComponent,
    GestionDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
  ],
})
export class GestionModule { }
