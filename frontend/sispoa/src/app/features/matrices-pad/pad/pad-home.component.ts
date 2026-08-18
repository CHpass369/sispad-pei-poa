import { Component } from '@angular/core';

/**
 * Portada del módulo PAD: separa el registro nuevo de la consulta de las
 * matrices ya generadas.
 */
@Component({
  selector: 'app-pad-home',
  standalone: false,
  template: `
    <div class="pad-home">
      <div class="home-header">
        <h1>MATRICES PAD 2026-2030</h1>
        <p>Plan Autónomo de Desarrollo — Gobierno Autónomo Municipal de Sacaba</p>
      </div>

      <div class="opciones">
        <a routerLink="/matrices-pad/nuevo" class="opcion">
          <span class="icono">＋</span>
          <span class="titulo">Registro nuevo</span>
          <span class="detalle">
            Abre el asistente para formular una matriz PAD desde cero: planificación
            nacional, acuerdos, sector, lineamiento y resultados territoriales.
          </span>
          <span class="accion">Iniciar asistente →</span>
        </a>

        <a routerLink="/matrices-pad/registros" class="opcion">
          <span class="icono">▤</span>
          <span class="titulo">Matrices PAD</span>
          <span class="detalle">
            Consulta las matrices formuladas y los registros que se van generando.
            Desde ahí se puede editar cualquier registro.
          </span>
          <span class="accion">Ver registros →</span>
        </a>
      </div>
    </div>
  `,
  styles: [`
    .pad-home { max-width: 900px; margin: 0 auto; }
    .home-header h1 { font-size: 1.35rem; color: var(--primary); }
    .home-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1.75rem; }

    .opciones { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
    .opcion {
      display: flex; flex-direction: column; gap: 0.5rem;
      padding: 1.5rem; border: 2px solid var(--border); border-radius: 10px;
      text-decoration: none; color: inherit; background: var(--surface, #fff);
      transition: border-color .15s ease, transform .15s ease;
    }
    .opcion:hover { border-color: var(--primary); transform: translateY(-2px); }
    .icono { font-size: 1.75rem; color: var(--primary); line-height: 1; }
    .titulo { font-size: 1rem; font-weight: 700; }
    .detalle { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.45; }
    .accion { margin-top: 0.5rem; font-size: 0.75rem; font-weight: 700; color: var(--primary); }

    @media (max-width: 768px) { .opciones { grid-template-columns: 1fr; } }
  `],
})
export class PadHomeComponent {}
