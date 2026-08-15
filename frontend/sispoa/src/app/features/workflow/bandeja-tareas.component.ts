import { Component, OnInit } from '@angular/core';
import { WorkflowV2Service } from './workflow-v2.service';
import { WorkflowInstanceV2, WorkflowTaskV2 } from './models/workflow-v2.model';

/** Etiquetas en español de los estados de tarea (EstadosTarea del backend). */
export const ESTADOS_TAREA: Record<string, string> = {
  pendiente: 'Pendiente',
  en_curso: 'En curso',
  completada: 'Completada',
  rechazada: 'Rechazada',
};

/** Bandeja de tareas del motor de workflow V2 (mis tareas + acciones). */
@Component({
  selector: 'app-bandeja-tareas',
  standalone: false,
  templateUrl: './bandeja-tareas.component.html',
})
export class BandejaTareasComponent implements OnInit {
  tareas: WorkflowTaskV2[] = [];
  filtradas: WorkflowTaskV2[] = [];
  cargando = true;
  error = '';
  mensaje = '';

  filtroEstado = '';
  busqueda = '';

  tareaSeleccionadaId: string | null = null;
  instanciaSeleccionada: WorkflowInstanceV2 | null = null;
  cargandoInstancia = false;

  readonly estados = ESTADOS_TAREA;
  readonly estadoKeys = Object.keys(ESTADOS_TAREA);

  constructor(private service: WorkflowV2Service) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.service.listarTareas({ mias: true }).subscribe({
      next: (pagina) => {
        this.tareas = pagina.results;
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar las tareas';
        this.cargando = false;
      },
    });
  }

  aplicarFiltros(): void {
    const q = this.busqueda.trim().toLowerCase();
    this.filtradas = this.tareas.filter((t) => {
      const porEstado = !this.filtroEstado || t.estado === this.filtroEstado;
      const porBusqueda = !q
        || t.definicion.toLowerCase().includes(q)
        || t.paso_nombre.toLowerCase().includes(q);
      return porEstado && porBusqueda;
    });
  }

  obtenerClaseEstado(estado: string): string {
    const clases: Record<string, string> = {
      pendiente: 'bg-gray-100 text-gray-700',
      en_curso: 'bg-blue-100 text-blue-700',
      completada: 'bg-green-100 text-green-700',
      rechazada: 'bg-red-100 text-red-700',
    };
    return clases[estado] || 'bg-gray-100 text-gray-700';
  }

  tieneAcciones(tarea: WorkflowTaskV2): boolean {
    return tarea.estado === 'pendiente' || tarea.estado === 'en_curso';
  }

  verInstancia(tarea: WorkflowTaskV2): void {
    if (this.tareaSeleccionadaId === tarea.id) {
      this.tareaSeleccionadaId = null;
      this.instanciaSeleccionada = null;
      return;
    }
    this.tareaSeleccionadaId = tarea.id;
    this.instanciaSeleccionada = null;
    this.cargandoInstancia = true;
    this.service.obtenerInstancia(tarea.instancia).subscribe({
      next: (instancia) => {
        this.instanciaSeleccionada = instancia;
        this.cargandoInstancia = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el detalle de la instancia';
        this.cargandoInstancia = false;
      },
    });
  }

  aprobar(tarea: WorkflowTaskV2): void {
    this.service.aprobarInstancia(tarea.instancia).subscribe({
      next: () => {
        this.mensaje = 'Instancia aprobada';
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo aprobar la instancia';
      },
    });
  }

  observar(tarea: WorkflowTaskV2): void {
    const texto = window.prompt('Texto de la observación:');
    if (!texto || !texto.trim()) return;
    this.service.observarInstancia(tarea.instancia, texto.trim()).subscribe({
      next: () => {
        this.mensaje = 'Observación registrada';
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo registrar la observación';
      },
    });
  }

  delegar(tarea: WorkflowTaskV2): void {
    const delegadoA = window.prompt('ID del usuario delegado:');
    if (!delegadoA || !delegadoA.trim()) return;
    this.service.delegarInstancia(tarea.instancia, delegadoA.trim()).subscribe({
      next: () => {
        this.mensaje = 'Tarea delegada';
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo delegar la tarea';
      },
    });
  }

  avanzar(tarea: WorkflowTaskV2): void {
    this.service.avanzarInstancia(tarea.instancia).subscribe({
      next: () => {
        this.mensaje = 'Instancia avanzada';
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo avanzar la instancia';
      },
    });
  }
}
