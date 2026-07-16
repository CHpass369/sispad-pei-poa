import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { PresupuestoDashboardComponent } from './presupuesto-dashboard.component';
import { ProgramaListaComponent } from './programa-lista.component';
import { LineaPresupuestariaListaComponent } from './linea-presupuestaria-lista.component';

const routes: Routes = [
  { path: '', component: PresupuestoDashboardComponent },
  { path: 'programas', component: ProgramaListaComponent },
  { path: 'lineas', component: LineaPresupuestariaListaComponent },
];

@NgModule({
  declarations: [
    PresupuestoDashboardComponent,
    ProgramaListaComponent,
    LineaPresupuestariaListaComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
  ],
})
export class PresupuestoModule { }
