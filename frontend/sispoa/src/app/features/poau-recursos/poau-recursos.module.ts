import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { PoauRecursosWizardComponent } from './poau-recursos-wizard.component';
import { PoauRecursosViewerComponent } from './poau-recursos-viewer.component';

/**
 * POAU — Programación Presupuestaria (requerimientos).
 *
 * Contraparte financiera de la programación física del POAU, en consonancia
 * con los asistentes de PAD, PEI, POA y POAU.
 */
const routes: Routes = [
  { path: '', component: PoauRecursosWizardComponent },
];

@NgModule({
  declarations: [PoauRecursosWizardComponent, PoauRecursosViewerComponent],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class PoauRecursosModule {}
