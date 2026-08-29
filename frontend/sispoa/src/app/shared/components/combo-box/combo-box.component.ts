import {
  AfterViewChecked, Component, ElementRef, EventEmitter, forwardRef, Input,
  OnDestroy, Output, ViewChild,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { Observable, Subject, Subscription, of } from 'rxjs';
import { debounceTime, switchMap } from 'rxjs/operators';

/** Una fila del desplegable. El consumidor mapea su catálogo a esto. */
export interface OpcionCombo {
  /** Lo que se guarda en el formulario. */
  valor: string;
  /** Lo que se ve y sobre lo que se busca. */
  etiqueta: string;
  /** Segunda línea, para desambiguar dos etiquetas parecidas. */
  detalle?: string;
  /** El registro original, para quien necesite más campos al seleccionar. */
  dato?: any;
}

/** Sin esto «Consultoría» no se encuentra tecleando «consultoria». */
export function normalizar(texto: string): string {
  return (texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .trim();
}

let secuencia = 0;

/**
 * Combo box accesible: se escribe para filtrar y se elige de una lista.
 *
 * Sigue el patrón ARIA de combobox con listbox: `role="combobox"` sobre el
 * input, `aria-expanded`, `aria-controls` y `aria-activedescendant` apuntando
 * a la opción resaltada. Un `<select>` no sirve acá porque los catálogos
 * tienen cientos de filas y no se pueden recorrer con la rueda del mouse.
 *
 * Dos modos:
 * - **local**: se le pasa `opciones` y filtra en memoria (catálogos chicos).
 * - **remoto**: se le pasa `buscador` y consulta al servidor con debounce.
 *   Es el único modo válido para catálogos paginados —el clasificador de
 *   objeto del gasto tiene 505 partidas y la API devuelve 25 por página—.
 *
 * **La lista se cuelga del `<body>`, no del componente.** `styles.scss` aplica
 * `animation: surgir ... both` a toda `.card`, y una animación con `fill-mode`
 * deja a la tarjeta como contexto de apilamiento **para siempre**: ningún
 * `z-index` de adentro puede pasar por encima de una tarjeta hermana
 * posterior. Medido en el navegador: con la lista dentro de la tarjeta gana
 * siempre la matriz de abajo; colgándola del body, gana la lista. Por eso va
 * en `position: fixed` contra el rectángulo del input.
 */
@Component({
  selector: 'app-combo-box',
  standalone: false,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => ComboBoxComponent),
    multi: true,
  }],
  template: `
    <div class="combo" [class.deshabilitado]="disabled">
      <input #entrada type="text" class="form-control" role="combobox"
             autocomplete="off"
             [id]="idCampo"
             [value]="texto"
             [disabled]="disabled"
             [placeholder]="placeholder"
             [attr.aria-label]="etiqueta || null"
             [attr.aria-expanded]="abierto"
             [attr.aria-controls]="idLista"
             aria-autocomplete="list"
             [attr.aria-activedescendant]="idOpcionActiva"
             (input)="alEscribir($any($event.target).value)"
             (focus)="abrir()"
             (blur)="alSalir()"
             (keydown)="alTeclear($event)">
      <button type="button" class="combo-flecha" tabindex="-1" aria-hidden="true"
              [disabled]="disabled" (mousedown)="$event.preventDefault()"
              (click)="alternar()">▾</button>

      <ul #lista class="combo-lista" role="listbox" [id]="idLista" *ngIf="abierto"
          [style.top.px]="caja.top" [style.left.px]="caja.left"
          [style.width.px]="caja.width" [style.maxHeight.px]="caja.alto"
          (mousedown)="$event.preventDefault()">
        <li *ngIf="buscando" class="combo-estado">Buscando…</li>
        <li *ngIf="!buscando && !visibles.length" class="combo-estado">
          Sin coincidencias
        </li>
        <li *ngFor="let o of visibles; let i = index"
            class="combo-opcion" role="option"
            [id]="idLista + '-op-' + i"
            [class.activa]="i === activa"
            [attr.aria-selected]="o.valor === valor"
            (mouseenter)="activa = i"
            (click)="elegir(o)">
          <span class="combo-etiqueta">{{ o.etiqueta }}</span>
          <span class="combo-detalle" *ngIf="o.detalle">{{ o.detalle }}</span>
        </li>
      </ul>
    </div>
  `,
  styles: [`
    .combo { position: relative; }
    .combo-flecha {
      position: absolute; right: 0; top: 0; height: 100%; width: 1.75rem;
      border: none; background: none; cursor: pointer; color: var(--text-secondary);
      font-size: 0.7rem;
    }
    .combo.deshabilitado .combo-flecha { cursor: default; opacity: .4; }
    .combo-lista {
      position: fixed; z-index: 1200;
      margin: 0; padding: 0; list-style: none;
      overflow-y: auto; background: var(--surface);
      border: 1px solid var(--border); border-radius: var(--radius);
      box-shadow: 0 6px 18px rgba(0,0,0,.14);
    }
    .combo-opcion { padding: 0.35rem 0.6rem; cursor: pointer; font-size: 0.8125rem; }
    .combo-opcion.activa { background: var(--pip-green-100); }
    .combo-etiqueta { display: block; }
    .combo-detalle {
      display: block; font-size: 0.6875rem; color: var(--text-secondary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .combo-estado {
      padding: 0.45rem 0.6rem; font-size: 0.75rem; color: var(--text-secondary);
    }
  `],
})
export class ComboBoxComponent
  implements ControlValueAccessor, AfterViewChecked, OnDestroy {
  @Input() opciones: OpcionCombo[] = [];
  @Input() placeholder = '';
  /** Texto para lectores de pantalla cuando el `<label>` no envuelve al input. */
  @Input() etiqueta = '';
  @Input() disabled = false;
  /** Modo remoto: devuelve las opciones que coinciden con lo tecleado. */
  @Input() buscador?: (consulta: string) => Observable<OpcionCombo[]>;
  /** Cuántas filas se muestran en modo local. */
  @Input() maximo = 50;

  @Output() seleccionado = new EventEmitter<OpcionCombo | null>();

  @ViewChild('entrada') entrada?: ElementRef<HTMLInputElement>;
  @ViewChild('lista') lista?: ElementRef<HTMLElement>;

  readonly idCampo = `combo-${++secuencia}`;
  readonly idLista = `${this.idCampo}-lista`;

  valor = '';
  texto = '';
  abierto = false;
  buscando = false;
  activa = -1;
  visibles: OpcionCombo[] = [];

  /** Posición de la lista en la ventana, medida contra el input. */
  caja = { top: 0, left: 0, width: 0, alto: 260 };
  /** El nodo ya se mudó al `<body>`: no hay que mudarlo en cada ciclo. */
  private mudada = false;

  private consultas = new Subject<string>();
  private suscripcion: Subscription;
  private alCambiar: (valor: string) => void = () => {};
  private alTocar: () => void = () => {};

  constructor() {
    // Solo el camino remoto pasa por acá: filtrar en memoria con 250 ms de
    // retardo se siente roto, y el `switchMap` descarta la respuesta vieja
    // cuando el usuario sigue tecleando.
    this.suscripcion = this.consultas.pipe(
      debounceTime(250),
      switchMap(consulta => this.buscador
        ? this.buscador(consulta)
        : of([] as OpcionCombo[])),
    ).subscribe({
      next: opciones => this.mostrar(opciones),
      // Un catálogo caído deja la lista vacía, no la pantalla rota.
      error: () => this.mostrar([]),
    });
  }

  /**
   * Muda la lista al `<body>` en cuanto Angular la crea.
   *
   * `*ngIf` la borra por `parentNode.removeChild`, y después de la mudanza su
   * `parentNode` es el body: Angular la sigue destruyendo bien sola.
   */
  ngAfterViewChecked(): void {
    const nodo = this.lista?.nativeElement;
    if (nodo && !this.mudada) {
      document.body.appendChild(nodo);
      this.mudada = true;
      this.medir();
    }
  }

  ngOnDestroy(): void {
    this.suscripcion.unsubscribe();
    this.dejarDeSeguir();
    // Si el componente muere con la lista abierta, el nodo quedaría colgado
    // del body para siempre.
    this.lista?.nativeElement.remove();
  }

  /**
   * Recalcula dónde va la lista.
   *
   * Va contra el rectángulo del input y no contra el componente porque, al
   * estar en `position: fixed`, sus coordenadas son de la ventana.
   */
  private medir(): void {
    const campo = this.entrada?.nativeElement;
    if (!campo) { return; }
    const r = campo.getBoundingClientRect();
    const abajo = window.innerHeight - r.bottom - 8;
    const arriba = r.top - 8;
    // Si abajo no entra ni lo mínimo, se despliega hacia arriba.
    const haciaArriba = abajo < 140 && arriba > abajo;
    const alto = Math.min(260, Math.max(120, haciaArriba ? arriba : abajo));
    this.caja = {
      top: haciaArriba ? r.top - alto - 2 : r.bottom + 2,
      left: r.left,
      width: r.width,
      alto,
    };
  }

  /** Al hacer scroll la lista se despega del input: hay que seguirlo. */
  private seguir = () => {
    if (!this.abierto) { return; }
    this.medir();
  };

  private empezarASeguir(): void {
    // `true` es el capture: sin él no se entera del scroll de un contenedor
    // interno, que es justo donde viven estos formularios.
    window.addEventListener('scroll', this.seguir, true);
    window.addEventListener('resize', this.seguir);
  }

  private dejarDeSeguir(): void {
    window.removeEventListener('scroll', this.seguir, true);
    window.removeEventListener('resize', this.seguir);
  }

  // --- ControlValueAccessor -------------------------------------------------

  writeValue(valor: string): void {
    this.valor = valor || '';
    this.texto = this.etiquetaDe(this.valor);
  }

  registerOnChange(fn: (valor: string) => void): void { this.alCambiar = fn; }
  registerOnTouched(fn: () => void): void { this.alTocar = fn; }
  setDisabledState(deshabilitado: boolean): void { this.disabled = deshabilitado; }

  // --- Interacción ----------------------------------------------------------

  get idOpcionActiva(): string | null {
    return this.abierto && this.activa >= 0
      ? `${this.idLista}-op-${this.activa}` : null;
  }

  abrir(): void {
    if (this.disabled || this.abierto) { return; }
    this.abierto = true;
    this.medir();
    this.empezarASeguir();
    // Con '' y no con `texto`: al volver a abrir, filtrar por la etiqueta ya
    // elegida deja una lista de un solo elemento y no se puede cambiar.
    this.buscar('');
  }

  cerrar(): void {
    this.abierto = false;
    this.activa = -1;
    this.mudada = false;
    this.dejarDeSeguir();
  }

  alternar(): void {
    if (this.disabled) { return; }
    if (this.abierto) { this.cerrar(); } else { this.entrada?.nativeElement.focus(); }
  }

  alEscribir(texto: string): void {
    this.texto = texto;
    if (!this.abierto) { this.empezarASeguir(); }
    this.abierto = true;
    this.medir();
    this.buscar(texto);
  }

  /**
   * Al salir se recupera la etiqueta de lo elegido.
   *
   * Sin esto queda en pantalla un texto a medio tipear que no corresponde a
   * ningún registro, y el usuario cree que eligió algo que nunca eligió.
   */
  alSalir(): void {
    this.cerrar();
    this.texto = this.etiquetaDe(this.valor);
    this.alTocar();
  }

  alTeclear(evento: KeyboardEvent): void {
    switch (evento.key) {
      case 'ArrowDown':
        evento.preventDefault();
        if (!this.abierto) { this.abrir(); return; }
        this.activa = Math.min(this.activa + 1, this.visibles.length - 1);
        break;
      case 'ArrowUp':
        evento.preventDefault();
        this.activa = Math.max(this.activa - 1, 0);
        break;
      case 'Enter':
        if (this.abierto && this.activa >= 0) {
          evento.preventDefault();
          this.elegir(this.visibles[this.activa]);
        }
        break;
      case 'Escape':
        this.cerrar();
        this.texto = this.etiquetaDe(this.valor);
        break;
      case 'Tab':
        this.cerrar();
        break;
    }
  }

  elegir(opcion: OpcionCombo): void {
    this.valor = opcion.valor;
    this.texto = opcion.etiqueta;
    this.cerrar();
    this.alCambiar(this.valor);
    this.seleccionado.emit(opcion);
  }

  /** Limpia la selección desde afuera sin emitir un valor a medias. */
  limpiar(): void {
    this.valor = '';
    this.texto = '';
    this.visibles = [];
    this.alCambiar('');
  }

  // --- Interno --------------------------------------------------------------

  private buscar(consulta: string): void {
    if (!this.buscador) {
      this.mostrar(this.filtrarLocal(consulta));
      return;
    }
    this.buscando = true;
    this.consultas.next(consulta);
  }

  private mostrar(opciones: OpcionCombo[]): void {
    this.visibles = opciones;
    this.activa = opciones.length ? 0 : -1;
    this.buscando = false;
  }

  private filtrarLocal(consulta: string): OpcionCombo[] {
    const aguja = normalizar(consulta);
    const fuente = aguja
      ? this.opciones.filter(o =>
          normalizar(`${o.etiqueta} ${o.detalle || ''}`).includes(aguja))
      : this.opciones;
    return fuente.slice(0, this.maximo);
  }

  private etiquetaDe(valor: string): string {
    if (!valor) { return ''; }
    const encontrada = this.opciones.find(o => o.valor === valor)
      || this.visibles.find(o => o.valor === valor);
    // En modo remoto la opción puede no estar cargada: el código ya es
    // identificación suficiente y es mejor eso que dejar el campo en blanco.
    return encontrada ? encontrada.etiqueta : valor;
  }
}
