import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { modulosPendientes } from '../sistemas/modulos-pendientes';

/**
 * SIS-PRO — Ciclo del Proyecto (plan maestro §18.1).
 *
 * El sistema está en depuración: se retiró la UI V2 anterior (cartera,
 * preinversión, asistentes ITCP/TDR/EDTP) junto con su backend, porque no
 * llegó a usarse —ninguna de sus tablas tenía un solo registro— y su modelo
 * de datos no acompañaba la codificación vigente. Cada módulo se reconstruye
 * desde cero; mientras tanto todas las rutas resuelven al placeholder.
 */
const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  ...modulosPendientes(
    [
      { ruta: 'dashboard', nombre: 'Dashboard de proyectos' },
      { ruta: 'proyectos', nombre: 'Cartera de proyectos' },
      { ruta: 'preinversion', nombre: 'Preinversión' },
      { ruta: 'preinversion/inventario', nombre: 'Inventario documental' },
      { ruta: 'formulacion', nombre: 'Formulación técnica' },
      { ruta: 'contratacion', nombre: 'Contratación' },
      { ruta: 'ejecucion', nombre: 'Ejecución' },
      { ruta: 'supervision', nombre: 'Supervisión / Fiscalización' },
      { ruta: 'seguimiento', nombre: 'Seguimiento de proyectos' },
    ],
    'SIS-PRO',
    '/sistemas',
    ['sis_pro.project.read'],
  ),
];

@NgModule({
  imports: [CommonModule, RouterModule.forChild(routes)],
})
export class SisProModule {}
