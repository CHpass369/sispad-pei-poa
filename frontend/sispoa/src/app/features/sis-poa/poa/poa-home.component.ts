import { Component } from '@angular/core';

/** Portada del módulo POA: separa el registro nuevo de la consulta. */
@Component({
  selector: 'app-poa-home',
  standalone: false,
  template: `
    <div class="poa-home">
      <div class="home-header">
        <h1>PROGRAMA OPERATIVO ANUAL</h1>
        <p>Formulación POA — Gobierno Autónomo Municipal de Sacaba</p>
      </div>

      <div class="opciones">
        <a routerLink="/sis-poa/poas/nuevo" class="opcion">
          <span class="icono">＋</span>
          <span class="titulo">Registro nuevo</span>
          <span class="detalle">
            Abre el asistente para formular el POA: articulación con el PEI, área
            responsable, acciones de corto plazo y su cadena de operaciones.
          </span>
          <span class="accion">Iniciar asistente →</span>
        </a>

        <a routerLink="/sis-poa/poas/registros" class="opcion">
          <span class="icono">▤</span>
          <span class="titulo">Matrices POA</span>
          <span class="detalle">
            Consulta las matrices formuladas y los registros que se van generando.
            Desde ahí se puede editar, validar, observar o aprobar cada registro.
          </span>
          <span class="accion">Ver registros →</span>
        </a>
      </div>
    </div>
  `,
  styles: [`
    .poa-home { max-width: 900px; margin: 0 auto; }
    .home-header h1 { font-size: 1.35rem; color: var(--primary); }
    .home-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1.75rem; }
    .opciones { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
    .opcion {
      display: flex; flex-direction: column; gap: 0.5rem; padding: 1.5rem;
      border: 2px solid var(--border); border-radius: 10px; text-decoration: none;
      color: inherit; background: var(--surface, #fff);
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
export class PoaHomeComponent {}
