import { Component, OnInit } from '@angular/core';
import {
  ApiErrorResponse,
  BudgetImport,
  BudgetService,
  CAMPOS_IMPORTACION,
  FiscalYear,
  ImportErrorItem,
} from './budget.service';

interface FilaMapeo {
  columna: string;
  campo: string;
}

interface PasosDef {
  numero: number;
  titulo: string;
}

@Component({
  standalone: false,
  selector: 'app-imports',
  templateUrl: './imports.component.html',
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
    .page-header h2 { margin: 0; }
    .wizard { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .wizard .paso { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.875rem; border: 1px solid var(--border); border-radius: 999px; font-size: 0.8125rem; color: var(--text-secondary); }
    .wizard .paso.activo { border-color: var(--primary); background: #F4F8FD; color: var(--primary); font-weight: 600; }
    .wizard .paso .num { width: 1.4rem; height: 1.4rem; border-radius: 50%; background: var(--border); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; }
    .wizard .paso.activo .num { background: var(--primary); }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1.125rem 1.25rem; margin-bottom: 1rem; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input, select.input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; width: 100%; box-sizing: border-box; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .data-table th { font-weight: 600; }
    .acciones { display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap; }
    .alert-error { background: var(--mdc-red-50); color: var(--mdc-red-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .loading, .empty { text-align: center; padding: 1.5rem; color: var(--text-secondary); }
    .badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #F57F17; }
    .badge-error { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-critical { background: #B71C1C; color: #fff; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .estado-archivo { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.5rem; word-break: break-all; }
    .resumen-conteos { display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 0.75rem 0; }
    .resumen-conteos .item { border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.875rem; font-size: 0.8125rem; }
    .resumen-conteos .item b { display: block; font-size: 1rem; }
  `],
})
export class ImportsComponent implements OnInit {
  pasos: PasosDef[] = [
    { numero: 1, titulo: 'Subir archivo' },
    { numero: 2, titulo: 'Hoja y mapeo' },
    { numero: 3, titulo: 'Validar' },
    { numero: 4, titulo: 'Aplicar' },
  ];
  paso = 1;

  gestiones: FiscalYear[] = [];
  gestionSeleccionada: string | null = null;
  perfil = 'PIP_GASTOS_HISTORICO';
  archivo: File | null = null;
  importacion: BudgetImport | null = null;
  importaciones: BudgetImport[] = [];

  hojas: string[] = [];
  hojaSeleccionada = '';
  filasMapeo: FilaMapeo[] = [];
  camposDisponibles = CAMPOS_IMPORTACION;

  errores: ImportErrorItem[] = [];
  conteos: Record<string, number> = {};
  resultado: string | null = null;

  cargando = false;
  validando = false;
  aplicando = false;
  error = '';
  mensaje = '';

  constructor(private service: BudgetService) {}

  ngOnInit(): void {
    this.service.listar().subscribe({
      next: (data) => {
        this.gestiones = data.results;
        if (this.gestiones.length > 0) {
          this.seleccionarGestion(this.gestiones[0].id);
        }
      },
      error: () => {
        this.error = 'Error al cargar las gestiones fiscales';
      },
    });
  }

  seleccionarGestion(id: string): void {
    this.gestionSeleccionada = id;
    this.error = '';
    this.service.listarImportaciones({ gestion: id }).subscribe({
      next: (r) => { this.importaciones = r.results; },
      error: () => { /* no bloquea */ },
    });
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivo = input.files?.item(0) ?? null;
    this.error = '';
  }

  // -- Paso 1: subir --------------------------------------------------------

  subir(): void {
    if (!this.gestionSeleccionada || !this.archivo) {
      this.error = 'Debe seleccionar gestión y archivo Excel';
      return;
    }
    this.error = '';
    this.cargando = true;
    const formData = new FormData();
    formData.append('gestion', this.gestionSeleccionada);
    formData.append('perfil', this.perfil);
    formData.append('archivo', this.archivo);
    this.service.subirImportacion(formData).subscribe({
      next: (imp) => {
        this.cargando = false;
        this.importacion = imp;
        this.mensaje = `Archivo "${imp.filename}" subido y parseado`;
        this.service.hojasImportacion(imp.id).subscribe({
          next: (h) => {
            this.hojas = h.hojas;
            this.hojaSeleccionada = imp.hoja_seleccionada || h.hojas[0] || '';
          },
          error: () => { this.hojas = [imp.hoja_seleccionada].filter(Boolean); },
        });
        this.filasMapeo = Object.entries(imp.mapeo_json?.columnas ?? {}).map(
          ([columna, campo]) => ({ columna, campo }),
        );
        this.paso = 2;
      },
      error: (err) => {
        this.cargando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  // -- Paso 2: hoja + mapeo -------------------------------------------------

  guardarMapeo(): void {
    if (!this.importacion) return;
    this.error = '';
    this.cargando = true;
    const columnas: Record<string, string | null> = {};
    this.filasMapeo.forEach((f) => { columnas[f.columna] = f.campo || null; });
    this.service.mapearImportacion(this.importacion.id, {
      hoja: this.hojaSeleccionada,
      mapeo: {
        columnas,
        fuentes: this.importacion.mapeo_json?.fuentes ?? {},
      },
    }).subscribe({
      next: (imp) => {
        this.cargando = false;
        this.importacion = imp;
        this.mensaje = `Mapeo aplicado sobre la hoja "${imp.hoja_seleccionada}"`;
        this.paso = 3;
      },
      error: (err) => {
        this.cargando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  // -- Paso 3: validar ------------------------------------------------------

  validar(): void {
    if (!this.importacion) return;
    this.error = '';
    this.validando = true;
    this.service.validarImportacion(this.importacion.id).subscribe({
      next: (imp) => {
        this.validando = false;
        this.importacion = imp;
        this.conteos = imp.conteos;
        this.cargarErrores();
      },
      error: (err) => {
        this.validando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  cargarErrores(): void {
    if (!this.importacion) return;
    this.service.erroresImportacion(this.importacion.id).subscribe({
      next: (errs) => { this.errores = errs; },
      error: () => { this.errores = []; },
    });
  }

  get bloques(): boolean {
    const c = this.conteos ?? {};
    return (c['CRITICAL'] ?? 0) > 0 || (c['ERROR'] ?? 0) > 0;
  }

  get erroresFiltrados(): ImportErrorItem[] {
    const c = this.conteos ?? {};
    const sinSeveridad = Object.keys(c).length === 0;
    return sinSeveridad ? [] : this.errores;
  }

  // -- Paso 4: aplicar ------------------------------------------------------

  aplicar(): void {
    if (!this.importacion) return;
    this.error = '';
    this.aplicando = true;
    this.service.aplicarImportacion(this.importacion.id).subscribe({
      next: (resp) => {
        this.aplicando = false;
        this.importacion = resp;
        const r = resp.resultado;
        this.resultado = r
          ? `${r.aperturas_creadas} aperturas BORRADOR creadas por Bs ${r.total_importado}`
          : 'Importación aplicada';
        this.mensaje = 'Importación aplicada correctamente';
        this.paso = 4;
        if (this.gestionSeleccionada) this.seleccionarGestion(this.gestionSeleccionada);
      },
      error: (err) => {
        this.aplicando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  // -- Helpers ---------------------------------------------------------------

  severidadClase(sev: string): string {
    switch (sev) {
      case 'CRITICAL': return 'badge-critical';
      case 'ERROR': return 'badge-error';
      case 'WARNING': return 'badge-warning';
      default: return 'badge-info';
    }
  }

  estadoClase(estado: string): string {
    switch (estado) {
      case 'APLICADO': return 'badge-success';
      case 'VALIDADO': return 'badge-success';
      case 'RECHAZADO': return 'badge-critical';
      default: return 'badge-warning';
    }
  }

  mensajeError(err: { error?: ApiErrorResponse }): string {
    const body = err?.error;
    const detail = body?.error && typeof body.error === 'object' && 'detail' in body.error
      ? (body.error as { detail?: string | string[] }).detail
      : undefined;
    if (Array.isArray(detail)) return detail.join(', ');
    if (detail) return detail;
    return 'Error de la operación';
  }

  reiniciar(): void {
    this.paso = 1;
    this.importacion = null;
    this.errores = [];
    this.conteos = {};
    this.resultado = null;
    this.error = '';
    this.mensaje = '';
    this.archivo = null;
  }
}
