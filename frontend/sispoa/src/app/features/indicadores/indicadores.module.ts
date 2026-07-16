import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { IndicadoresComponent } from './indicadores.component';

const routes: Routes = [
  { path: '', component: IndicadoresComponent },
];

@NgModule({
  declarations: [IndicadoresComponent],
  imports: [CommonModule, RouterModule.forChild(routes)],
})
export class IndicadoresModule { }
