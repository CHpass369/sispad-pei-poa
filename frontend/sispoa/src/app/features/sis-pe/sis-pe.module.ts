import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { SisPeArbolComponent } from './sis-pe-arbol.component';
import { SisPeDashboardComponent } from './sis-pe-dashboard.component';
import { SisPeInstrumentosComponent } from './sis-pe-instrumentos.component';
import { SisPeVersionComponent } from './sis-pe-version.component';

const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    component: SisPeDashboardComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pe.instrumento.read'] },
  },
  {
    path: 'instrumentos',
    component: SisPeInstrumentosComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pe.instrumento.read'] },
  },
  {
    path: 'versiones/:id',
    component: SisPeVersionComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ['sis_pe.instrumento.read'] },
  },
];

@NgModule({
  declarations: [
    SisPeDashboardComponent,
    SisPeInstrumentosComponent,
    SisPeVersionComponent,
    SisPeArbolComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class SisPeModule {}
