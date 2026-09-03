import {
  AfterViewInit, ChangeDetectorRef, Component, ElementRef, OnDestroy, OnInit,
  ViewChild,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { environment } from '../../../environments/environment';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { OpcionCombo } from '../../shared/components/combo-box/combo-box.component';

interface ColumnaMatriz { clave: string; etiqueta: string; ancho: number; }
interface BloqueMatriz {
  etiqueta: string; color: string; columnas: ColumnaMatriz[];
}
interface UnidadCatalogo { codigo: string; nombre: string; sigla: string; }

interface PoauImportPreview {
  id: string;
  estado: 'VALIDO' | 'INVALIDO' | 'APLICADO';
  resumen: {
    filas_leidas: number; filas_validas: number; filas_rechazadas: number;
    errores: number; registros_preview: number;
  };
  errores: { fila: number; campo: string; codigo: string; mensaje: string }[];
  filas: any[];
  resultado?: {
    creados: number; actualizados: number; eliminados: number;
    reemplazados: number; sin_cambios: number;
  };
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
               'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/** Las cinco bandas del formato oficial, con los colores exactos de la planilla.
 *  La cabecera va fuerte a propósito: es lo que ancla la lectura de 34 columnas.
 *  El desglose interno (COLOR_NIVEL) sí va en pastel. */
const BLOQUES_MATRIZ: BloqueMatriz[] = [
  {
    etiqueta: 'UNIDAD ORGANIZACIONAL', color: '#FF0000',
    columnas: [
      { clave: 'unidad', etiqueta: 'UNIDADES', ancho: 150 },
      { clave: 'unidad_codigo', etiqueta: 'CÓDIGO', ancho: 92 },
    ],
  },
  {
    etiqueta: 'MEDIANO PLAZO', color: '#E8A202',
    columnas: [
      { clave: 'cod_producto_pei', etiqueta: 'COD. PRODUCTO PEI', ancho: 108 },
      { clave: 'accion_institucional', etiqueta: 'ACCIÓN INSTITUCIONAL ESPECÍFICA (PEI)', ancho: 300 },
      { clave: 'cod_accion_corto_plazo', etiqueta: 'CÓDIGO ACCIÓN DE CORTO PLAZO', ancho: 132 },
      { clave: 'accion_corto_plazo', etiqueta: 'ACCIÓN DE CORTO PLAZO GESTIÓN {gestion} (PRODUCTO INSTITUCIONAL ANUAL)', ancho: 300 },
    ],
  },
  {
    etiqueta: 'CORTO PLAZO', color: '#127622',
    columnas: [
      { clave: 'categoria_programatica', etiqueta: 'CATEGORÍA PROGRAMÁTICA', ancho: 104 },
      { clave: 'denominacion_categoria', etiqueta: 'DENOMINACIÓN (CATEGORÍA PROGRAMÁTICA)', ancho: 180 },
      { clave: 'operacion', etiqueta: 'OPERACIONES (PRODUCTO INTERMEDIO)', ancho: 340 },
      { clave: 'actividad', etiqueta: 'ACTIVIDADES', ancho: 340 },
      { clave: 'tarea', etiqueta: 'TAREAS ESPECÍFICAS', ancho: 340 },
    ],
  },
  {
    etiqueta: 'PROGRAMACIÓN DE OPERACIÓN ANUAL UNIDAD', color: '#3465A4',
    columnas: [
      { clave: 'indicador', etiqueta: 'INDICADOR', ancho: 230 },
      { clave: 'formula', etiqueta: 'FÓRMULA', ancho: 210 },
      { clave: 'unidad_medida', etiqueta: 'UNIDAD DE MEDIDA', ancho: 96 },
      { clave: 'linea_base', etiqueta: 'LÍNEA BASE ({gestion_anterior})', ancho: 72 },
      { clave: 'meta', etiqueta: 'META', ancho: 72 },
      { clave: 'meta_actual', etiqueta: 'META ACTUAL', ancho: 80 },
      { clave: 'fecha_inicio', etiqueta: 'FECHA INICIO', ancho: 86 },
      { clave: 'fecha_fin', etiqueta: 'FECHA FINAL', ancho: 86 },
      { clave: 'ponderacion', etiqueta: '% PONDERACIÓN', ancho: 80 },
    ],
  },
  {
    etiqueta: 'CRONOGRAMA DE EJECUCIÓN', color: '#3465A4',
    columnas: [
      ...MESES.map(m => ({ clave: `mes_${m}`, etiqueta: m.toUpperCase(), ancho: 54 })),
      { clave: 'total_anual', etiqueta: 'TOTAL ANUAL', ancho: 84 },
      { clave: 'resultado_logrado',
        etiqueta: 'RESULTADO LOGRADO (BIEN O SERVICIO PRODUCIDO DURANTE LA GESTIÓN)', ancho: 260 },
    ],
  },
];

/**
 * Vista de árbol. Las once columnas de la cadena se colapsan en DESGLOSE: en la
 * matriz oficial cada nivel escribe en la suya, y a la altura de las tareas el
 * texto arranca recién a 440px con diez columnas vacías a la izquierda. Acá la
 * jerarquía la marca la sangría, no la posición de la columna.
 */
const BLOQUES_ARBOL: BloqueMatriz[] = [
  {
    etiqueta: 'DESGLOSE JERÁRQUICO', color: '#37474F',
    columnas: [
      { clave: 'desglose', etiqueta: 'UNIDAD · PEI · CORTO PLAZO · OPERACIÓN · ACTIVIDAD · TAREA', ancho: 620 },
      { clave: 'codigo', etiqueta: 'CÓDIGO', ancho: 190 },
    ],
  },
  ...BLOQUES_MATRIZ.slice(2).map(b => ({
    ...b,
    columnas: b.columnas.filter(c => !['operacion', 'actividad', 'tarea'].includes(c.clave)),
  })),
];

/** Resuelve `{gestion}` y `{gestion_anterior}` en las etiquetas del formato.
 *
 *  El formato oficial lleva el año escrito adentro del encabezado. Antes estaba
 *  clavado (`GESTIÓN 2027`, `LÍNEA BASE (2026)`), así que al cambiar de gestión
 *  la matriz seguía anunciando la anterior — y lo que se exporta a Excel y PDF
 *  es exactamente este encabezado. */
function conGestion(bloques: BloqueMatriz[], anio: number | null): BloqueMatriz[] {
  const gestion = anio === null ? '—' : String(anio);
  const anterior = anio === null ? '—' : String(anio - 1);
  return bloques.map(b => ({
    ...b,
    columnas: b.columnas.map(c => ({
      ...c,
      etiqueta: c.etiqueta
        .replace('{gestion_anterior}', anterior)
        .replace('{gestion}', gestion),
    })),
  }));
}

/** Color de fondo por nivel: el escalonado de la planilla, en pastel.
 *  Cada tono conserva la familia del original pero desaturado, para que la
 *  matriz se pueda leer largo rato sin cansar. */
const COLOR_NIVEL: Record<string, string> = {
  unidad: '#F7DEDC',
  aie: '#FBE9D4',
  accion: '#FDF3E6',
  operacion: '#E4EFDC',
  actividad: '#F1F7EA',
  tarea: '#FFFFFF',
};

/** Columna donde cada nivel escribe su denominación (y lleva el desplegable). */
const COLUMNA_NIVEL: Record<string, string> = {
  unidad: 'unidad',
  aie: 'accion_institucional',
  accion: 'accion_corto_plazo',
  operacion: 'operacion',
  actividad: 'actividad',
  tarea: 'tarea',
};

const ETIQUETA_NIVEL: Record<string, string> = {
  unidad: 'Unidad organizacional',
  aie: 'Acción institucional específica (PEI)',
  accion: 'Acción de corto plazo',
  operacion: 'Operación (producto intermedio)',
  actividad: 'Actividad',
  tarea: 'Tarea específica',
};

/**
 * Tinta que se lee sobre un fondo dado. Los colores de la planilla se respetan
 * tal cual, pero el ámbar `#E8A202` con blanco encima queda en 2.19:1 —
 * ilegible—, así que la tinta se elige por luminancia en vez de fijarse.
 */
function tintaSobre(fondo: string): string {
  const canal = [1, 3, 5].map(i => {
    const v = parseInt(fondo.slice(i, i + 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  const l = 0.2126 * canal[0] + 0.7152 * canal[1] + 0.0722 * canal[2];
  const contra = (otra: number) =>
    (Math.max(l, otra) + 0.05) / (Math.min(l, otra) + 0.05);
  return contra(1) >= contra(0.0176) ? '#FFFFFF' : '#1F2933';
}

/**
 * Columnas de la cadena (índices 0..10) que cada nivel llena. La última absorbe
 * las que le quedan a la derecha: en vista de árbol siempre están vacías, y sin
 * eso la denominación se lee en una franja angosta con medio ancho de tabla al
 * lado sin usar.
 */
const DATOS_NIVEL: Record<string, number[]> = {
  unidad: [0, 1], aie: [2, 3], accion: [4, 5],
  operacion: [6, 7, 8], actividad: [9], tarea: [10],
};
const FIN_CADENA = 10;  // índice de TAREAS ESPECÍFICAS

const NUMERICAS = new Set(['linea_base', 'meta', 'meta_actual', 'ponderacion',
                           'total_anual', ...MESES.map(m => `mes_${m}`)]);
const TODAS_UNIDADES = '__todas_las_unidades__';

@Component({
  selector: 'app-matriz-poau',
  standalone: false,
  template: `
    <div class="poau lienzo lienzo-datos">
      <div class="encabezado-pantalla">
        <div>
          <h2>Matriz POAU</h2>
          <p class="sub">
            Programa Operativo Anual por Unidad, gestión {{ gestion }}. Se despliega
            de lo general a lo específico.
          </p>
        </div>
        <div class="encabezado-acciones">
          <app-combo-box class="filtro" [opciones]="opcionesUnidadFiltro"
                         [ngModel]="unidadFiltro"
                         (ngModelChange)="filtrar($event)"
                         etiqueta="Filtrar por Unidad Organizacional"
                         placeholder="Buscar unidad por código, nombre o sigla"
                         [maximo]="60"></app-combo-box>
          <div class="vistas">
            <button class="btn btn-sm" [class.activa]="modo === 'arbol'"
                    (click)="cambiarModo('arbol')">Árbol</button>
            <button class="btn btn-sm" [class.activa]="modo === 'matriz'"
                    (click)="cambiarModo('matriz')">Matriz oficial</button>
          </div>
          <button class="btn btn-sm btn-secondary" (click)="expandirTodo()"
                  [disabled]="!filas.length">Expandir todo</button>
          <button class="btn btn-sm btn-secondary" (click)="contraerTodo()"
                  [disabled]="!filas.length">Contraer</button>
          <button class="btn btn-sm btn-importar" type="button"
                  (click)="abrirImportacion()" [disabled]="cargando"
                  title="Importar programación física">
            ⇧ Importar
          </button>
          <button class="btn btn-sm btn-excel" (click)="exportarExcel()"
                  [disabled]="!filas.length">⬇ Excel</button>
          <button class="btn btn-sm btn-pdf" (click)="exportarPdf()"
                  [disabled]="!filas.length">⬇ PDF</button>
        </div>
      </div>

      <div class="leyenda" *ngIf="filas.length">
        <span *ngFor="let n of niveles" class="chip"
              [style.background]="colorNivel[n]">
          {{ etiquetaNivel[n] }} · {{ conteo[n] || 0 }}
        </span>
        <span class="chip visible">{{ visibles.length }} de {{ filas.length }} filas</span>
        <span class="chip marcadas" *ngIf="seleccion.size">
          {{ seleccion.size }} seleccionada(s) · se exporta solo eso
          <button class="limpiar" (click)="limpiarSeleccion()">limpiar</button>
        </span>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>
      <div class="msg-box aviso" *ngIf="aviso && !error">{{ aviso }}</div>

      <div class="import-overlay" *ngIf="importAbierto" role="presentation"
           (keydown.escape)="cerrarImportacion()">
        <section class="import-dialog" role="dialog" aria-modal="true"
                 aria-labelledby="import-title" tabindex="-1" #importDialog>
          <header>
            <div>
              <h3 id="import-title">Importar programación física</h3>
              <p>
                <ng-container *ngIf="unidad; else elegirUnidadImport">
                  Unidad {{ unidad }} · gestión {{ gestion }}.
                </ng-container>
                <ng-template #elegirUnidadImport>Seleccione una Unidad Organizacional.</ng-template>
                Primero se valida una vista previa.
              </p>
            </div>
            <button type="button" class="import-close" aria-label="Cerrar importación"
                    (click)="cerrarImportacion()">×</button>
          </header>

          <label class="import-unit">
            Unidad Organizacional
            <app-combo-box [opciones]="opcionesUnidadImport"
                           [ngModel]="unidad"
                           (ngModelChange)="cambiarUnidadImport($event)"
                           etiqueta="Unidad Organizacional para importar"
                           placeholder="Buscar por código, nombre o sigla"
                           [maximo]="60"></app-combo-box>
          </label>

          <div class="import-impact nuevo" *ngIf="unidad && !cargando && !tienePoauSeleccionado" role="status">
            <strong>Esta Unidad Organizacional todavía no tiene un POAU.</strong>
            <p>La importación creará un nuevo POAU y llenará su árbol completo con los datos de la matriz.</p>
          </div>
          <div class="import-impact reemplazo" *ngIf="unidad && !cargando && tienePoauSeleccionado" role="alert">
            <strong>Esta Unidad Organizacional ya tiene un POAU.</strong>
            <p>Al aplicar la importación se reemplazará su árbol completo con los datos de la matriz.</p>
          </div>

          <div class="source-tabs" role="radiogroup" aria-label="Fuente de importación">
            <label><input type="radio" name="fuenteImport" value="excel"
                          [(ngModel)]="fuenteImport" (change)="limpiarPreviewImport()"> Excel</label>
            <label><input type="radio" name="fuenteImport" value="google_sheets"
                          [(ngModel)]="fuenteImport" (change)="limpiarPreviewImport()"> Google Sheets</label>
          </div>

          <div class="import-fields">
            <label *ngIf="fuenteImport === 'excel'">
              Archivo Excel (.xlsx)
              <input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                     (change)="seleccionarArchivo($event)">
            </label>
            <label *ngIf="fuenteImport === 'google_sheets'">
              Enlace de Google Sheets
              <input class="form-control" type="url" [(ngModel)]="googleUrl"
                     placeholder="https://docs.google.com/spreadsheets/d/.../edit?gid=...">
            </label>
            <label>
              Nombre de la hoja <span>(opcional si el enlace incluye gid)</span>
              <input class="form-control" [(ngModel)]="hojaImport" placeholder="POAU">
            </label>
          </div>

          <div class="msg-box error" *ngIf="importError" role="alert">{{ importError }}</div>

          <div class="import-summary" *ngIf="previewImport as p" aria-live="polite">
            <span>Leídas <strong>{{ p.resumen.filas_leidas }}</strong></span>
            <span class="ok">Válidas <strong>{{ p.resumen.filas_validas }}</strong></span>
            <span class="bad">Rechazadas <strong>{{ p.resumen.filas_rechazadas }}</strong></span>
            <span>Errores <strong>{{ p.resumen.errores }}</strong></span>
          </div>

          <div class="import-errors" *ngIf="previewImport?.errores?.length">
            <h4>Errores que bloquean la importación</h4>
            <ul>
              <li *ngFor="let e of previewImport!.errores | slice:0:50">
                <strong>{{ e.fila ? 'Fila ' + e.fila : 'Estructura' }}</strong>
                · {{ e.campo }}: {{ e.mensaje }}
              </li>
            </ul>
          </div>

          <div class="import-table" *ngIf="previewImport?.filas?.length">
            <table class="tabla tabla-compacta">
              <thead><tr><th>Fila</th><th>Nivel</th><th>Código</th><th>Denominación</th><th>Meta</th></tr></thead>
              <tbody><tr *ngFor="let f of previewImport!.filas | slice:0:20">
                <td>{{ f.fila }}</td><td>{{ f.nivel }}</td>
                <td>{{ codigoImportado(f) || 'se generará' }}</td>
                <td>{{ f[f.nivel] }}</td><td class="num">{{ f.meta }}</td>
              </tr></tbody>
            </table>
          </div>

          <div class="apply-result" *ngIf="previewImport?.resultado as r" role="status">
            Aplicación completada: {{ r.creados }} creados, {{ r.actualizados }} actualizados,
            {{ r.eliminados }} eliminados y {{ r.sin_cambios }} sin cambios.
          </div>

          <label class="replace-confirm" *ngIf="previewImport?.estado === 'VALIDO'">
            <input type="checkbox" [(ngModel)]="confirmarReemplazo">
            <span *ngIf="tienePoauSeleccionado">Confirmo que esta vista previa reemplazará el árbol POAU completo de la unidad.</span>
            <span *ngIf="!tienePoauSeleccionado">Confirmo que deseo crear el nuevo POAU con el árbol completo de esta vista previa.</span>
          </label>

          <footer>
            <button class="btn btn-secondary" type="button" (click)="cerrarImportacion()">Cerrar</button>
            <button class="btn btn-primary" type="button" (click)="previsualizarImportacion()"
                    [disabled]="!unidad || importando || aplicando">
              {{ importando ? 'Validando…' : 'Previsualizar' }}
            </button>
            <button class="btn btn-importar" type="button" (click)="aplicarImportacion()"
                    [disabled]="!unidad || aplicando || previewImport?.estado !== 'VALIDO' || !confirmarReemplazo">
              {{ aplicando ? 'Aplicando…' : (tienePoauSeleccionado ? 'Reemplazar POAU' : 'Crear nuevo POAU') }}
            </button>
          </footer>
        </section>
      </div>

      <div class="sin-datos" *ngIf="cargando">
        <div class="esqueleto" style="width:300px"></div>
        <span>Cargando la matriz POAU…</span>
      </div>

       <div class="poau-empty-state" *ngIf="mostrarEstadoVacio" role="status">
         <strong>Esta unidad todavía no tiene registros POAU.</strong>
         <p>Use el botón Importar para crear un nuevo POAU y cargar su árbol desde Excel o Google Sheets.</p>
       </div>

       <div class="tabla-caja" *ngIf="!cargando && !mostrarEstadoVacio">
         <table class="tabla tabla-compacta mz" #tabla>
          <colgroup>
            <col style="width:34px">
            <ng-container *ngFor="let b of bloques">
              <col *ngFor="let c of b.columnas" [style.width.px]="c.ancho">
            </ng-container>
            <col style="width:168px">
          </colgroup>
          <thead>
            <tr #bandas>
              <th rowspan="2" class="th-fija th-sel">
                <input type="checkbox" [checked]="todoSeleccionado()"
                       [indeterminate]="algoSeleccionado()"
                       (change)="alternarTodos()" title="Seleccionar todo">
              </th>
              <th *ngFor="let b of bloques" [attr.colspan]="b.columnas.length"
                  [style.background]="b.color"
                  [style.color]="tinta(b.color)">{{ b.etiqueta }}</th>
              <th rowspan="2" class="th-fija th-acc">ACCIONES</th>
            </tr>
            <tr>
              <ng-container *ngFor="let b of bloques">
                <th *ngFor="let c of b.columnas" class="th-col"
                    [style.background]="b.color"
                    [style.color]="tinta(b.color)">{{ c.etiqueta }}</th>
              </ng-container>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let f of visibles; trackBy: porId"
                [class.marcada]="seleccion.has(f.id)">
              <td class="td-sel" [style.background]="colorNivel[f.nivel]">
                <input type="checkbox" [checked]="seleccion.has(f.id)"
                       (change)="alternarSeleccion(f)">
              </td>
              <td *ngFor="let c of f.celdas" [attr.colspan]="c.colspan"
                  [style.background]="colorNivel[f.nivel]"
                  [class.num]="esNumero(c.clave)" [class.propia]="c.propia"
                  [ngClass]="claseCelda(f, c.clave)" [title]="tituloCelda(f, c.clave)">
                <ng-container *ngIf="c.propia; else simple">
                  <div class="nodo" [style.paddingLeft.px]="f.orden_nivel * 16">
                    <button *ngIf="f.hijos" class="desplegar" type="button"
                            [attr.aria-expanded]="expandidos.has(f.id)"
                            (click)="alternar(f)">{{ expandidos.has(f.id) ? '▾' : '▸' }}</button>
                    <span *ngIf="!f.hijos" class="hoja">•</span>
                    <span class="texto">{{ celda(f, c.clave) }}</span>
                    <span *ngIf="f.hijos" class="cuantos">{{ f.hijos }}</span>
                  </div>
                </ng-container>
                <ng-template #simple>{{ celda(f, c.clave) }}</ng-template>
              </td>
              <td class="td-acc" [style.background]="colorNivel[f.nivel]">
                <div class="acciones" *ngIf="f.objeto_id; else sinAcciones">
                  <span class="estado" [ngClass]="'e-' + f.estado"
                        [title]="f.observacion || ''">{{ f.estado }}</span>
                  <button class="acc" title="Editar en el wizard"
                          (click)="editar(f)">✎</button>
                  <button class="acc" title="Validar" [disabled]="ocupado === f.id"
                          (click)="revisar(f, 'validar')">✓</button>
                  <button class="acc" title="Aprobar" [disabled]="ocupado === f.id"
                          (click)="revisar(f, 'aprobar')">✓✓</button>
                  <button class="acc" title="Observar" [disabled]="ocupado === f.id"
                          (click)="revisar(f, 'observar')">!</button>
                  <button class="acc peligro" title="Eliminar"
                          [disabled]="ocupado === f.id" (click)="eliminar(f)">✕</button>
                </div>
                <ng-template #sinAcciones><span class="sin-acc">—</span></ng-template>
              </td>
            </tr>
            <tr *ngIf="!filas.length">
              <td [attr.colspan]="totalColumnas + 2">
                <div class="sin-datos">
                  <span class="sin-datos-icono">▤</span>
                  <strong>No hay POAUs para este filtro</strong>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ================= PROGRAMACIÓN PRESUPUESTARIA ================= -->
      <div class="bloque-presupuesto">
        <div class="encabezado-pantalla">
          <div>
            <h3>Programación presupuestaria</h3>
            <p class="sub">
              Requerimientos registrados para
              {{ unidad ? 'la unidad ' + unidad : 'todas las unidades' }},
              agrupados por categoría programática.
            </p>
          </div>
          <div class="encabezado-acciones" *ngIf="presupuesto.length">
            <span class="chip total">
              Total programado: {{ moneda(totalPresupuesto) }} Bs.
            </span>
          </div>
        </div>

        <div class="msg-box error" *ngIf="errorPresupuesto">{{ errorPresupuesto }}</div>
        <div class="sin-datos" *ngIf="cargandoPresupuesto">
          <span>Cargando programación presupuestaria…</span>
        </div>

        <div class="sin-datos" *ngIf="!cargandoPresupuesto && !errorPresupuesto
                                      && !presupuesto.length">
          <span class="sin-datos-icono">◫</span>
          <strong>Sin requerimientos presupuestados</strong>
          <span>La programación se registra en POAU (Recursos).</span>
          <a class="btn btn-sm btn-primary" routerLink="/poau_recursos">
            Ir a la programación presupuestaria
          </a>
        </div>

        <div class="tabla-caja" *ngIf="!cargandoPresupuesto && presupuesto.length">
          <table class="tabla tabla-compacta tabla-presupuesto">
            <thead>
              <tr>
                <th *ngFor="let c of columnasPresupuesto"
                    [class.num]="c.num" [style.min-width.px]="c.ancho">
                  {{ c.etiqueta }}
                </th>
              </tr>
            </thead>
            <tbody>
              <ng-container *ngFor="let cat of presupuesto">
                <!-- La categoría encabeza su grupo, como en la planilla. -->
                <tr class="fila-categoria">
                  <td [attr.colspan]="columnasPresupuesto.length - 1">
                    <strong>{{ cat.categoria || 'SIN CATEGORÍA' }}</strong>
                    <span class="denominacion">{{ cat.denominacion }}</span>
                    <span class="cuenta">{{ cat.filas.length }} requerimiento(s)</span>
                  </td>
                  <td class="num"><strong>{{ moneda(cat.total) }}</strong></td>
                </tr>
                <tr *ngFor="let f of cat.filas">
                  <td>{{ f.codigo_asignacion }}</td>
                  <td>{{ f.da }} / {{ f.ue }}</td>
                  <td>{{ f.cod_objeto_gasto }}</td>
                  <td class="descripcion">{{ f.descripcion_objeto }}</td>
                  <td>{{ f.fuente_financiamiento }}/{{ f.organismo_financiador }}</td>
                  <td>{{ f.fecha_requerimiento || '—' }}</td>
                  <td class="num" *ngFor="let m of meses">
                    {{ f['mes_' + m] ? moneda(f['mes_' + m]) : '' }}
                  </td>
                  <td class="num">{{ moneda(f.total_anual) }}</td>
                </tr>
              </ng-container>
              <tr class="fila-total">
                <td [attr.colspan]="columnasPresupuesto.length - 1">
                  TOTAL PROGRAMADO GESTIÓN {{ gestion }}
                </td>
                <td class="num">{{ moneda(totalPresupuesto) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .filtro { display: block; width: min(420px, 40vw); font-size: 0.8125rem; }
    .bloque-presupuesto { margin-top: 2rem; padding-top: 1.25rem; border-top: 2px solid var(--border); }
    .bloque-presupuesto h3 { font-size: 1rem; color: var(--primary); margin: 0; }
    .chip.total { background: var(--pip-green-100); color: var(--pip-green-700); font-size: 0.75rem; font-weight: 700; padding: 0.3rem 0.7rem; border-radius: 999px; }
    .tabla-presupuesto { font-size: 0.75rem; }
    .tabla-presupuesto .num { text-align: right; }
    .tabla-presupuesto .descripcion { max-width: 240px; }
    .fila-categoria td { background: #ECEFF1; border-top: 2px solid var(--border); }
    .fila-categoria .denominacion { color: var(--text-secondary); margin-left: 0.5rem; }
    .fila-categoria .cuenta { color: var(--text-secondary); margin-left: 0.5rem; font-size: 0.6875rem; }
    .fila-total td { background: var(--pip-green-100); font-weight: 700; border-top: 2px solid var(--pip-green-500); }
    .vistas { display: inline-flex; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
    .vistas .btn { border: none; border-radius: 0; background: transparent; }
    .vistas .btn.activa { background: var(--pip-green-500); color: #fff; }
    .leyenda { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: var(--e-2); }
    .leyenda .chip {
      font-size: 0.625rem; font-weight: 700; color: #1F2933;
      padding: 0.2rem 0.55rem; border-radius: 999px; border: 1px solid rgba(0,0,0,.14);
    }
    .leyenda .chip.visible { background: var(--realce); color: var(--text-secondary); }
    /* 34 columnas necesitan ancho propio: sin él el navegador reparte parejo y
       una denominación de 250 caracteres cae en 84px, armando una fila de
       quince líneas. El max-content es explícito, no un arreglo: con layout
       fijo el ancho de la tabla ya es el mayor entre su width y la suma del
       colgroup, así que el width 100% del global no la comprime. */
    .mz {
      table-layout: fixed; width: max-content; min-width: 100%;
    }
    .mz th { border: 1px solid rgba(127,127,127,.35); text-align: center; white-space: normal; }
    .mz th.th-col { font-size: 0.5625rem; line-height: 1.3; padding: 0.35rem 0.3rem; }
    .mz td {
      font-size: 0.6875rem; line-height: 1.35; color: #1F2933;
      border: 1px solid rgba(0,0,0,.07); vertical-align: top;
      white-space: normal; overflow-wrap: anywhere; padding: 0.3rem 0.45rem;
    }
    .mz td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .mz td.propia { font-weight: 600; }
    .nodo { display: flex; align-items: flex-start; gap: 0.3rem; }
    .desplegar {
      border: none; background: rgba(0,0,0,.07); color: #1F2933; cursor: pointer;
      border-radius: 3px; width: 15px; height: 15px; line-height: 1;
      font-size: 0.625rem; flex: 0 0 auto;
    }
    .desplegar:hover { background: rgba(0,0,0,.16); }
    .hoja { color: rgba(0,0,0,.3); flex: 0 0 auto; width: 15px; text-align: center; }
    .texto { flex: 1 1 auto; }
    .cuantos {
      flex: 0 0 auto; font-size: 0.5rem; font-weight: 700;
      background: rgba(0,0,0,.09); border-radius: 999px; padding: 0 0.3rem;
    }
    /* Recuadro de navegación tipo planilla: la cabecera no se mueve y el
       cuerpo se desplaza en los dos ejes. */
    .tabla-caja {
      max-height: calc(100vh - 300px); min-height: 340px;
      /* Explícito: el global declara overflow-y visible junto a overflow-x
         auto, y ahí el visible ya computa como auto. Se deja escrito para que
         el scroll vertical no dependa de esa regla. */
      overflow-x: auto; overflow-y: auto;
      border: 1px solid var(--border); border-radius: var(--radius);
    }
    .mz { --h-banda: 30px; }
    .mz thead tr:first-child th {
      position: sticky; top: 0; z-index: 5;
      height: var(--h-banda); box-sizing: border-box;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .mz thead tr:nth-child(2) th {
      position: sticky; top: var(--h-banda); z-index: 5;
    }
    /* Casilla y acciones quedan ancladas a los costados: con 34 columnas, si
       se desplazan se pierde de vista sobre qué fila se está operando. */
    .th-fija, .td-sel, .td-acc { position: sticky; z-index: 4; }
    .th-sel, .td-sel { left: 0; }
    .th-acc, .td-acc { right: 0; }
    .mz thead .th-fija { z-index: 7; background: var(--surface); color: var(--text-secondary); }
    .th-acc { font-size: 0.5625rem; letter-spacing: .06em; }
    .td-sel, .td-acc { border-left: 1px solid rgba(0,0,0,.12); }
    .td-acc { box-shadow: -2px 0 4px rgba(0,0,0,.06); }
    .td-sel { box-shadow: 2px 0 4px rgba(0,0,0,.06); }
    .td-sel { text-align: center; }
    .mz tbody tr.marcada td { box-shadow: inset 0 0 0 9999px rgba(21,101,192,.09); }
    .acciones { display: flex; align-items: center; gap: 0.15rem; }
    .acc {
      border: none; background: rgba(0,0,0,.06); color: #1F2933; cursor: pointer;
      border-radius: 3px; padding: 0.1rem 0.28rem; font-size: 0.625rem; line-height: 1.4;
    }
    .acc:hover:not(:disabled) { background: rgba(0,0,0,.16); }
    .acc:disabled { opacity: .4; cursor: progress; }
    .acc.peligro:hover:not(:disabled) { background: #B3261E; color: #fff; }
    .sin-acc { color: rgba(0,0,0,.28); }
    .mz td.sin-catalogo { color: #B3261E; font-style: italic; opacity: .8; }
    .mz td.aprox { color: #7A4F01; }
    .estado {
      font-size: 0.5rem; font-weight: 700; padding: 0.05rem 0.28rem;
      border-radius: 999px; margin-right: 0.15rem; white-space: nowrap;
    }
    .e-BORRADOR { background: #E0E0E0; color: #37474F; }
    .e-VALIDADO { background: #BBDEFB; color: #0D47A1; }
    .e-OBSERVADO { background: #FFE0B2; color: #E65100; }
    .e-APROBADO { background: #C8E6C9; color: #1B5E20; }
    .leyenda .chip.marcadas { background: #BBDEFB; color: #0D47A1; }
    .limpiar {
      border: none; background: transparent; color: inherit; cursor: pointer;
      text-decoration: underline; font-size: 0.625rem; padding: 0;
    }
    .msg-box.aviso {
      background: var(--pip-green-100); color: var(--pip-green-700);
      padding: 0.55rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
      font-size: 0.8125rem;
    }
    .btn-excel { background: #1B5E20; color: #fff; border: none; }
    .btn-pdf { background: #B3261E; color: #fff; border: none; }
    .btn-importar { background: #0D47A1; color: #fff; border: none; }
    .import-overlay {
      position: fixed; inset: 0; z-index: 1000; background: rgba(24, 33, 43, .62);
      display: grid; place-items: center; padding: 1rem;
    }
    .import-dialog {
      width: min(900px, 100%); max-height: calc(100vh - 2rem); overflow: auto;
      background: var(--surface); border-radius: var(--radius); padding: 1.25rem;
      box-shadow: 0 20px 60px rgba(0,0,0,.28); color: var(--text-primary);
    }
    .import-dialog > header { display: flex; justify-content: space-between; gap: 1rem; }
    .import-dialog h3, .import-dialog h4 { margin: 0; color: var(--primary); }
    .import-dialog header p { margin: .25rem 0 1rem; color: var(--text-secondary); }
    .import-close { border: 0; background: transparent; font-size: 1.75rem; cursor: pointer; }
    .import-unit { display: block; margin-bottom: 1rem; font-size: .8125rem; font-weight: 700; }
    .import-unit app-combo-box { display: block; width: 100%; margin-top: .3rem; }
    .import-impact { border-left: 4px solid; padding: .7rem .85rem; margin-bottom: 1rem; }
    .import-impact strong { display: block; margin-bottom: .2rem; }
    .import-impact p { margin: 0; font-size: .8125rem; }
    .import-impact.nuevo { background: #E8F5E9; border-color: #2E7D32; color: #1B5E20; }
    .import-impact.reemplazo { background: #FFF3E0; border-color: #EF6C00; color: #8A3B00; }
    .source-tabs { display: flex; gap: 1rem; padding: .65rem; background: var(--realce); border-radius: var(--radius); }
    .source-tabs label { display: flex; align-items: center; gap: .35rem; font-weight: 700; }
    .import-fields { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin: 1rem 0; }
    .import-fields label { font-size: .8125rem; font-weight: 700; }
    .import-fields label span { color: var(--text-secondary); font-weight: 400; }
    .import-fields input { display: block; width: 100%; margin-top: .3rem; }
    .import-summary { display: flex; flex-wrap: wrap; gap: .5rem; margin: .75rem 0; }
    .import-summary span { background: var(--realce); border-radius: 999px; padding: .3rem .65rem; font-size: .75rem; }
    .import-summary .ok { background: #C8E6C9; color: #1B5E20; }
    .import-summary .bad { background: #FFCDD2; color: #B3261E; }
    .import-errors { max-height: 180px; overflow: auto; border-left: 4px solid #B3261E; padding: .7rem; background: #FFF5F5; }
    .import-errors ul { margin: .5rem 0 0; padding-left: 1.2rem; font-size: .75rem; }
    .import-table { max-height: 240px; overflow: auto; margin-top: .8rem; border: 1px solid var(--border); }
    .import-table .num { text-align: right; }
    .replace-confirm { display: flex; gap: .5rem; align-items: flex-start; margin-top: 1rem; font-size: .8125rem; }
    .apply-result { margin-top: .8rem; padding: .7rem; background: #C8E6C9; color: #1B5E20; border-radius: var(--radius); }
    .import-dialog footer { display: flex; justify-content: flex-end; gap: .5rem; margin-top: 1rem; }
    @media (max-width: 700px) { .import-fields { grid-template-columns: 1fr; } }
     .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
       padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
     }
     .poau-empty-state {
       padding: var(--e-4); border: 1px dashed var(--pip-line); border-radius: var(--radius);
       background: var(--pip-card); color: var(--pip-ink-soft); text-align: center;
     }
     .poau-empty-state p { margin: .35rem 0 0; }
  `],
})
export class MatrizPoauComponent implements OnInit, AfterViewInit, OnDestroy {
  modo: 'arbol' | 'matriz' = 'arbol';
  /** Encabezado oficial con el año de la gestión habilitada ya resuelto.
   *  La exportación a Excel/PDF usa SIEMPRE este, nunca la vista de árbol. */
  bloquesMatriz: BloqueMatriz[] = BLOQUES_MATRIZ;
  private bloquesArbol: BloqueMatriz[] = BLOQUES_ARBOL;
  colorNivel = COLOR_NIVEL;
  columnaNivel = COLUMNA_NIVEL;
  etiquetaNivel = ETIQUETA_NIVEL;
  niveles = Object.keys(ETIQUETA_NIVEL);

  filas: any[] = [];

  // --- Programación presupuestaria -------------------------------------------
  /** Grupos por categoría programática, como los arma el servidor. */
  presupuesto: any[] = [];
  totalPresupuesto = 0;
  cargandoPresupuesto = true;
  errorPresupuesto = '';
  readonly meses = MESES;
  /** La última columna es siempre el total: la fila de categoría hace
   *  `colspan` sobre todas las demás y apoya su total en esa. */
  readonly columnasPresupuesto = [
    { etiqueta: 'CÓDIGO', ancho: 150, num: false },
    { etiqueta: 'DA / UE', ancho: 70, num: false },
    { etiqueta: 'PARTIDA', ancho: 64, num: false },
    { etiqueta: 'DESCRIPCIÓN DE LA PARTIDA', ancho: 220, num: false },
    { etiqueta: 'FTE/ORG', ancho: 70, num: false },
    { etiqueta: 'MES REQUERIDO', ancho: 88, num: false },
    ...MESES.map(m => ({ etiqueta: m.slice(0, 3).toUpperCase(), ancho: 68, num: true })),
    { etiqueta: 'TOTAL ANUAL', ancho: 92, num: true },
  ];
  visibles: any[] = [];
  conteo: Record<string, number> = {};
  expandidos = new Set<string>();
  unidades: UnidadCatalogo[] = [];
  opcionesUnidadFiltro: OpcionCombo[] = [];
  opcionesUnidadImport: OpcionCombo[] = [];
  unidadFiltro = TODAS_UNIDADES;
  seleccion = new Set<string>();
  ocupado = '';
  aviso = '';
  unidad = '';
  /** La gestión la pone el candado de SIS-POA, no la pantalla (ADR-007). */
  get gestion(): number | null { return this.gestionActiva.anio(); }
  cargando = true;
  error = '';

  importAbierto = false;
  fuenteImport: 'excel' | 'google_sheets' = 'excel';
  archivoImport: File | null = null;
  googleUrl = '';
  hojaImport = '';
  importando = false;
  aplicando = false;
  importError = '';
  previewImport: PoauImportPreview | null = null;
  confirmarReemplazo = false;

  @ViewChild('tabla') tabla?: ElementRef<HTMLTableElement>;
  @ViewChild('bandas') bandas?: ElementRef<HTMLTableRowElement>;
  @ViewChild('importDialog') importDialog?: ElementRef<HTMLElement>;
  private observador?: ResizeObserver;
  private gestionCatalogo: number | null | undefined;
  private catalogoCargado = false;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef,
              private router: Router,
              private gestionActiva: GestionHabilitadaService) {}

  /**
   * La fila de columnas se pega justo debajo de la de bandas. Ese desnivel no
   * se puede clavar en el CSS: la banda mide distinto según el modo, la fuente
   * y el zoom, y si el número queda corto la segunda fila se monta encima de la
   * primera. Se mide y se publica como variable.
   */
  ngAfterViewInit(): void {
    if (typeof ResizeObserver === 'undefined') { return; }
    this.observador = new ResizeObserver(() => this.medirBanda());
    if (this.bandas) { this.observador.observe(this.bandas.nativeElement); }
    this.medirBanda();
  }

  ngOnDestroy(): void { this.observador?.disconnect(); }

  private medirBanda(): void {
    const fila = this.bandas?.nativeElement;
    const tabla = this.tabla?.nativeElement;
    if (!fila || !tabla) { return; }
    const alto = Math.round(fila.getBoundingClientRect().height);
    if (alto > 0) { tabla.style.setProperty('--h-banda', `${alto}px`); }
  }

  get bloques(): BloqueMatriz[] {
    return this.modo === 'arbol' ? this.bloquesArbol : this.bloquesMatriz;
  }

  cambiarModo(modo: 'arbol' | 'matriz'): void {
    if (this.modo === modo) { return; }
    this.modo = modo;
    for (const f of this.filas) { f.celdas = this.armarCeldas(f); }
    this.cdr.markForCheck();
  }

  ngOnInit(): void {
    // El encabezado del formato oficial lleva el año adentro: se resuelve una
    // vez, con la gestión que el candado ya dejó cargada antes de esta ruta.
    this.bloquesMatriz = conGestion(BLOQUES_MATRIZ, this.gestion);
    this.bloquesArbol = conGestion(BLOQUES_ARBOL, this.gestion);
    this.cargar();
  }

  get totalColumnas(): number {
    return this.bloques.reduce((n, b) => n + b.columnas.length, 0);
  }

  get mostrarEstadoVacio(): boolean {
    return !this.cargando && !this.error && Boolean(this.unidad) && this.filas.length === 0;
  }

  get tienePoauSeleccionado(): boolean {
    return Boolean(this.unidad) && this.filas.length > 0;
  }

  porId = (_: number, f: any) => f.id;

  tinta(fondo: string): string { return tintaSobre(fondo); }

  /**
   * La programación va de la mano de la matriz: mismo candado, misma unidad.
   *
   * Si la de arriba muestra una unidad y la de abajo mostrara todas, los dos
   * totales de la pantalla hablarían de universos distintos.
   */
  cargarPresupuesto(): void {
    this.cargandoPresupuesto = true;
    this.errorPresupuesto = '';
    const filtro = this.unidad ? `?unidad=${encodeURIComponent(this.unidad)}` : '';
    this.http.get<any>(
      `${environment.apiUrl}/articulacion/matriz-poau/presupuesto/${filtro}`)
      .pipe(finalize(() => {
        this.cargandoPresupuesto = false;
        this.cdr.markForCheck();
      }))
      .subscribe({
        next: d => {
          this.presupuesto = d?.categorias ?? [];
          this.totalPresupuesto = Number(d?.total || 0);
          this.cdr.markForCheck();
        },
        error: () => {
          this.presupuesto = [];
          this.totalPresupuesto = 0;
          this.errorPresupuesto =
            'No se pudo cargar la programación presupuestaria.';
          this.cdr.markForCheck();
        },
      });
  }

  moneda(valor: number | null | undefined): string {
    const n = Number(valor || 0);
    return n ? n.toLocaleString('es-BO', { maximumFractionDigits: 0 }) : '0';
  }

  abrirImportacion(): void {
    this.importAbierto = true;
    this.limpiarPreviewImport();
    setTimeout(() => this.importDialog?.nativeElement.focus());
  }

  cambiarUnidadImport(codigo: string): void {
    if (this.unidad === codigo) { return; }
    this.unidad = codigo;
    this.unidadFiltro = codigo || TODAS_UNIDADES;
    this.filas = [];
    this.visibles = [];
    this.limpiarPreviewImport();
    this.cargar();
  }

  cerrarImportacion(): void {
    if (this.importando || this.aplicando) { return; }
    this.importAbierto = false;
  }

  limpiarPreviewImport(): void {
    this.previewImport = null;
    this.confirmarReemplazo = false;
    this.importError = '';
  }

  seleccionarArchivo(event: Event): void {
    this.archivoImport = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.limpiarPreviewImport();
  }

  private importUrl(path: string): string {
    const gestionId = this.gestionActiva.gestion()?.id;
    return `${environment.apiUrlV2}/sis-poa/poau-imports/${path}` +
      (gestionId ? `?gestion_id=${encodeURIComponent(gestionId)}` : '');
  }

  previsualizarImportacion(): void {
    if (!this.unidad) { return; }
    if (this.fuenteImport === 'excel' && !this.archivoImport) {
      this.importError = 'Seleccione un archivo Excel .xlsx.';
      return;
    }
    if (this.fuenteImport === 'google_sheets' && !this.googleUrl.trim()) {
      this.importError = 'Pegue el enlace de Google Sheets.';
      return;
    }
    const data = new FormData();
    data.append('source_type', this.fuenteImport);
    data.append('unidad_codigo', this.unidad);
    if (this.hojaImport.trim()) { data.append('sheet_name', this.hojaImport.trim()); }
    if (this.archivoImport && this.fuenteImport === 'excel') { data.append('file', this.archivoImport); }
    if (this.fuenteImport === 'google_sheets') { data.append('google_url', this.googleUrl.trim()); }
    this.importando = true;
    this.importError = '';
    this.previewImport = null;
    this.confirmarReemplazo = false;
    this.http.post<PoauImportPreview>(this.importUrl('preview/'), data)
      .pipe(finalize(() => { this.importando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: preview => { this.previewImport = preview; this.cdr.markForCheck(); },
        error: response => {
          this.importError = this.importMessage(response, 'No se pudo validar la fuente.');
          this.cdr.markForCheck();
        },
      });
  }

  aplicarImportacion(): void {
    if (!this.previewImport || this.previewImport.estado !== 'VALIDO' || !this.confirmarReemplazo) { return; }
    this.aplicando = true;
    this.importError = '';
    this.http.post<PoauImportPreview>(
      this.importUrl(`${this.previewImport.id}/apply/`), {},
    ).pipe(finalize(() => { this.aplicando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: preview => {
          this.previewImport = preview;
          const result = preview.resultado;
          this.aviso = result
            ? `Importación aplicada: ${result.creados} creados, ${result.reemplazados} reemplazados.`
            : 'Importación aplicada.';
          this.confirmarReemplazo = false;
          this.cargar();
        },
        error: response => {
          this.importError = this.importMessage(response, 'No se pudo aplicar la importación.');
          this.cdr.markForCheck();
        },
      });
  }

  codigoImportado(row: any): string {
    return row[`${row.nivel}_codigo`] || '';
  }

  private importMessage(response: any, fallback: string): string {
    const body = response?.error?.error ?? response?.error;
    const detail = body?.detail ?? body;
    if (Array.isArray(detail)) { return detail.join(' '); }
    if (typeof detail === 'string') { return detail; }
    if (detail && typeof detail === 'object') {
      return Object.values(detail).flat().join(' ') || fallback;
    }
    return fallback;
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    const gestionActual = this.gestion;
    if (this.gestionCatalogo !== gestionActual) {
      this.gestionCatalogo = gestionActual;
      this.catalogoCargado = false;
      this.unidades = [];
      this.opcionesUnidadFiltro = [];
      this.opcionesUnidadImport = [];
      this.unidad = '';
      this.unidadFiltro = TODAS_UNIDADES;
    }
    this.cargarPresupuesto();
    const incluirUnidades = !this.catalogoCargado;
    const parametros = [`incluir_unidades=${incluirUnidades ? '1' : '0'}`];
    if (this.unidad) {
      parametros.push(`unidad=${encodeURIComponent(this.unidad)}`);
    }
    this.http.get<any>(
      `${environment.apiUrl}/articulacion/matriz-poau/?${parametros.join('&')}`)
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: d => {
          this.filas = d.filas ?? [];
          if (incluirUnidades) {
            this.unidades = d.unidades ?? [];
            this.prepararOpcionesUnidad();
            this.catalogoCargado = true;
          }
          const vigentes = new Set(this.filas.map((f: any) => f.id));
          this.seleccion = new Set([...this.seleccion].filter(id => vigentes.has(id)));
          this.conteo = {};
          for (const f of this.filas) {
            this.conteo[f.nivel] = (this.conteo[f.nivel] || 0) + 1;
            f.celdas = this.armarCeldas(f);
          }
          // Con una sola unidad a la vista conviene abrirla; con las 47, no.
          this.expandidos.clear();
          if (this.unidad) { this.expandirTodo(); } else { this.recalcular(); }
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudo cargar la matriz POAU.';
          this.cdr.markForCheck();
        },
      });
  }

  private prepararOpcionesUnidad(): void {
    this.opcionesUnidadImport = this.unidades.map(u => ({
      valor: u.codigo,
      etiqueta: `${u.codigo} — ${u.nombre}`,
      detalle: u.sigla || undefined,
      dato: u,
    }));
    this.opcionesUnidadFiltro = [
      {
        valor: TODAS_UNIDADES,
        etiqueta: `Todas las unidades (${this.unidades.length})`,
      },
      ...this.opcionesUnidadImport,
    ];
  }

  // --- Selección de filas ----------------------------------------------------

  limpiarSeleccion(): void {
    this.seleccion.clear();
    this.cdr.markForCheck();
  }

  alternarSeleccion(fila: any): void {
    if (this.seleccion.has(fila.id)) {
      this.seleccion.delete(fila.id);
    } else {
      this.seleccion.add(fila.id);
    }
    this.cdr.markForCheck();
  }

  /** El encabezado marca y desmarca lo que está a la vista, no lo plegado. */
  alternarTodos(): void {
    if (this.todoSeleccionado()) {
      this.visibles.forEach(f => this.seleccion.delete(f.id));
    } else {
      this.visibles.forEach(f => this.seleccion.add(f.id));
    }
    this.cdr.markForCheck();
  }

  todoSeleccionado(): boolean {
    return this.visibles.length > 0
      && this.visibles.every(f => this.seleccion.has(f.id));
  }

  algoSeleccionado(): boolean {
    return this.seleccion.size > 0 && !this.todoSeleccionado();
  }

  // --- Circuito de revisión --------------------------------------------------

  private RUTA: Record<string, string> = {
    operacion: 'operaciones', actividad: 'actividades', tarea: 'tareas',
  };

  editar(fila: any): void {
    // El wizard trabaja sobre la acción de corto plazo completa, no sobre una
    // tarea suelta: es ahí donde vive la programación que se va a modificar.
    this.router.navigate(['/sis-poa/poaus/editar', fila.accion_id],
                         { queryParams: { foco: fila.objeto_id } });
  }

  revisar(fila: any, accion: 'validar' | 'aprobar' | 'observar'): void {
    let cuerpo: any = {};
    if (accion === 'observar') {
      const comentario = (window.prompt('Motivo de la observación:') || '').trim();
      if (!comentario) { return; }
      cuerpo = { comentario };
    }
    this.ocupado = fila.id;
    this.error = '';
    this.http.post<any>(
      `${environment.apiUrl}/articulacion/${this.RUTA[fila.tipo]}/${fila.objeto_id}/${accion}/`,
      cuerpo)
      .pipe(finalize(() => { this.ocupado = ''; this.cdr.markForCheck(); }))
      .subscribe({
        next: r => {
          fila.estado = r.estado;
          fila.observacion = r.observacion || '';
          this.aviso = `Registro ${r.estado.toLowerCase()}.`;
          this.cdr.markForCheck();
        },
        error: e => {
          this.error = e?.error?.error || 'No se pudo completar la acción.';
          this.cdr.markForCheck();
        },
      });
  }

  eliminar(fila: any): void {
    const que = this.celda(fila, COLUMNA_NIVEL[fila.nivel]).slice(0, 70);
    if (!window.confirm(`¿Eliminar este registro?\n\n${que}`)) { return; }
    this.ocupado = fila.id;
    this.error = '';
    this.http.delete(
      `${environment.apiUrl}/articulacion/${this.RUTA[fila.tipo]}/${fila.objeto_id}/`)
      .pipe(finalize(() => { this.ocupado = ''; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => { this.aviso = 'Registro eliminado.'; this.cargar(); },
        error: e => {
          this.error = e?.error?.error || 'No se pudo eliminar el registro.';
          this.cdr.markForCheck();
        },
      });
  }

  /**
   * Celdas de una fila. Las columnas de la cadena que quedan a la derecha del
   * último dato del nivel se absorben con `colspan`: están vacías por
   * definición y ese ancho es el que le falta a la denominación.
   */
  armarCeldas(fila: any): any[] {
    if (this.modo === 'arbol') {
      return this.bloques.flatMap(b => b.columnas).map(c => ({
        clave: c.clave, colspan: 1, propia: c.clave === 'desglose',
      }));
    }
    const propia = COLUMNA_NIVEL[fila.nivel];
    const datos = DATOS_NIVEL[fila.nivel] ?? [];
    const ultima = datos.length ? datos[datos.length - 1] : FIN_CADENA;
    const celdas: any[] = [];
    const planas = this.bloques.flatMap(b => b.columnas);
    planas.forEach((c, i) => {
      // Absorbida por la celda de `ultima`.
      if (i > ultima && i <= FIN_CADENA) { return; }
      celdas.push({
        clave: c.clave,
        colspan: i === ultima ? FIN_CADENA - ultima + 1 : 1,
        propia: c.clave === propia,
      });
    });
    return celdas;
  }

  /** Una fila se ve si toda su cadena de padres está desplegada. */
  private recalcular(): void {
    const vivos = new Set<string>();
    this.visibles = this.filas.filter(f => {
      const visible = f.padre === null || vivos.has(f.padre);
      if (visible && this.expandidos.has(f.id)) { vivos.add(f.id); }
      return visible;
    });
  }

  alternar(fila: any): void {
    if (this.expandidos.has(fila.id)) {
      this.expandidos.delete(fila.id);
    } else {
      this.expandidos.add(fila.id);
    }
    this.recalcular();
    this.cdr.markForCheck();
  }

  expandirTodo(): void {
    this.expandidos = new Set(this.filas.filter(f => f.hijos).map(f => f.id));
    this.recalcular();
    this.cdr.markForCheck();
  }

  contraerTodo(): void {
    this.expandidos.clear();
    this.recalcular();
    this.cdr.markForCheck();
  }

  filtrar(codigo: string): void {
    this.unidadFiltro = codigo || TODAS_UNIDADES;
    this.unidad = codigo === TODAS_UNIDADES ? '' : codigo;
    this.limpiarPreviewImport();
    this.cargar();
  }

  esNumero(clave: string): boolean { return NUMERICAS.has(clave); }

  /**
   * La denominación sale del catálogo maestro de categorías programáticas.
   * Cuando la categoría no está dada de alta ahí, se dice —no se inventa un
   * texto ni se deja una celda vacía que parezca un olvido de carga.
   */
  etiquetaCategoria(fila: any): string {
    if (fila?.denominacion_categoria) {
      return fila.origen_categoria === 'programa'
        ? `≈ ${fila.denominacion_categoria}`
        : fila.denominacion_categoria;
    }
    return fila?.categoria_programatica ? 'sin catálogo' : '';
  }

  claseCelda(fila: any, clave: string): string {
    if (clave !== 'denominacion_categoria') { return ''; }
    if (!fila?.categoria_programatica) { return ''; }
    if (!fila.denominacion_categoria) { return 'sin-catalogo'; }
    return fila.origen_categoria === 'programa' ? 'aprox' : '';
  }

  tituloCelda(fila: any, clave: string): string {
    const clase = this.claseCelda(fila, clave);
    if (clase === 'sin-catalogo') {
      return `La categoría ${fila.categoria_programatica} no figura en el `
        + 'catálogo maestro de esta gestión.';
    }
    if (clase === 'aprox') {
      return 'Denominación del programa: la actividad exacta todavía no está '
        + 'en el catálogo maestro.';
    }
    return '';
  }

  celda(fila: any, clave: string): string {
    if (clave === 'desglose') { return fila?.[COLUMNA_NIVEL[fila.nivel]] ?? ''; }
    if (clave === 'denominacion_categoria') { return this.etiquetaCategoria(fila); }
    const v = fila?.[clave];
    if (v === null || v === undefined || v === '') { return ''; }
    if (this.esNumero(clave)) { return Number(v).toLocaleString('es-BO'); }
    return String(v);
  }

  // --- Exportación ----------------------------------------------------------

  private escapar(v: string): string {
    return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /** Colores embebidos: Excel los conserva y el PDF los imprime. */
  private tablaHtml(): string {
    const th = (c: string, p: string, f: string) =>
      `bgcolor="${c}" style="background-color:${c};color:${tintaSobre(c)};` +
      `mso-pattern:${c} none;border:1px solid #BFBFBF;padding:${p};font-size:${f};` +
      `text-align:center;-webkit-print-color-adjust:exact;print-color-adjust:exact"`;

    const grupo = this.bloquesMatriz.map(b =>
      `<th colspan="${b.columnas.length}" ${th(b.color, '6px', '10px')}>` +
      `${this.escapar(b.etiqueta)}</th>`).join('');
    const cols = this.bloquesMatriz.flatMap(b => b.columnas.map(c =>
      `<th width="${c.ancho}" ${th(b.color, '5px', '8px')}>` +
      `${this.escapar(c.etiqueta)}</th>`)).join('');

    const cuerpo = this.filasAExportar().map(f => {
      const fondo = this.colorNivel[f.nivel];
      return '<tr>' + this.bloquesMatriz.flatMap(b => b.columnas.map(c => {
        const sangria = c.clave === this.columnaNivel[f.nivel]
          ? `padding-left:${4 + f.orden_nivel * 10}px;font-weight:bold;` : '';
        return `<td bgcolor="${fondo}" style="background-color:${fondo};` +
          `mso-pattern:${fondo} none;border:1px solid #BFBFBF;padding:3px;` +
          `font-size:8px;vertical-align:top;${sangria}` +
          `-webkit-print-color-adjust:exact;print-color-adjust:exact">` +
          `${this.escapar(this.celda(f, c.clave))}</td>`;
      })).join('') + '</tr>';
    }).join('');

    const alcance = this.unidad
      ? `unidad ${this.unidad}` : `todas las unidades (${this.unidades.length})`;
    return `<table style="border-collapse:collapse;font-family:Arial;margin:0 0 10px">
        <tr><td style="font-size:13px;font-weight:bold;color:#1B5E20">
          GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA</td></tr>
        <tr><td style="font-size:12px;font-weight:bold;color:#37474F">
          PROGRAMA OPERATIVO ANUAL POR UNIDAD ${this.gestion}</td></tr>
        <tr><td style="font-size:9px;color:#546E7A;padding:6px 0 0">
          ${alcance} · ${this.filasAExportar().length} fila(s)${
            this.seleccion.size ? ' seleccionada(s)' : ''} ·
          generado el ${new Date().toLocaleString('es-BO')}</td></tr>
      </table>
      <table style="border-collapse:collapse;font-family:Arial">
        <thead><tr>${grupo}</tr><tr>${cols}</tr></thead><tbody>${cuerpo}</tbody></table>`;
  }

  /**
   * Qué se exporta: lo seleccionado, o toda la matriz si no hay selección.
   * A lo seleccionado se le suman sus ancestros —sin la unidad y la acción de
   * corto plazo, una tarea suelta no dice de qué cuelga—, y el orden original
   * se respeta para que el bloque se lea igual que en pantalla.
   */
  filasAExportar(): any[] {
    if (!this.seleccion.size) { return this.filas; }
    const porId = new Map(this.filas.map(f => [f.id, f]));
    const incluidas = new Set<string>();
    for (const id of this.seleccion) {
      let actual = porId.get(id);
      while (actual && !incluidas.has(actual.id)) {
        incluidas.add(actual.id);
        actual = actual.padre ? porId.get(actual.padre) : undefined;
      }
    }
    return this.filas.filter(f => incluidas.has(f.id));
  }

  private nombre(ext: string): string {
    const u = this.unidad ? `-${this.unidad}` : '';
    return `matriz-poau${u}-${new Date().toISOString().slice(0, 10)}.${ext}`;
  }

  exportarExcel(): void {
    const html = `<html xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="utf-8"></head><body>${this.tablaHtml()}</body></html>`;
    const url = URL.createObjectURL(
      new Blob(['﻿', html], { type: 'application/vnd.ms-excel;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url; a.download = this.nombre('xls'); a.click();
    URL.revokeObjectURL(url);
  }

  exportarPdf(): void {
    const v = window.open('', '_blank');
    if (!v) {
      this.error = 'El navegador bloqueó la ventana. Habilite las emergentes.';
      return;
    }
    v.document.write(`<!doctype html><html><head><meta charset="utf-8">
      <title>${this.nombre('pdf')}</title><style>
      @page { size: A3 landscape; margin: 8mm; }
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      body { margin: 0; } thead { display: table-header-group; }
      </style></head><body>${this.tablaHtml()}</body></html>`);
    v.document.close(); v.focus();
    setTimeout(() => v.print(), 300);
  }
}
