import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { PriorizacionService } from './priorizacion.service';

@Component({
  selector: 'app-acta-oficial',
  standalone: false,
  template: `
    <div class="lienzo">
      <div class="encabezado-pantalla no-imprimir">
        <div>
          <h2>Acta oficial</h2>
          <p class="sub">
            Documento generado con la plantilla vigente. Se imprime en tamaño
            oficio (21,6 × 33 cm).
          </p>
        </div>
        <div class="encabezado-acciones">
          <a class="btn btn-sm btn-secondary" routerLink="/priorizacion/actas">Volver</a>
          <button class="btn btn-sm btn-primary" (click)="descargar()"
                  [disabled]="!acta || bajando">
            {{ bajando ? 'Generando…' : '⬇ Descargar PDF (oficio)' }}
          </button>
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

        <p class="parrafo" *ngIf="acta.aclaracion">{{ acta.aclaracion }}</p>
        <p class="nota">{{ acta.nota }}</p>
        <p class="parrafo">{{ acta.cierre }}</p>

        <div class="firmas">
          <div class="firma" *ngFor="let f of acta.firmas">
            <div class="linea"></div>
            <div class="nombre">{{ f.nombre }}</div>
            <div class="rol">{{ f.rol }}</div>
          </div>
        </div>

        <div class="huella" *ngIf="acta.huella">
          <span class="marca">QR</span>
          <div>
            <strong>Verificación del contenido · SHA-256</strong>
            <code>{{ acta.huella }}</code>
            <em>El código QR con esta huella se imprime en el PDF.</em>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    /* La vista previa usa la hoja real: 216 x 330 mm con sus márgenes, para
       que lo que se ve en pantalla sea lo que sale impreso. */
    .hoja {
      background: #fff; color: #1F2933; margin: 0 auto;
      width: 216mm; min-height: 330mm; max-width: 100%;
      padding: 24mm 25mm 20mm; border: 1px solid var(--border);
      border-radius: var(--radius); font-family: Arial, Helvetica, sans-serif;
      box-shadow: var(--shadow);
    }
    .hoja h1 {
      text-align: center; font-size: 1.3rem; letter-spacing: .02em;
      margin: 0 0 0.2rem;
    }
    .gestion, .distrito {
      text-align: center; font-size: 1.1rem; margin: 0.15rem 0; font-weight: 700;
    }
    .parrafo { margin: 1.7rem 0; text-align: justify; line-height: 1.65; font-size: 1.02rem; }
    .detalle { width: 100%; border-collapse: collapse; margin: 1.2rem 0; }
    .detalle th, .detalle td {
      border: 1px solid #444; padding: 0.45rem 0.55rem; font-size: 0.94rem;
    }
    .detalle th { background: #E8E8E8; text-align: center; }
    .detalle .num { text-align: right; }
    .detalle .centro { text-align: center; }
    .detalle tr.total td { font-weight: 700; background: #F3F3F3; }
    .nota { font-size: 0.88rem; font-style: italic; margin: 1.6rem 0 0; text-align: justify; }
    .firmas {
      display: flex; justify-content: space-around; gap: 2rem; margin-top: 4.5rem;
    }
    .firma { text-align: center; flex: 1 1 0; }
    .firma .linea { border-top: 1px solid #333; margin-bottom: 0.3rem; }
    .firma .nombre { font-size: 0.94rem; font-weight: 700; }
    .firma .rol { font-size: 0.84rem; color: #555; }
    .huella {
      display: flex; gap: 0.7rem; align-items: center; margin-top: 3rem;
      padding-top: 0.9rem; border-top: 1px dashed #bbb;
      font-size: 0.7rem; color: #555;
    }
    .huella .marca {
      flex: 0 0 auto; width: 46px; height: 46px; display: grid;
      place-items: center; border: 2px solid #555; border-radius: 4px;
      font-weight: 700; font-size: 0.7rem;
    }
    .huella code { display: block; word-break: break-all; font-size: 0.65rem; }
    .huella em { display: block; margin-top: 0.15rem; }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
    /* Oficio: 21,6 x 33 cm. No es el Legal norteamericano (21,6 x 35,6), así
       que la medida va explícita y no como palabra clave. */
    @page { size: 216mm 330mm; margin: 20mm 18mm; }

    @media print {
      .no-imprimir { display: none !important; }
      .lienzo { padding: 0; margin: 0; }
      .hoja {
        border: none; border-radius: 0; box-shadow: none;
        padding: 0; margin: 0; width: auto; min-height: 0; max-width: none;
      }
      /* La tabla no se puede partir a la mitad de una fila. */
      .detalle { page-break-inside: auto; }
      .detalle tr { page-break-inside: avoid; }
      .detalle thead { display: table-header-group; }
      .firmas { page-break-inside: avoid; }
    }
  `],
})
export class ActaOficialComponent implements OnInit {
  acta: any = null;
  error = '';
  bajando = false;

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

  /**
   * El PDF lo genera el servidor. Antes esto llamaba a `window.print()`, y el
   * diálogo nativo imprime con el tamaño de papel que el usuario tenga
   * configurado —carta o A4—, escalando el acta.
   */
  descargar(): void {
    const id = this.ruta.snapshot.paramMap.get('id') || '';
    this.bajando = true;
    this.api.actaPdf(id)
      .pipe(finalize(() => { this.bajando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: blob => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `acta-${this.acta?.otb || 'priorizacion'}.pdf`
            .replace(/\s+/g, '-');
          a.click();
          URL.revokeObjectURL(url);
        },
        error: () => {
          this.error = 'No se pudo generar el PDF.';
          this.cdr.markForCheck();
        },
      });
  }
}
