import { Component, ViewChild } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { Observable, of } from 'rxjs';
import { ComboBoxComponent, OpcionCombo } from './combo-box.component';

@Component({
  standalone: false,
  template: `
    <app-combo-box [opciones]="opciones" [buscador]="buscador"
                   [(ngModel)]="valor" etiqueta="Partida"
                   (seleccionado)="elegida = $event"></app-combo-box>
  `,
})
class AnfitrionComponent {
  @ViewChild(ComboBoxComponent) combo!: ComboBoxComponent;
  opciones: OpcionCombo[] = [];
  buscador?: (consulta: string) => Observable<OpcionCombo[]>;
  valor = '';
  elegida: OpcionCombo | null = null;
}

@Component({
  standalone: false,
  template: `
    <div style="position:absolute; top:0; left:0; width:420px">
      <div class="card">
        <app-combo-box [opciones]="opciones" [(ngModel)]="valor"></app-combo-box>
      </div>
      <div class="card" id="matriz" style="height:220px"></div>
    </div>
  `,
})
class PantallaComponent {
  @ViewChild(ComboBoxComponent) combo!: ComboBoxComponent;
  opciones: OpcionCombo[] = [];
  valor = '';
}

/**
 * El defecto que reportó la pantalla POAU (Recursos): el desplegable quedaba
 * tapado por la matriz de abajo.
 *
 * `styles.scss` —que karma carga— aplica `animation: surgir ... both` a toda
 * `.card`. Una animación con `fill-mode` deja a la tarjeta como contexto de
 * apilamiento permanente, así que desde adentro **ningún** `z-index` pasa por
 * encima de una tarjeta hermana posterior. Medido: con la lista dentro de la
 * tarjeta, `elementFromPoint` sobre ella devolvía la matriz.
 */
describe('ComboBoxComponent · desplegable sobre el contenido de abajo', () => {
  let fixture: ComponentFixture<PantallaComponent>;
  let pantalla: PantallaComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [ComboBoxComponent, PantallaComponent],
    });
    fixture = TestBed.createComponent(PantallaComponent);
    pantalla = fixture.componentInstance;
    pantalla.opciones = [
      { valor: '1', etiqueta: '1 — SECRETARIA MUNICIPAL DE FINANZAS' },
      { valor: '3', etiqueta: '3 — SECRETARIA DE PLANIFICACION' },
      { valor: '4', etiqueta: '4 — SECRETARIA DE INFRAESTRUCTURA' },
      { valor: '13', etiqueta: '13 — STAFF DE ALCALDIA' },
    ];
    fixture.detectChanges();
  });

  it('la lista queda por encima de la tarjeta de abajo, no debajo', () => {
    const input: HTMLInputElement =
      fixture.nativeElement.querySelector('input[role="combobox"]');
    input.dispatchEvent(new Event('focus'));
    fixture.detectChanges();

    const lista = document.getElementById(pantalla.combo.idLista)!;
    expect(lista).toBeTruthy();
    const r = lista.getBoundingClientRect();
    // Un punto de la lista que cae más abajo del borde de la primera tarjeta:
    // es justo donde la matriz la tapaba.
    const encima = document.elementFromPoint(r.left + 10, r.bottom - 6);
    expect(lista.contains(encima)).toBe(true);
    expect(encima!.id).not.toBe('matriz');
  });
});

