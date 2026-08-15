import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  readonly systems = [
    { code: 'SIS-PE', title: 'Planificación Estratégica', desc: 'Articulación nacional, territorial, PAD y PEI.', route: '/sis-pe', cls: 'pe', progress: 68, meta: 'PAD · PEI · Articulación' },
    { code: 'SIS-POA', title: 'Planificación Operativa', desc: 'Gestión fiscal, techos, distribución, POA y POAU.', route: '/sis-poa', cls: 'poa', progress: 54, meta: 'POA · POAU · Presupuesto' },
    { code: 'SIS-PRO', title: 'Gestión de Proyectos', desc: 'Cartera, condiciones previas, preinversión y ejecución.', route: '/sis-pro', cls: 'pro', progress: 41, meta: 'ITCP · EDTP · Ejecución' }
  ];

  readonly activity = [
    ['Techos 2027', 'Se cargó el techo institucional SIGEP', 'Hace 18 min'],
    ['Matriz PEI', 'Planificación Estratégica actualizó 12 resultados', 'Hace 1 h'],
    ['POAU', 'Unidad de Catastro guardó borrador de programación', 'Hace 2 h'],
    ['Proyecto', 'Se registró una nueva condición previa', 'Ayer']
  ];
}
