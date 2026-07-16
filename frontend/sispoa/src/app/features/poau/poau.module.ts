import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { PoauListaComponent } from './poau-lista.component';
import { PoauFormComponent } from './poau-form.component';

const routes: Routes = [
  { path: '', component: PoauListaComponent },
  { path: 'nuevo', component: PoauFormComponent },
  { path: ':id', component: PoauFormComponent },
];

@NgModule({
  declarations: [PoauListaComponent, PoauFormComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class PoauModule { }