describe('ComboBoxComponent', () => {
  let fixture: ComponentFixture<AnfitrionComponent>;
  let anfitrion: AnfitrionComponent;

  const CATALOGO: OpcionCombo[] = [
    { valor: '25200', etiqueta: '25200', detalle: 'Estudios e Investigaciones' },
    { valor: '25800', etiqueta: '25800', detalle: 'Consultoría por Producto' },
    { valor: '31100', etiqueta: '31100', detalle: 'Alimentos para Personas' },
  ];

  const entrada = (): HTMLInputElement =>
    fixture.nativeElement.querySelector('input[role="combobox"]');

  // La lista se cuelga del `<body>` para escapar del contexto de apilamiento
  // que `animation: surgir` crea en toda `.card`. Se la busca por su id, que
  // es único por instancia.
  const lista = (): HTMLElement | null =>
    document.getElementById(anfitrion.combo.idLista);

  const opciones = (): HTMLElement[] =>
    Array.from(lista()?.querySelectorAll('[role="option"]') ?? []);

  const teclear = (texto: string) => {
    const input = entrada();
    input.value = texto;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  };

  const tecla = (key: string) => {
    entrada().dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
    fixture.detectChanges();
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [ComboBoxComponent, AnfitrionComponent],
    });
    fixture = TestBed.createComponent(AnfitrionComponent);
    anfitrion = fixture.componentInstance;
    anfitrion.opciones = CATALOGO;
    fixture.detectChanges();
  });

  describe('modo local', () => {
    it('arranca cerrado y sin listbox en el DOM', () => {
      expect(lista()).toBeNull();
      expect(entrada().getAttribute('aria-expanded')).toBe('false');
    });

    it('al enfocar abre con el catálogo completo', () => {
      entrada().dispatchEvent(new Event('focus'));
      fixture.detectChanges();
      expect(entrada().getAttribute('aria-expanded')).toBe('true');
      expect(opciones().length).toBe(3);
    });

    it('filtra por código y por descripción', () => {
      teclear('consul');
      expect(opciones().length).toBe(1);
      expect(opciones()[0].textContent).toContain('25800');
      teclear('312');
      expect(opciones().length).toBe(0);
      teclear('311');
      expect(opciones()[0].textContent).toContain('Alimentos');
    });

    it('ignora tildes: «consultoria» encuentra «Consultoría»', () => {
      teclear('consultoria');
      expect(opciones().length).toBe(1);
      expect(opciones()[0].textContent).toContain('25800');
    });

    it('anuncia la opción resaltada con aria-activedescendant', () => {
      teclear('2');
      const activo = entrada().getAttribute('aria-activedescendant');
      expect(activo).toBeTruthy();
      expect(opciones()[0].id).toBe(activo!);
      tecla('ArrowDown');
      expect(entrada().getAttribute('aria-activedescendant')).toBe(opciones()[1].id);
    });

    it('se elige con el teclado y el valor sube al formulario', () => {
      teclear('258');
      tecla('Enter');
      expect(anfitrion.valor).toBe('25800');
      expect(anfitrion.elegida?.valor).toBe('25800');
      expect(lista()).toBeNull();
    });

    it('se elige con el mouse', () => {
      teclear('3');
      opciones()[0].click();
      fixture.detectChanges();
      expect(anfitrion.valor).toBe('31100');
    });

    it('marca con aria-selected la opción ya elegida', () => {
      teclear('258');
      tecla('Enter');
      entrada().dispatchEvent(new Event('focus'));
      fixture.detectChanges();
      const elegida = opciones().find(o => o.getAttribute('aria-selected') === 'true');
      expect(elegida?.textContent).toContain('25800');
    });

    it('al salir sin elegir recupera la etiqueta de lo que estaba elegido', () => {
      teclear('258');
      tecla('Enter');
      teclear('basura a medio tipear');
      entrada().dispatchEvent(new Event('blur'));
      fixture.detectChanges();
      expect(entrada().value).toBe('25800');
      expect(anfitrion.valor).toBe('25800');
    });

    it('Escape cierra sin cambiar lo elegido', () => {
      teclear('258');
      tecla('Enter');
      teclear('311');
      tecla('Escape');
      expect(lista()).toBeNull();
      expect(anfitrion.valor).toBe('25800');
    });
  });

  it('la lista cuelga del body y no de la tarjeta que la contiene', () => {
    // `styles.scss` anima toda `.card` con `fill-mode: both`, y eso la deja
    // como contexto de apilamiento permanente: desde adentro, ningún z-index
    // pasa por encima de una tarjeta hermana posterior.
    teclear('2');
    expect(lista()).toBeTruthy();
    expect(lista()!.parentElement).toBe(document.body);
    expect(fixture.nativeElement.querySelector('[role="listbox"]')).toBeNull();
  });

  it('al cerrarse no deja el nodo colgado del body', () => {
    teclear('2');
    expect(lista()).toBeTruthy();
    tecla('Escape');
    expect(lista()).toBeNull();
  });

  it('se posiciona contra el input, en coordenadas de ventana', () => {
    teclear('2');
    const r = entrada().getBoundingClientRect();
    expect(getComputedStyle(lista()!).position).toBe('fixed');
    expect(anfitrion.combo.caja.left).toBe(r.left);
    expect(anfitrion.combo.caja.width).toBe(r.width);
  });

  describe('modo remoto', () => {
    beforeEach(() => {
      // El clasificador real pagina: filtrar en memoria dejaría fuera la
      // mayoría de las partidas, así que el combo consulta al servidor.
      anfitrion.opciones = [];
      anfitrion.buscador = (consulta: string) => of(
        CATALOGO.filter(o => (o.detalle || '').toLowerCase().includes(consulta.toLowerCase())),
      );
      fixture.detectChanges();
    });

    it('consulta al buscador y muestra lo que devuelve', fakeAsync(() => {
      teclear('aliment');
      tick(250);
      fixture.detectChanges();
      expect(opciones().length).toBe(1);
      expect(opciones()[0].textContent).toContain('31100');
    }));

    it('no consulta una vez por tecla: espera a que el usuario pare', fakeAsync(() => {
      const espia = jasmine.createSpy('buscador').and.returnValue(of([]));
      anfitrion.buscador = espia;
      fixture.detectChanges();
      teclear('a');
      teclear('al');
      teclear('ali');
      tick(250);
      expect(espia).toHaveBeenCalledTimes(1);
      expect(espia).toHaveBeenCalledWith('ali');
    }));

    it('un catálogo caído deja la lista vacía y no rompe la pantalla', fakeAsync(() => {
      anfitrion.buscador = () => new Observable<OpcionCombo[]>(s => s.error('500'));
      fixture.detectChanges();
      teclear('lo que sea');
      tick(250);
      fixture.detectChanges();
      expect(opciones().length).toBe(0);
      expect(lista()?.querySelector('.combo-estado')?.textContent)
        .toContain('Sin coincidencias');
    }));
  });
});
