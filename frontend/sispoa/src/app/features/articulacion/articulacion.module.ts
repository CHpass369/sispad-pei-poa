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
import { ArticulacionFormM1Component } from './articulacion-form-m1.component';
import { ArticulacionFormM2Component } from './articulacion-form-m2.component';
import { ArticulacionFormM3Component } from './articulacion-form-m3.component';
import { ArticulacionFormM4Component } from './articulacion-form-m4.component';
import { ArticulacionFormM5Component } from './articulacion-form-m5.component';

const routes: Routes = [
  { path: '', component: ArticulacionHomeComponent },
  { path: 'pad-pei', component: MatrizPADPEIComponent },
  { path: 'pad-pei/nuevo', component: ArticulacionFormM1Component },
  { path: 'pei-poa', component: MatrizPEIPOAComponent },
  { path: 'pei-poa/nuevo', component: ArticulacionFormM2Component },
  { path: 'poa-poau', component: MatrizPOAPOAUComponent },
  { path: 'poa-poau/nuevo', component: ArticulacionFormM3Component },
  { path: 'presupuesto-seguimiento', component: MatrizPresupuestoSeguimientoComponent },
  { path: 'presupuesto-seguimiento/nuevo', component: ArticulacionFormM4Component },
  { path: 'objetos-gasto', component: MatrizObjetosGastoComponent },
  { path: 'objetos-gasto/nuevo', component: ArticulacionFormM5Component },
];

@NgModule({
  declarations: [
    ArticulacionHomeComponent,
    MatrizPADPEIComponent,
    MatrizPEIPOAComponent,
    MatrizPOAPOAUComponent,
    MatrizPresupuestoSeguimientoComponent,
    MatrizObjetosGastoComponent,
    ArticulacionFormM1Component,
    ArticulacionFormM2Component,
    ArticulacionFormM3Component,
    ArticulacionFormM4Component,
    ArticulacionFormM5Component,
  ],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class ArticulacionModule {}
