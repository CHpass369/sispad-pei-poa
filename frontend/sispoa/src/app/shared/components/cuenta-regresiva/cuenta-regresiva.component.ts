import {
  ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy, OnInit,
} from '@angular/core';

/**
 * Cuenta regresiva hasta el cierre de registros de un instrumento.
 *
 * Es EXCLUSIVAMENTE visual: no bloquea el formulario, no deshabilita botones,
 * no cierra sesión y no consulta al backend. Quien decide si un registro entra
 * es el candado de gestión, no este reloj.
 */
@Component({
  selector: 'app-cuenta-regresiva',
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="registro-countdown" [ngClass]="'countdown--' + estado">
      <div class="countdown-icono">&#8987;</div>
      <div class="countdown-contenido">
        <div class="countdown-titulo">{{ titulo }}</div>
        <div class="countdown-tiempo" *ngIf="!finalizado">{{ restante }}</div>
        <div class="countdown-tiempo countdown-finalizado" *ngIf="finalizado">
          PLAZO FINALIZADO
        </div>
        <div class="countdown-subtitulo">{{ subtitulo }}</div>
      </div>
    </div>
  `,
  styles: [`
.registro-countdown {
        flex: 0 0 auto;
        min-width: 270px;
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 0.85rem;
        padding:
          0.8rem
          1.1rem;
        box-sizing: border-box;
        color: #fff;
        border:
          2px solid
          rgba(255,255,255,.90);
        border-radius: 13px;
        box-shadow:
          0 7px 20px rgba(0,0,0,.20),
          0 0 0 1px rgba(0,0,0,.05);
        transition:
          background .25s ease,
          box-shadow .25s ease,
          transform .25s ease;
      }
      .countdown-icono {
        flex: 0 0 auto;
        font-size: 2.1rem;
        line-height: 1;
        filter:
          drop-shadow(
            0 2px 2px
            rgba(0,0,0,.22)
          );
      }
      .countdown-contenido {
        min-width: 0;
        display: flex;
        flex-direction: column;
      }
      .countdown-titulo {
        font-size: .69rem;
        font-weight: 900;
        line-height: 1.1;
        letter-spacing: .08em;
        color: #fff;
      }
      .countdown-tiempo {
        margin-top: .16rem;
        font-size: 1.8rem;
        font-weight: 900;
        line-height: 1;
        letter-spacing: .045em;
        font-variant-numeric:
          tabular-nums;
        color: #fff;
        text-shadow:
          0 2px 3px
          rgba(0,0,0,.20);
      }
      .countdown-finalizado {
        font-size: 1rem;
        line-height: 1.15;
      }
      .countdown-subtitulo {
        margin-top: .3rem;
        font-size: .64rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: .06em;
        color:
          rgba(255,255,255,.94);
      }
      /*
       * Estado normal:
       * resaltante naranja → rojo.
       */
      .countdown--normal {
        background:
          linear-gradient(
            135deg,
            #f59e0b 0%,
            #f97316 40%,
            #dc2626 100%
          );
      }
      /*
       * Menos de 2 horas.
       */
      .countdown--urgente {
        background:
          linear-gradient(
            135deg,
            #f97316 0%,
            #dc2626 45%,
            #991b1b 100%
          );
        box-shadow:
          0 7px 22px
          rgba(185,28,28,.36),
          0 0 0 2px
          rgba(254,202,202,.22);
      }
      /*
       * Últimos 30 minutos.
       */
      .countdown--critico {
        background:
          linear-gradient(
            135deg,
            #dc2626 0%,
            #b91c1c 50%,
            #7f1d1d 100%
          );
        box-shadow:
          0 8px 25px
          rgba(185,28,28,.48),
          0 0 0 3px
          rgba(254,202,202,.38);
        animation:
          pulso-cierre
          1.7s
          ease-in-out
          infinite;
      }
      /*
       * Luego de las 14:00.
       * Sigue sin realizar ninguna acción funcional.
       */
      .countdown--finalizado {
        background:
          linear-gradient(
            135deg,
            #374151 0%,
            #111827 100%
          );
        animation: none;
      }
      @keyframes pulso-cierre {
        0%,
        100% {
          transform: scale(1);
        }
        50% {
          transform: scale(1.018);
        }
      }
      /* En pantalla angosta el aviso ocupa el ancho completo. */
    @media (max-width: 900px) {
      .registro-countdown {
        align-self: stretch;
        width: 100%;
        min-width: 0;
        margin-left: 0;
      }
    }
  `],
})
export class CuentaRegresivaComponent implements OnInit, OnDestroy {
  /** Momento del cierre, en ISO con huso explícito. */
  @Input({ required: true }) cierre!: string;
  @Input() titulo = 'CIERRE DE REGISTROS';
  @Input() subtitulo = '';

  restante = '--:--:--';
  finalizado = false;
  estado: 'normal' | 'urgente' | 'critico' | 'finalizado' = 'normal';

  private limite = 0;
  private timer: ReturnType<typeof setInterval> | null = null;

  constructor(private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.limite = new Date(this.cierre).getTime();
    this.tic();
    // Un plazo ya vencido no necesita reloj: se pinta una vez y listo.
    if (!this.finalizado) {
      this.timer = setInterval(() => this.tic(), 1000);
    }
  }

  ngOnDestroy(): void { this.frenar(); }

  private frenar(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private tic(): void {
    const falta = this.limite - Date.now();

    if (falta <= 0) {
      this.restante = '00:00:00';
      this.finalizado = true;
      this.estado = 'finalizado';
      this.frenar();
      this.cdr.markForCheck();
      return;
    }

    this.finalizado = false;

    const total = Math.floor(falta / 1000);
    const hh = Math.floor(total / 3600);
    const mm = Math.floor((total % 3600) / 60);
    const ss = total % 60;
    const dosDigitos = (n: number) => String(n).padStart(2, '0');
    this.restante =
      `${dosDigitos(hh)}:${dosDigitos(mm)}:${dosDigitos(ss)}`;

    // Solo color: el estado no cambia ninguna regla de negocio.
    this.estado = falta <= 5 * 60 * 1000 ? 'critico'
      : falta <= 30 * 60 * 1000 ? 'urgente'
      : 'normal';
    this.cdr.markForCheck();
  }
}
