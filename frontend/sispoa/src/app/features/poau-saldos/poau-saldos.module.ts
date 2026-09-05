import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { GestionHabilitadaGuard } from '../../core/guards/gestion-habilitada.guard';
import { SuperAdminGuard } from '../../core/guards/super-admin.guard';
import { PoauSaldosAdminComponent } from './poau-saldos-admin.component';

/**
 * Administración del presupuesto por unidad organizacional y categoría
 * programática.
 *
 * Es el techo que el asistente de recursos ofrece para programar. Hasta la
 * gestión 2027 vivía en un arreglo estático del bundle y cambiar un monto
 * costaba un despliegue completo.
 *
 * `SuperAdminGuard` espeja el candado del backend (`IsSuperAdmin`): si la ruta
 * se abriera con un permiso más ancho, la pantalla cargaría y cada guardado
 * moriría con 403.
 */
const routes: Routes = [
  {
    path: '',
    component: PoauSaldosAdminComponent,
    canActivate: [SuperAdminGuard, GestionHabilitadaGuard],
  },
];

@NgModule({
  declarations: [PoauSaldosAdminComponent],
  imports: [
    CommonModule, FormsModule, SharedModule,
    RouterModule.forChild(routes),
  ],
})
export class PoauSaldosModule {}
