import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { ArticulacionHomeComponent } from './articulacion-home.component';
import { MatrizPADPEIComponent } from './matriz-pad-pei.component';
import { MatrizPEIPOAComponent } from './matriz-pei-poa.component';
import { MatrizPOAPOAUComponent } from './matriz-poapoau.component';
import { MatrizPresupuestoSeguimientoComponent } from './matriz-presupuesto-seguimiento.component';
import { MatrizObjetosGastoComponent } from './matriz-objetos-gasto.component';

const routes: Routes = [
  { path: '', component: ArticulacionHomeComponent },
  { path: 'pad-pei', component: MatrizPADPEIComponent },
  { path: 'pei-poa', component: MatrizPEIPOAComponent },
  { path: 'poa-poau', component: MatrizPOAPOAUComponent },
  { path: 'presupuesto-seguimiento', component: MatrizPresupuestoSeguimientoComponent },
  { path: 'objetos-gasto', component: MatrizObjetosGastoComponent },
];

@NgModule({
  declarations: [
    ArticulacionHomeComponent,
    MatrizPADPEIComponent,
    MatrizPEIPOAComponent,
    MatrizPOAPOAUComponent,
    MatrizPresupuestoSeguimientoComponent,
    MatrizObjetosGastoComponent,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class ArticulacionModule {}
