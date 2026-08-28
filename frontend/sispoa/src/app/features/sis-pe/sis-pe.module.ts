import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import {
  SIS_PE_CAPABILITIES,
  SIS_PE_PEI_CAPABILITIES,
} from '../../core/config/modules.config';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { modulosPendientes } from '../sistemas/modulos-pendientes';
import { PeiMatrizViewerComponent } from './pei/pei-matriz-viewer.component';
import { PeiWizardComponent } from './pei/pei-wizard.component';
import { PeiHomeComponent } from './pei/pei-home.component';
import { PeiRegistrosComponent } from './pei/pei-registros.component';

/**
 * SIS-PE — Planificación Estratégica.
 *
 * The domain is being rebuilt one tool at a time on top of a clean schema.
 * PEI is the first tool back online: it builds the official 2026-2030 planning
 * matrix. The remaining routes still resolve to the "module in development"
 * placeholder.
 */
const SIS_PE_INSTRUMENT_CAPABILITIES = ['sis_pe.instrumento.read'];

export const SIS_PE_ROUTES: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'pei',
    canActivate: [CapabilityGuard],
    data: { capacidades: SIS_PE_PEI_CAPABILITIES },
    children: [
      { path: '', component: PeiHomeComponent },
      { path: 'nuevo', component: PeiWizardComponent },
      { path: 'nuevo/:id', component: PeiWizardComponent },
      { path: 'registros', component: PeiRegistrosComponent },
    ],
  },
  ...modulosPendientes(
    [{ ruta: 'dashboard', nombre: 'Dashboard PE' }],
    'SIS-PE',
    '/sistemas',
    SIS_PE_CAPABILITIES,
  ),
  ...modulosPendientes(
    [
      { ruta: 'instrumentos', nombre: 'Instrumentos' },
      { ruta: 'diagnostico', nombre: 'Diagnóstico Integral' },
      { ruta: 'seguimiento-evaluacion', nombre: 'Seguimiento y Evaluación' },
    ],
    'SIS-PE',
    '/sistemas',
    SIS_PE_INSTRUMENT_CAPABILITIES,
  ),
];

@NgModule({
  declarations: [
    PeiHomeComponent,
    PeiWizardComponent,
    PeiRegistrosComponent,
    PeiMatrizViewerComponent,
  ],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(SIS_PE_ROUTES)],
})
export class SisPeModule {}
