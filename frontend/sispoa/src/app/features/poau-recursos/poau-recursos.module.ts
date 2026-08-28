import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { POAU_CAPABILITIES } from '../../core/config/poau-capabilities';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { GestionHabilitadaGuard } from '../../core/guards/gestion-habilitada.guard';
import { PoauRecursosWizardComponent } from './poau-recursos-wizard.component';
import { PoauRecursosViewerComponent } from './poau-recursos-viewer.component';

/**
 * POAU — Programación Presupuestaria (requerimientos).
 *
 * Contraparte financiera de la programación física del POAU, en consonancia
 * con los asistentes de PAD, PEI, POA y POAU.
 */
const routes: Routes = [
  {
    // Antes esta ruta no tenía guard: cualquier sesión autenticada entraba
    // por URL, sin importar su rol.
    path: '',
    component: PoauRecursosWizardComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: POAU_CAPABILITIES },
  },
];

@NgModule({
  declarations: [PoauRecursosWizardComponent, PoauRecursosViewerComponent],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class PoauRecursosModule {}
