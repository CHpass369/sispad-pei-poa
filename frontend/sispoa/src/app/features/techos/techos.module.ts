import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { TechoListaComponent } from './techo-lista.component';
import { DistribucionListaComponent } from './distribucion-lista.component';

const routes: Routes = [
  { path: '', component: TechoListaComponent },
  { path: 'distribucion', component: DistribucionListaComponent },
];

@NgModule({
  declarations: [
    TechoListaComponent,
    DistribucionListaComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
  ],
})
export class TechosModule { }
