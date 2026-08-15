import { Component, computed, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

type SystemKey = 'pe' | 'poa' | 'pro';

interface SystemConfig {
  code: string; title: string; subtitle: string; className: string; progress: number;
  modules: { title: string; text: string; route: string; badge: string }[];
  stages: string[];
}

@Component({
  selector: 'app-system-overview',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './system-overview.component.html',
  styleUrl: './system-overview.component.scss'
})
export class SystemOverviewComponent {
  private route = inject(ActivatedRoute);
  private readonly configs: Record<SystemKey, SystemConfig> = {
    pe: {
      code: 'SIS-PE', title: 'Sistema de Planificación Estratégica', subtitle: 'Del marco nacional a los resultados institucionales del Gobierno Autónomo Municipal de Sacaba.', className: 'pe', progress: 68,
      modules: [
        { title: 'Articulación Estratégica', text: 'PGDESA, PDESA, instrumentos sectoriales y su vínculo con el PAD.', route: '/sis-pe/articulacion', badge: 'Nacional → Municipal' },
        { title: 'Matriz PAD', text: 'Ejes, resultados, acciones, indicadores, territorialización y responsables.', route: '/sis-pe/pad', badge: 'Mediano plazo' },
        { title: 'Matriz PEI', text: 'Resultados institucionales, productos, indicadores y articulación con PAD.', route: '/sis-pe/pei', badge: 'Institucional' }
      ],
      stages: ['PGDESA', 'PDESA / PES', 'PAD', 'PEI']
    },
    poa: {
      code: 'SIS-POA', title: 'Sistema de Planificación Operativa', subtitle: 'Formulación anual, programación presupuestaria y asignación a unidades organizacionales.', className: 'poa', progress: 54,
      modules: [
        { title: 'Gestión Fiscal', text: 'Apertura de gestión, parámetros, vigencias, responsables y calendario.', route: '/sis-poa/gestion-fiscal', badge: 'Paso 1' },
        { title: 'Techos Presupuestarios', text: 'Techo SIGEP y recursos específicos municipales para la nueva gestión.', route: '/sis-poa/techos', badge: 'Paso 2' },
        { title: 'Distribución Presupuestaria', text: 'Distribución por fuente, organismo, tipo de gasto, programa y unidad.', route: '/sis-poa/distribucion', badge: 'Paso 3' },
        { title: 'Formulación POA', text: 'Operaciones, metas, indicadores, presupuesto y articulación PEI.', route: '/sis-poa/poa', badge: 'Formulación' },
        { title: 'Programación POAU', text: 'Asignación y programación operativa por unidad organizacional.', route: '/sis-poa/poau', badge: 'Unidades' },
        { title: 'Seguimiento', text: 'Avance físico, financiero, alertas, reprogramaciones y reportes.', route: '/sis-poa/seguimiento', badge: 'Monitoreo' }
      ],
      stages: ['Gestión fiscal', 'Techos', 'Distribución', 'POA', 'POAU']
    },
    pro: {
      code: 'SIS-PRO', title: 'Sistema de Gestión de Proyectos', subtitle: 'Ciclo municipal de proyectos desde la cartera y condiciones previas hasta la ejecución.', className: 'pro', progress: 41,
      modules: [
        { title: 'Cartera de Proyectos', text: 'Registro único, priorización, procedencia y articulación con POA.', route: '/sis-pro/cartera', badge: 'Portafolio' },
        { title: 'Condiciones Previas', text: 'Checklist técnico, legal, territorial, ambiental y financiero.', route: '/sis-pro/condiciones-previas', badge: 'ITCP' },
        { title: 'Preinversión', text: 'Estudios, EDTP, costos, diseños, documentos y aprobaciones.', route: '/sis-pro/preinversion', badge: 'Formulación' },
        { title: 'Contratación', text: 'PAC, DBC, procesos, adjudicación y trazabilidad administrativa.', route: '/sis-pro/contratacion', badge: 'Proceso' },
        { title: 'Ejecución y Seguimiento', text: 'Contratos, planillas, avance físico-financiero, modificaciones y cierre.', route: '/sis-pro/ejecucion', badge: 'Ejecución' }
      ],
      stages: ['Cartera', 'Condiciones', 'Preinversión', 'Contratación', 'Ejecución']
    }
  };
  readonly config = computed(() => this.configs[(this.route.snapshot.data['system'] as SystemKey) ?? 'pe']);
}
