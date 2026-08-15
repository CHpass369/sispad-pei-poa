import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { MatricesPadHomeComponent } from './matrices-pad-home.component';
import { MatrizPadWizardComponent } from './matriz-pad-wizard.component';
import { MatrizAVisualizadorComponent } from './matriz-a-visualizador.component';
import { MatrizBVisualizadorComponent } from './matriz-b-visualizador.component';
import { TablaJerarquicaComponent } from './tabla-jerarquica.component';
import { MapaConexionesComponent } from './mapa-conexiones.component';
import { MatrizAcumuladaComponent } from './matriz-acumulada.component';

const routes: Routes = [
  { path: '', component: MatricesPadHomeComponent },
  { path: 'acumulada', component: MatrizAcumuladaComponent },
  { path: 'nuevo', component: MatrizPadWizardComponent },
  { path: 'nuevo/:id', component: MatrizPadWizardComponent },
  { path: ':id/matriz-a', component: MatrizAVisualizadorComponent },
  { path: ':id/matriz-b', component: MatrizBVisualizadorComponent },
  { path: ':id/matriz-b/mapa', component: MapaConexionesComponent },
];

@NgModule({
  declarations: [
    MatricesPadHomeComponent,
    MatrizPadWizardComponent,
    MatrizAVisualizadorComponent,
    MatrizBVisualizadorComponent,
    TablaJerarquicaComponent,
    MapaConexionesComponent,
    MatrizAcumuladaComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class MatricesPadModule {}
