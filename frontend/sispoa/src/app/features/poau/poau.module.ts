import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
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
  { path: '', component: PoauWizardComponent },
];

@NgModule({
  declarations: [PoauWizardComponent, PoauMatrizViewerComponent],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class PoauModule {}
