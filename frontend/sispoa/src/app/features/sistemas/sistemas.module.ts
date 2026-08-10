import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { SistemasSeleccionComponent } from './sistemas-seleccion.component';

const routes: Routes = [
  {
    path: '',
    component: SistemasSeleccionComponent,
    canActivate: [CapabilityGuard],
  },
];

@NgModule({
  declarations: [SistemasSeleccionComponent],
  imports: [CommonModule, RouterModule.forChild(routes)],
})
export class SistemasModule {}
