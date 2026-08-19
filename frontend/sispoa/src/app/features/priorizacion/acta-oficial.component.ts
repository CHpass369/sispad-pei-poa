import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PriorizacionService } from './priorizacion.service';

@Component({
  selector: 'app-acta-oficial',
  standalone: false,
  template: `
    <div class="lienzo">
      <div class="encabezado-pantalla no-imprimir">
        <div>
          <h2>Acta oficial</h2>
          <p class="sub">Documento generado con la plantilla vigente.</p>
        </div>
        <div class="encabezado-acciones">
          <a class="btn btn-sm btn-secondary" routerLink="/priorizacion/actas">Volver</a>
          <button class="btn btn-sm btn-primary" (click)="imprimir()"
                  [disabled]="!acta">Imprimir / PDF</button>
        </div>
      </div>

      <div class="msg-box error no-imprimir" *ngIf="error">{{ error }}</div>

      <div class="hoja" *ngIf="acta">
        <h1>{{ acta.titulo }}</h1>
        <h2 class="gestion">{{ acta.subtitulo }}</h2>
        <h3 class="distrito">{{ acta.distrito }}</h3>

        <p class="parrafo">{{ acta.encabezado }}</p>

        <table class="detalle">
          <thead>
            <tr>
              <th style="width:36px">N°</th>
              <th>{{ acta.rotulo_descripcion }}</th>
              <th style="width:130px">{{ acta.rotulo_monto }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of acta.proyectos">
              <td class="centro">{{ p.nro }}</td>
              <td>{{ p.descripcion }}</td>
              <td class="num">{{ p.monto | number:'1.0-0' }}</td>
            </tr>
            <tr class="total">
              <td></td>
              <td>{{ acta.rotulo_total }}</td>
              <td class="num">{{ acta.total | number:'1.0-0' }}</td>
            </tr>
          </tbody>
        </table>

        <p class="nota">{{ acta.nota }}</p>
        <p class="parrafo">{{ acta.cierre }}</p>

        <div class="firmas">
          <div class="firma" *ngFor="let f of acta.firmas">
            <div class="linea"></div>
            <div class="nombre">{{ f.nombre }}</div>
            <div class="rol">{{ f.rol }}</div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .hoja {
      background: #fff; color: #1F2933; max-width: 820px; margin: 0 auto;
      padding: 3rem 3.4rem; border: 1px solid var(--border);
      border-radius: var(--radius); font-family: Arial, Helvetica, sans-serif;
    }
    .hoja h1 {
      text-align: center; font-size: 1.05rem; letter-spacing: .02em;
      margin: 0 0 0.2rem;
    }
    .gestion, .distrito {
      text-align: center; font-size: 0.9rem; margin: 0.1rem 0; font-weight: 700;
    }
    .parrafo { margin: 1.6rem 0; text-align: justify; line-height: 1.6; font-size: 0.85rem; }
    .detalle { width: 100%; border-collapse: collapse; margin: 1.2rem 0; }
    .detalle th, .detalle td {
      border: 1px solid #444; padding: 0.4rem 0.5rem; font-size: 0.8rem;
    }
    .detalle th { background: #E8E8E8; text-align: center; }
    .detalle .num { text-align: right; }
    .detalle .centro { text-align: center; }
    .detalle tr.total td { font-weight: 700; background: #F3F3F3; }
    .nota { font-size: 0.75rem; font-style: italic; margin: 1.6rem 0 0; }
    .firmas {
      display: flex; justify-content: space-around; gap: 2rem; margin-top: 4.5rem;
    }
    .firma { text-align: center; flex: 1 1 0; }
    .firma .linea { border-top: 1px solid #333; margin-bottom: 0.3rem; }
    .firma .nombre { font-size: 0.8rem; font-weight: 700; }
    .firma .rol { font-size: 0.7rem; color: #555; }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
    @media print {
      .no-imprimir { display: none !important; }
      .hoja { border: none; padding: 0; max-width: none; }
    }
  `],
})
export class ActaOficialComponent implements OnInit {
  acta: any = null;
  error = '';

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private ruta: ActivatedRoute) {}

  ngOnInit(): void {
    const id = this.ruta.snapshot.paramMap.get('id') || '';
    this.api.actaOficial(id).subscribe({
      next: a => { this.acta = a; this.cdr.markForCheck(); },
      error: e => {
        // El backend explica por qué no se puede emitir: sin fecha, sin
        // proyectos o sin plantilla cargada.
        this.error = e?.error?.error || 'No se pudo generar el acta.';
        this.cdr.markForCheck();
      },
    });
  }

  imprimir(): void { window.print(); }
}
