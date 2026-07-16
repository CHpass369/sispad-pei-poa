import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { MapaInversionesComponent } from './mapa-inversiones.component';

const routes: Routes = [
  { path: 'mapa', component: MapaInversionesComponent },
  { path: '', redirectTo: 'mapa', pathMatch: 'full' },
];

@NgModule({
  declarations: [MapaInversionesComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class TerritorioModule { }
