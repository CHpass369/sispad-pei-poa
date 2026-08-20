import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ActaOficialComponent } from './acta-oficial.component';

const ACTA = {
  titulo: 'ACTA DE PRIORIZACIÓN DE PROYECTOS Y ACTIVIDADES',
  subtitulo: 'POA 2027', distrito: 'DISTRITO 2', otb: 'OTB SAN JOSE',
  encabezado: 'El Sr. X presidente de la OTB SAN JOSE del DISTRITO 2…',
  rotulo_descripcion: 'DESCRIPCION', rotulo_monto: 'MONTO BS.-',
  rotulo_total: 'TOTAL',
  proyectos: [{ nro: 1, descripcion: 'CONST. PAVIMENTO', monto: 220000,
                sisin: '', categoria_programatica: '' }],
  total: 220000,
  aclaracion: 'Aclarar que las transferencias del TGN y la proyección de '
    + 'recursos propios del GAMS programados en el POA 2027 son proyectados…',
  nota: 'Nota: …', cierre: 'En constancia…',
  firmas: [{ rol: 'Presidente de la OTB', nombre: 'X' }],
  huella: 'a'.repeat(64),
};

describe('ActaOficialComponent', () => {
  let fixture: ComponentFixture<ActaOficialComponent>;
  let componente: ActaOficialComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule],
      declarations: [ActaOficialComponent],
    });
    fixture = TestBed.createComponent(ActaOficialComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  const cargar = (respuesta: any = ACTA, documentos: any[] = []) => {
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('acta-oficial')).flush(respuesta);
    http.expectOne(r => r.url.includes('/documentos/')).flush(documentos);
    fixture.detectChanges();
  };

  /** El @page no se puede leer con getComputedStyle: se busca en la regla. */
  const reglasDelComponente = (): string => {
    let texto = '';
    for (const hoja of Array.from(document.styleSheets)) {
      let reglas: CSSRuleList;
      try { reglas = hoja.cssRules; } catch { continue; }
      for (const regla of Array.from(reglas)) { texto += regla.cssText; }
    }
    return texto.replace(/\s+/g, ' ');
  };

  it('declara la hoja en tamaño oficio, no en Legal', () => {
    cargar();
    const css = reglasDelComponente();
    // Oficio es 216 x 330 mm; el Legal norteamericano mide 216 x 356.
    expect(css).toContain('216mm 330mm');
    expect(css).not.toContain('size: legal');
  });

  it('la vista previa usa la misma medida que la impresión', () => {
    cargar();
    const hoja = fixture.nativeElement.querySelector('.hoja') as HTMLElement;
    // 216mm ≈ 816px a 96dpi; se compara con holgura por el redondeo.
    expect(hoja.getBoundingClientRect().width).toBeGreaterThan(700);
  });

  it('arma el acta con sus proyectos, el total y las firmas', () => {
    cargar();
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('ACTA DE PRIORIZACIÓN DE PROYECTOS Y ACTIVIDADES');
    expect(texto).toContain('POA 2027');
    expect(texto).toContain('CONST. PAVIMENTO');
    expect(texto).toContain('220,000');
    expect(texto).toContain('Presidente de la OTB');
  });

  it('incluye la aclaración sobre los recursos debajo de la tabla', () => {
    cargar();
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('transferencias del TGN');
    expect(texto).toContain('recursos propios del GAMS');
    // Va después de la tabla, no antes.
    expect(texto.indexOf('transferencias del TGN'))
      .toBeGreaterThan(texto.indexOf('MONTO BS.-'));
  });

  it('muestra la huella al pie, sin el rótulo', () => {
    cargar();
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('a'.repeat(64));
    expect(texto).not.toContain('Verificación del contenido');
    expect(texto).not.toContain('SHA-256');
  });

  it('descarga el PDF del servidor en vez de abrir el diálogo del navegador',
     () => {
    const imprimir = spyOn(window, 'print');
    cargar();
    componente.descargar();
    const pedido = http.expectOne(r => r.url.endsWith('/pdf/'));
    expect(pedido.request.responseType).toBe('blob');
    pedido.flush(new Blob(['%PDF-1.4'], { type: 'application/pdf' }));
    // El diálogo nativo usaría el tamaño de papel del usuario y escalaría.
    expect(imprimir).not.toHaveBeenCalled();
  });

  it('avisa si el PDF no se pudo generar', () => {
    cargar();
    componente.descargar();
    http.expectOne(r => r.url.endsWith('/pdf/'))
        .flush(null, { status: 500, statusText: 'Error' });
    expect(componente.error).toContain('No se pudo generar el PDF');
    expect(componente.bajando).toBe(false);
  });

  it('muestra el motivo del backend cuando el acta no se puede emitir', () => {
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('acta-oficial')).flush(
      { error: 'El acta no tiene fecha: no se puede emitir.' },
      { status: 400, statusText: 'Bad Request' });
    fixture.detectChanges();
    expect(componente.error).toContain('no tiene fecha');
    expect(fixture.nativeElement.querySelector('.hoja')).toBeNull();
  });
});

