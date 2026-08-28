import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { POAU_CAPABILITIES } from '../../core/config/poau-capabilities';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { GestionHabilitadaGuard } from '../../core/guards/gestion-habilitada.guard';
import { PoauWizardComponent } from './formulacion/poau-wizard.component';
import { PoauMatrizViewerComponent } from './formulacion/poau-matriz-viewer.component';

/**
 * POAU — Programación de Operaciones Anual por Unidad.
 *
 * La ruta raíz es el asistente de formulación: desagrega una acción de corto
 * plazo del POA en operaciones, actividades y tareas, con programación física
 * mensual. En consonancia con los asistentes de PAD, PEI y POA.
 */
const routes: Routes = [
  {
    // Antes esta ruta no tenía guard: cualquier sesión autenticada entraba
    // por URL, sin importar su rol.
    path: '',
    component: PoauWizardComponent,
    canActivate: [CapabilityGuard, GestionHabilitadaGuard],
    data: { capacidades: POAU_CAPABILITIES },
  },
];

@NgModule({
  declarations: [PoauWizardComponent, PoauMatrizViewerComponent],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class PoauModule {}
