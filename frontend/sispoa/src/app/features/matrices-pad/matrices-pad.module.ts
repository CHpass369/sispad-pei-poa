import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { PadWizardComponent } from './pad/pad-wizard.component';
import { PadHomeComponent } from './pad/pad-home.component';
import { PadRegistrosComponent } from './pad/pad-registros.component';
import { PadMatrizViewerComponent } from './pad/pad-matriz-viewer.component';
import { MatrizAVisualizadorComponent } from './matriz-a-visualizador.component';
import { MatrizBVisualizadorComponent } from './matriz-b-visualizador.component';
import { TablaJerarquicaComponent } from './tabla-jerarquica.component';
import { MapaConexionesComponent } from './mapa-conexiones.component';
import { MatrizAcumuladaComponent } from './matriz-acumulada.component';

/**
 * Matrices PAD — Plan Autónomo de Desarrollo 2026-2030.
 *
 * La ruta raíz es el asistente de construcción de las Matrices "A" y "B",
 * en consonancia con el asistente de la Matriz PEI. Las vistas por borrador
 * y la matriz acumulada de la gestión siguen disponibles como consulta.
 */
const routes: Routes = [
  { path: '', component: PadHomeComponent },
  { path: 'nuevo', component: PadWizardComponent },
  { path: 'nuevo/:id', component: PadWizardComponent },
  { path: 'registros', component: PadRegistrosComponent },
  { path: 'acumulada', component: MatrizAcumuladaComponent },
  { path: ':id/matriz-a', component: MatrizAVisualizadorComponent },
  { path: ':id/matriz-b', component: MatrizBVisualizadorComponent },
  { path: ':id/matriz-b/mapa', component: MapaConexionesComponent },
];

@NgModule({
  declarations: [
    PadHomeComponent,
    PadRegistrosComponent,
    PadWizardComponent,
    PadMatrizViewerComponent,
    MatrizAVisualizadorComponent,
    MatrizBVisualizadorComponent,
    TablaJerarquicaComponent,
    MapaConexionesComponent,
    MatrizAcumuladaComponent,
  ],
  imports: [CommonModule, FormsModule, SharedModule, RouterModule.forChild(routes)],
})
export class MatricesPadModule {}
