import { Component, Input } from '@angular/core';

/** Observación de contraste contra la guía o el reglamento del instrumento. */
export interface HallazgoMetodologico {
  severidad: 'error' | 'aviso';
  seccion: string;
  mensaje: string;
}

/**
 * Panel vertical de control metodológico.
 *
 * Acompaña a los asistentes de PAD, PEI, POA, POAU y POAU Recursos: se
 * mantiene visible mientras se llena el formulario y va contrastando el
 * borrador contra la guía correspondiente, sin esperar al paso de registro.
 */
@Component({
  selector: 'app-control-metodologico',
  standalone: false,
  template: `
    <aside class="control-panel" [class.colapsado]="colapsado">
      <div class="panel-head" (click)="colapsado = !colapsado">
        <span class="titulo">
          <span class="icono">◈</span>
          <span class="texto-titulo" *ngIf="!colapsado">Control metodológico</span>
        </span>
        <span class="contadores" *ngIf="!colapsado">
          <span class="chip chip-error" *ngIf="errores">{{ errores }}</span>
          <span class="chip chip-aviso" *ngIf="avisos">{{ avisos }}</span>
          <span class="chip chip-ok" *ngIf="!hallazgos.length">✓</span>
        </span>
        <span class="toggle">{{ colapsado ? '‹' : '›' }}</span>
      </div>

      <div class="panel-cuerpo" *ngIf="!colapsado">
        <p class="fuente" *ngIf="fuente">{{ fuente }}</p>

        <div class="estado-ok" *ngIf="!hallazgos.length">
          Sin observaciones. El borrador cumple las reglas verificables.
        </div>

        <div class="bloque" *ngIf="errores">
          <h4 class="bloque-titulo error">
            {{ errores }} {{ errores === 1 ? 'punto bloquea' : 'puntos bloquean' }} el registro
          </h4>
          <ul>
            <li *ngFor="let h of soloErrores" class="error">
              <span class="seccion">{{ h.seccion }}</span>
              <span class="mensaje">{{ h.mensaje }}</span>
            </li>
          </ul>
        </div>

        <div class="bloque" *ngIf="avisos">
          <h4 class="bloque-titulo aviso">
            {{ avisos }} {{ avisos === 1 ? 'advertencia' : 'advertencias' }}
          </h4>
          <ul>
            <li *ngFor="let h of soloAvisos" class="aviso">
              <span class="seccion">{{ h.seccion }}</span>
              <span class="mensaje">{{ h.mensaje }}</span>
            </li>
          </ul>
        </div>

        <p class="nota-pie" *ngIf="avisos && !errores">
          Las advertencias no impiden registrar: son criterios de la guía que conviene revisar.
        </p>
      </div>
    </aside>
  `,
  styles: [`
    .control-panel {
      position: sticky;
      top: 1rem;
      align-self: start;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface, #fff);
      overflow: hidden;
      max-height: calc(100vh - 2rem);
      display: flex;
      flex-direction: column;
    }
    .control-panel.colapsado { width: 44px; }

    .panel-head {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.6rem 0.7rem;
      background: var(--primary); color: #fff;
      cursor: pointer; user-select: none;
    }
    .titulo { display: flex; align-items: center; gap: 0.4rem; flex: 1; min-width: 0; }
    .icono { font-size: 0.875rem; }
    .texto-titulo { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; white-space: nowrap; }
    .contadores { display: flex; gap: 0.25rem; }
    .chip { border-radius: 10px; padding: 0 0.4rem; font-size: 0.625rem; font-weight: 800; }
    .chip-error { background: #FFEBEE; color: #B3261E; }
    .chip-aviso { background: #FFF8E1; color: #8A6100; }
    .chip-ok { background: #E8F5E9; color: #1B5E20; }
    .toggle { font-size: 0.875rem; opacity: 0.85; }

    .panel-cuerpo { padding: 0.7rem; overflow-y: auto; }
    .fuente { font-size: 0.625rem; color: var(--text-secondary); margin: 0 0 0.6rem; }

    .estado-ok {
      background: #E8F5E9; color: var(--success);
      padding: 0.6rem; border-radius: 6px; font-size: 0.75rem;
    }

    .bloque { margin-bottom: 0.9rem; }
    .bloque-titulo { font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.03em; margin: 0 0 0.4rem; }
    .bloque-titulo.error { color: var(--warn); }
    .bloque-titulo.aviso { color: #8A6100; }

    ul { list-style: none; padding: 0; margin: 0; }
    li {
      display: flex; flex-direction: column; gap: 0.15rem;
      padding: 0.45rem 0.55rem; border-radius: 6px; margin-bottom: 0.35rem;
      border-left: 3px solid transparent;
    }
    li.error { background: #FFEBEE; border-left-color: var(--warn); }
    li.aviso { background: #FFF8E1; border-left-color: #C99A2E; }
    .seccion { font-size: 0.5625rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; opacity: 0.75; }
    .mensaje { font-size: 0.6875rem; line-height: 1.35; }
    li.error .mensaje { color: #7A1C16; }
    li.aviso .mensaje { color: #6B4B00; }

    .nota-pie { font-size: 0.625rem; color: var(--text-secondary); margin: 0.5rem 0 0; }

    @media (max-width: 1100px) {
      .control-panel { position: static; max-height: none; width: auto; }
      .control-panel.colapsado { width: auto; }
    }
  `],
})
export class ControlMetodologicoComponent {
  @Input() hallazgos: HallazgoMetodologico[] = [];
  /** Norma contra la que se contrasta, para que el panel diga de dónde sale. */
  @Input() fuente = '';

  colapsado = false;

  get soloErrores(): HallazgoMetodologico[] {
    return this.hallazgos.filter(h => h.severidad === 'error');
  }

  get soloAvisos(): HallazgoMetodologico[] {
    return this.hallazgos.filter(h => h.severidad === 'aviso');
  }

  get errores(): number { return this.soloErrores.length; }
  get avisos(): number { return this.soloAvisos.length; }
}
