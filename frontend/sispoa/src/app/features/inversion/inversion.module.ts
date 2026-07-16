import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { ProyectoListaComponent } from './proyecto-lista.component';

const routes: Routes = [
  { path: '', component: ProyectoListaComponent },
];

@NgModule({
  declarations: [ProyectoListaComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class InversionModule { }