describe('ActaOficialComponent · documentos cifrados', () => {
  let fixture: ComponentFixture<ActaOficialComponent>;
  let componente: ActaOficialComponent;
  let http: HttpTestingController;

  const DOCS = [
    { id: 'd1', nombre: 'acta.pdf', tipo_documento: 'ACTA_GENERADA',
      tamanio_bytes: 8192, hash_sha256: 'a'.repeat(64) },
    { id: 'd2', nombre: 'firmada.pdf', tipo_documento: 'ACTA_ESCANEADA',
      tamanio_bytes: 4096, hash_sha256: 'b'.repeat(64) },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule],
      declarations: [ActaOficialComponent],
    });
    fixture = TestBed.createComponent(ActaOficialComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('acta-oficial')).flush(ACTA);
    http.expectOne(r => r.url.includes('/documentos/')).flush(DOCS);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('lista el emitido y el escaneado', () => {
    expect(componente.documentos.length).toBe(2);
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('acta.pdf');
    expect(texto).toContain('firmada.pdf');
    expect(texto).toContain('emitido');
    expect(texto).toContain('escaneado');
  });

  it('adjuntar manda el archivo y recarga la lista', () => {
    const archivo = new File([new Blob(['x'])], 'escaneada.pdf',
                             { type: 'application/pdf' });
    const entrada = { files: [archivo], value: 'c:\\escaneada.pdf' } as any;
    componente.adjuntar({ target: entrada } as any);

    const subida = http.expectOne(r => r.url.endsWith('/adjuntar/'));
    expect(subida.request.method).toBe('POST');
    expect(subida.request.body instanceof FormData).toBe(true);
    subida.flush({ id: 'd3', nombre: 'escaneada.pdf' });

    http.expectOne(r => r.url.includes('/documentos/')).flush(DOCS);
    expect(entrada.value).toBe('');
  });

  it('sin archivo elegido no pega en el backend', () => {
    componente.adjuntar({ target: { files: [] } } as any);
    http.expectNone(() => true);
  });

  it('descarga el documento por el endpoint que descifra', () => {
    componente.bajarDocumento(DOCS[1]);
    const pedido = http.expectOne(r => r.url.endsWith('/documentos/d2/descargar/'));
    expect(pedido.request.responseType).toBe('blob');
    pedido.flush(new Blob(['%PDF'], { type: 'application/pdf' }));
  });

  it('un documento alterado se avisa, no se baja en silencio', async () => {
    componente.bajarDocumento(DOCS[1]);
    // El error de una descarga blob vuelve como Blob, no como JSON.
    http.expectOne(r => r.url.endsWith('/descargar/')).flush(
      new Blob([JSON.stringify({ error: 'El documento no se pudo descifrar.' })],
               { type: 'application/json' }),
      { status: 409, statusText: 'Conflict' });
    await new Promise(r => setTimeout(r, 50));
    expect(componente.error).toContain('no se pudo descifrar');
  });
});
