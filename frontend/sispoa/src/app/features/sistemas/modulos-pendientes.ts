import { Route } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { ModuloPendienteComponent } from './modulo-pendiente.component';

/**
 * Genera rutas de módulos del plan maestro (§18.1) aún en desarrollo.
 * Cada ruta muestra la página genérica "módulo en desarrollo" con el
 * nombre oficial del módulo y su ubicación en el roadmap.
 */
export function modulosPendientes(
  modulos: { ruta: string; nombre: string }[],
  sistema: string,
  volver: string,
  capacidades: string[],
): Route[] {
  return modulos.map(m => ({
    path: m.ruta,
    component: ModuloPendienteComponent,
    canActivate: [CapabilityGuard],
    data: {
      capacidades,
      modulo: m.nombre,
      sistema,
      volver,
    },
  }));
}
