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
            Documento oficial de priorización POA.
            Formato oficio 21,6 × 33 cm.
          </p>
        </div>

        <div class="encabezado-acciones">
          <a
            class="btn btn-sm btn-secondary"
            routerLink="/priorizacion/actas">
            Volver
          </a>

          <button
            class="btn btn-sm btn-primary"
            (click)="descargar()"
            [disabled]="!acta || bajando">
            {{ bajando ? 'Generando…' : '⬇ Descargar PDF' }}
          </button>
        </div>
      </div>


      <div
        class="msg-box error no-imprimir"
        *ngIf="error">
        {{ error }}
      </div>


      <!-- DOCUMENTOS ADJUNTOS -->
      <div class="documentos no-imprimir" *ngIf="acta">

        <div class="cabecera">
          <div>
            <strong>Documentos del acta</strong>
            <small>
              Se guardan cifrados. Solo se descargan desde acá.
            </small>
          </div>

          <label class="btn btn-sm btn-secondary">
            📎 Adjuntar escaneado

            <input
              type="file"
              hidden
              (change)="adjuntar($event)"
              accept="application/pdf,image/*">
          </label>
        </div>

        <ul>

          <li *ngFor="let d of documentos">

            <span
              class="tipo"
              [class.generado]="d.tipo_documento === 'ACTA_GENERADA'">

              {{
                d.tipo_documento === 'ACTA_GENERADA'
                  ? 'emitido'
                  : 'escaneado'
              }}

            </span>

            <span class="nombre">
              {{ d.nombre }}
            </span>

            <small>
              {{ (d.tamanio_bytes / 1024) | number:'1.0-0' }} kB
            </small>

            <button
              class="btn btn-sm btn-secondary"
              (click)="bajarDocumento(d)">
              Descargar
            </button>

          </li>

          <li
            class="vacio"
            *ngIf="!documentos.length">
            Todavía no hay documentos adjuntos.
          </li>

        </ul>
      </div>


      <!-- ====================================================== -->
      <!-- ACTA OFICIAL                                           -->
      <!-- ====================================================== -->

      <article class="hoja" *ngIf="acta">

        <!-- ENCABEZADO -->
        <header class="cabecera-acta">

          <h1>
            {{ acta.titulo }}
          </h1>

          <h2>
            {{ acta.subtitulo }}
          </h2>

          <h3>
            {{ acta.distrito }}
          </h3>

        </header>


        <!-- PÁRRAFO INTRODUCTORIO -->
        <p class="parrafo introduccion">
          {{ acta.encabezado }}
        </p>


        <!-- PROYECTOS PRIORIZADOS -->
        <table class="detalle">

          <thead>
            <tr>
              <th class="col-numero">N°</th>
              <th>{{ acta.rotulo_descripcion }}</th>
              <th class="col-monto">
                {{ acta.rotulo_monto }}
              </th>
            </tr>
          </thead>

          <tbody>

            <tr *ngFor="let p of acta.proyectos">

              <td class="centro">
                {{ p.nro }}
              </td>

              <td>
                {{ p.descripcion }}
              </td>

              <td class="num">
                {{ formatearMonto(p.monto) }}
              </td>

            </tr>


            <tr class="total">

              <td></td>

              <td>
                {{ acta.rotulo_total }}
              </td>

              <td class="num">
                {{ formatearMonto(acta.total) }}
              </td>

            </tr>

          </tbody>

        </table>


        <section
          class="clausula-pavimento"
          *ngIf="acta.es_pavimento">

          <div class="titulo-pavimento">
            CONDICIÓN PARA LA EJECUCIÓN DE PROYECTO DE PAVIMENTO FLEXIBLE POR ADM. DIRECTA
          </div>

          <p>
            Se aclara que, para la ejecución de proyectos de pavimento
            flexible bajo la modalidad de administración directa, la
            composición del presupuesto priorizado se distribuirá de la
            siguiente manera: <strong>75% destinado a materiales e insumos
            y 25% destinado a la ejecución del proyecto</strong>,
            comprendiendo este último componente el uso de equipo pesado, logística, combustible y personal.
          </p>

        </section>


        <!-- ====================================================== -->
        <!-- PRINCIPIOS                                             -->
        <!-- ====================================================== -->



        <!-- CONDICIONES PRESUPUESTARIAS -->
                <p class="texto-legal" *ngIf="acta.nota">
          {{ acta.nota }}
        </p>



        <!-- DECLARACIÓN -->
                <p class="texto-legal" *ngIf="acta.cierre">
          {{ acta.cierre }}
        </p>



        <!-- FIRMA -->
        <section
          class="firmas"
          *ngIf="firmasVisibles().length">

          <div
            class="firma"
            *ngFor="let f of firmasVisibles()">

            <div class="linea"></div>

            <div class="nombre">
              {{ f.nombre }}
            </div>

            <div class="rol">
              {{ f.rol }}
            </div>

            <div class="dato-firma">
              C.I.: ____________________
            </div>

            <div class="dato-firma">
              Fecha: __________________
            </div>

          </div>

        </section>


        <!-- VERIFICACIÓN -->
        <section
          class="huella"
          *ngIf="acta.huella">

          <span class="marca">
            QR
          </span>

          <div class="huella-texto">

            <span>
              Código de verificación:
            </span>

            <code>
              {{ acta.huella }}
            </code>

          </div>

        </section>


        <footer>
          Gobierno Autónomo Municipal de Sacaba ·
          POA {{ acta.gestion }}
        </footer>

      </article>

    </div>
  `,


  styles: [`

    /* ========================================================== */
    /* HOJA                                                       */
    /* ========================================================== */

    .hoja {
      position: relative;
      box-sizing: border-box;

      width: 216mm;
      min-height: 330mm;

      /*
       * IMPORTANTE:
       * NO se fija height.
       *
       * Si el contenido crece, la hoja también crece en la
       * vista previa y el PDF realizará la paginación.
       */
      height: auto;

      max-width: 100%;

      margin: 0 auto;

      /*
       * 4 cm superior
       * 2,5 cm laterales
       * 2 cm inferior
       */
      padding: 40mm 25mm 20mm;

      background: #fff;
      color: #1f2933;

      border: 1px solid var(--border);
      border-radius: var(--radius);

      box-shadow: var(--shadow);

      font-family: Arial, Helvetica, sans-serif;
    }


    /* ========================================================== */
    /* CABECERA                                                   */
    /* ========================================================== */

    .cabecera-acta {
      text-align: center;
      margin: 0 0 4mm;
    }

    .cabecera-acta h1 {
      margin: 0 0 1mm;
      font-size: 1rem;
      line-height: 1.15;
      font-weight: 700;
    }

    .cabecera-acta h2 {
      margin: 0;
      font-size: 0.90rem;
      line-height: 1.15;
      font-weight: 700;
    }

    .cabecera-acta h3 {
      margin: 1mm 0 0;
      font-size: 0.86rem;
      line-height: 1.15;
      font-weight: 700;
    }


    /* ========================================================== */
    /* TEXTO                                                      */
    /* ========================================================== */

    .parrafo {
      text-align: justify;
      font-size: 0.77rem;
      line-height: 1.35;
    }

    .introduccion {
      margin: 4mm 0 5mm;
    }


    /* ========================================================== */
    /* TABLA DE PROYECTOS                                        */
    /* ========================================================== */

    .detalle {
      width: 100%;

      margin: 0 0 5mm;

      border-collapse: collapse;

      table-layout: fixed;
    }

    .detalle th,
    .detalle td {
      border: 1px solid #444;

      padding: 2.2mm 2.5mm;

      font-size: 0.72rem;
      line-height: 1.25;

      vertical-align: middle;
    }

    .detalle th {
      background: #e8e8e8;

      text-align: center;

      font-weight: 700;
    }

    .col-numero {
      width: 10mm;
    }

    .col-monto {
      width: 34mm;
    }

    .detalle .centro {
      text-align: center;
    }

    .detalle .num {
      text-align: right;

      white-space: nowrap;
    }

    .detalle .total td {
      background: #f3f3f3;

      font-weight: 700;
    }


    /* ========================================================== */
    /* TITULOS DE SECCION                                        */
    /* ========================================================== */

    .clausula-pavimento {
      margin: 4mm 0;
      padding: 2.5mm 3.5mm;
      border: 1px solid #555;
      font-size: 0.66rem;
      line-height: 1.30;
      text-align: justify;
      break-inside: avoid;
      page-break-inside: avoid;
    }

    .titulo-pavimento {
      margin-bottom: 1.5mm;
      text-align: center;
      font-size: 0.68rem;
      line-height: 1.15;
      font-weight: 700;
    }

    .clausula-pavimento p {
      margin: 0;
    }

    .titulo-seccion {
      margin-bottom: 2mm;

      text-align: center;

      font-size: 0.70rem;

      line-height: 1.1;

      font-weight: 700;

      letter-spacing: 0.01em;
    }


    /* ========================================================== */
    /* PRINCIPIOS                                                 */
    /* ========================================================== */

    .principios {
      margin: 5mm 0;
    }

    .principios-grid {
      display: grid;

      grid-template-columns:
        minmax(0, 1fr)
        minmax(0, 1fr);

      /*
       * Un solo recuadro.
       */
      border: 1px solid #555;

      padding: 1.5mm 2mm;

      column-gap: 0;
    }

    .principio {
      box-sizing: border-box;

      padding: 1.3mm 2mm;

      font-size: 0.60rem;

      line-height: 1.22;

      text-align: justify;

      break-inside: avoid;
    }

    /*
     * Línea central.
     * Los principios se muestran:
     *
     * 1 | 2
     * 3 | 4
     * 5 | 6
     * 7 | 8
     */
    .principio:nth-child(odd) {
      border-right: 1px solid #bbb;
    }


    /* ========================================================== */
    /* CONDICIONES / DECLARACION                                  */
    /* ========================================================== */

    .bloque-texto {
      margin-top: 5mm;
    }

    .bloque-texto p {
      margin: 0;

      text-align: justify;

      font-size: 0.68rem;

      line-height: 1.30;
    }


    /* ========================================================== */
    /* FIRMAS                                                     */
    /* ========================================================== */

    .texto-legal {
      margin: 5mm 0 0;
      font-size: 0.68rem;
      line-height: 1.30;
      text-align: justify;
    }

    .firmas {
      display: flex;

      justify-content: center;

      margin-top: 16mm;

      page-break-inside: avoid;
    }

    .firma {
      width: 70mm;

      text-align: center;
    }

    .firma .linea {
      width: 48mm;

      margin: 0 auto 2mm;

      border-top: 1px solid #333;
    }

    .firma .nombre {
      font-size: 0.72rem;

      font-weight: 700;
    }

    .firma .rol {
      margin-top: 1mm;

      font-size: 0.66rem;
    }

    .dato-firma {
      margin-top: 2.5mm;

      font-size: 0.64rem;
    }


    /* ========================================================== */
    /* QR / HUELLA                                                */
    /* ========================================================== */

    .huella {
      position: absolute;

      top: 10mm;
      right: 25mm;

      width: 20mm;
      height: 20mm;

      margin: 0;

      display: flex;
      align-items: center;
      justify-content: center;

      gap: 1mm;

      font-size: 0.45rem;
      color: #555;

      z-index: 2;
    }

    .huella .marca {
      width: 20mm;
      height: 20mm;

      flex: 0 0 auto;

      display: grid;
      place-items: center;

      border: 1px solid #555;

      font-size: 0.50rem;
      font-weight: 700;
    }

    .huella-texto {
      max-width: 125mm;
    }

    .huella code {
      display: block;

      word-break: break-all;

      font-size: 0.50rem;
    }


    footer {
      margin-top: 2mm;

      text-align: center;

      font-size: 0.53rem;

      color: #555;
    }


    /* ========================================================== */
    /* DOCUMENTOS                                                 */
    /* ========================================================== */

    .msg-box.error {
      padding: 0.7rem 0.9rem;

      margin-bottom: var(--e-2);

      border-radius: var(--radius);

      background: var(--error-fondo);

      color: var(--error-tinta);
    }

    .documentos {
      max-width: 820px;

      margin: 0 auto var(--e-2);

      padding: 0.8rem 1rem;

      border: 1px solid var(--border);

      border-radius: var(--radius);

      background: var(--surface);
    }

    .documentos .cabecera {
      display: flex;

      justify-content: space-between;

      align-items: center;

      gap: 1rem;
    }

    .documentos small {
      display: block;

      font-size: 0.6875rem;

      color: var(--text-secondary);
    }

    .documentos ul {
      margin: 0.6rem 0 0;

      padding: 0;

      list-style: none;
    }

    .documentos li {
      display: flex;

      align-items: center;

      gap: 0.6rem;

      padding: 0.35rem 0;

      border-top: 1px solid var(--border);

      font-size: 0.8125rem;
    }

    .documentos li.vacio {
      color: var(--text-secondary);
    }

    .documentos .nombre {
      flex: 1 1 auto;
    }

    .tipo {
      padding: 0.1rem 0.4rem;

      border-radius: 999px;

      background: #e0e0e0;

      color: #37474f;

      font-size: 0.5625rem;

      font-weight: 700;

      text-transform: uppercase;
    }

    .tipo.generado {
      background: #c8e6c9;

      color: #1b5e20;
    }


    /* ========================================================== */
    /* IMPRESION                                                  */
    /* ========================================================== */

    @page {
      size: 216mm 330mm;

      margin:
        40mm
        25mm
        20mm;
    }

    @media print {

      .no-imprimir {
        display: none !important;
      }

      .lienzo {
        padding: 0;

        margin: 0;
      }

      .hoja {
        width: auto;

        min-height: 0;

        margin: 0;

        padding: 0;

        border: none;

        border-radius: 0;

        box-shadow: none;
      }

      .detalle {
        page-break-inside: auto;
      }

      .detalle tr {
        page-break-inside: avoid;
      }

      .detalle thead {
        display: table-header-group;
      }

      .principio {
        break-inside: avoid;
      }

      .firmas {
        page-break-inside: avoid;
      }

    }

  `]
})


export class ActaOficialComponent implements OnInit {

  acta: any = null;

  documentos: any[] = [];

  ultimoFallo: Promise<void> = Promise.resolve();

  error = '';

  bajando = false;


  constructor(
    private api: PriorizacionService,
    private cdr: ChangeDetectorRef,
    private ruta: ActivatedRoute
  ) {}


  /**
   * Convierte:
   *
   * 1234567.8
   *
   * en:
   *
   * 1.234.567,80
   */
  formatearMonto(
    valor: number | string | null | undefined
  ): string {

    const numero = Number(valor ?? 0);

    return new Intl.NumberFormat(
      'es-BO',
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }
    ).format(
      Number.isFinite(numero)
        ? numero
        : 0
    );
  }


  /**
   * Permite recibir los principios:
   *
   * - uno por línea;
   * - o todos en una única línea.
   *
   * Ej:
   *
   * 1. Necesidad... 2. Equidad... 3. Integralidad...
   */
  principiosItems(
    texto: string | null | undefined
  ): string[] {

    const limpio = String(texto ?? '')
      .replace(/\r/g, ' ')
      .replace(/\n/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    if (!limpio) {
      return [];
    }

    /*
     * Divide tanto:
     *
     * 1. texto
     * 2. texto
     *
     * como:
     *
     * 1. texto 2. texto 3. texto...
     */
    const partes = limpio
      .split(/(?=\b\d+\.\s+)/)
      .map(item => item.trim())
      .filter(item => /^\d+\.\s+/.test(item));

    return partes.length ? partes : [limpio];
  }


  /**
   * Seguridad adicional:
   * Responsable del registro nunca se imprime.
   */
  firmasVisibles(): any[] {

    return (this.acta?.firmas ?? []).filter(
      (firma: any) =>
        !String(firma?.rol ?? '')
          .toLowerCase()
          .includes('responsable')
    );
  }


  ngOnInit(): void {

    const id =
      this.ruta.snapshot.paramMap.get('id') || '';

    this.api.actaOficial(id).subscribe({

      next: a => {

        this.acta = a;

        this.cargarDocumentos();

        this.cdr.markForCheck();
      },

      error: e => {

        this.error =
          e?.error?.error ||
          'No se pudo generar el acta.';

        this.cdr.markForCheck();
      }

    });
  }


  private cargarDocumentos(): void {

    const id =
      this.ruta.snapshot.paramMap.get('id') || '';

    this.api.documentosDelActa(id).subscribe({

      next: d => {

        this.documentos = d ?? [];

        this.cdr.markForCheck();
      },

      error: () => {

        this.documentos = [];
      }

    });
  }


  adjuntar(evento: Event): void {

    const entrada =
      evento.target as HTMLInputElement;

    const archivo =
      entrada.files?.[0];

    if (!archivo) {
      return;
    }

    const id =
      this.ruta.snapshot.paramMap.get('id') || '';

    this.error = '';

    this.api.adjuntar(
      id,
      archivo
    ).subscribe({

      next: () => {

        entrada.value = '';

        this.cargarDocumentos();
      },

      error: e => {

        this.error =
          e?.error?.error ||
          'No se pudo adjuntar el documento.';

        this.cdr.markForCheck();
      }

    });
  }


  bajarDocumento(
    documento: any
  ): void {

    this.api
      .descargarDocumento(documento.id)
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(blob);

          const a =
            document.createElement('a');

          a.href = url;

          a.download =
            documento.nombre;

          a.click();

          URL.revokeObjectURL(url);
        },

        error: e => {

          this.ultimoFallo =
            this.explicarFalloDeBlob(
              e,
              'No se pudo descargar el documento.'
            );
        }

      });
  }


  private explicarFalloDeBlob(
    e: any,
    porDefecto: string
  ): Promise<void> {

    const cuerpo =
      e?.error;

    const mostrar =
      (mensaje: string) => {

        this.error =
          mensaje ||
          porDefecto;

        this.cdr.markForCheck();
      };


    if (
      cuerpo instanceof Blob
    ) {

      return cuerpo
        .text()
        .then(texto => {

          try {

            mostrar(
              JSON.parse(texto)?.error
            );

          } catch {

            mostrar('');
          }

        })
        .catch(
          () => mostrar('')
        );
    }


    mostrar(
      cuerpo?.error
    );

    return Promise.resolve();
  }


  descargar(): void {

    const id =
      this.ruta.snapshot.paramMap.get('id') || '';

    this.bajando = true;


    this.api
      .actaPdf(id)
      .pipe(
        finalize(() => {

          this.bajando = false;

          this.cdr.markForCheck();
        })
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(blob);

          const a =
            document.createElement('a');

          a.href = url;

          a.download =
            `acta-${this.acta?.otb || 'priorizacion'}.pdf`
              .replace(/\s+/g, '-');

          a.click();

          URL.revokeObjectURL(url);
        },

        error: () => {

          this.error =
            'No se pudo generar el PDF.';

          this.cdr.markForCheck();
        }

      });
  }

}
