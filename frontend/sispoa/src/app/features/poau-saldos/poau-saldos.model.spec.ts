import {
  SaldoUnidadCategoriaForm,
  aPayload,
  erroresDeFormulario,
  formularioVacio,
  montoDelFormulario,
  totalDeSaldos,
} from './poau-saldos.model';

function formulario(
  cambios: Partial<SaldoUnidadCategoriaForm> = {},
): SaldoUnidadCategoriaForm {
  return {
    ...formularioVacio(),
    unidad: 'uuid-unidad',
    categoria_programatica: '280 0 004',
    ...cambios,
  };
}

describe('poau-saldos.model', () => {
  describe('erroresDeFormulario', () => {
    // La regresión que rompió producción: `<input type="number">` con ngModel
    // escribe un NUMBER en el modelo, no la cadena tipeada. La validación
    // llamaba `.trim()` sobre él, reventaba con TypeError dentro del handler
    // del click y el botón Guardar quedaba mudo: sin petición y sin mensaje.
    it('acepta el monto que entrega un input numérico sin lanzar', () => {
      expect(() => erroresDeFormulario(formulario({ saldo: 1489783 }))).not.toThrow();
      expect(erroresDeFormulario(formulario({ saldo: 1489783 }))).toEqual([]);
    });

    it('acepta el negativo, que la planilla sí declara', () => {
      expect(erroresDeFormulario(formulario({ saldo: -50000 }))).toEqual([]);
    });

    it('acepta el cero', () => {
      expect(erroresDeFormulario(formulario({ saldo: 0 }))).toEqual([]);
    });

    it('acepta la cadena con la que el backend abre la edición', () => {
      expect(erroresDeFormulario(formulario({ saldo: '250000.00' }))).toEqual([]);
    });

    it('reclama cuando el campo se vació: ngModel deja null, no cadena vacía', () => {
      expect(erroresDeFormulario(formulario({ saldo: null })))
        .toEqual(['El saldo tiene que ser un número.']);
    });

    it('reclama la unidad y la categoría faltantes', () => {
      const errores = erroresDeFormulario(
        formulario({ unidad: '', categoria_programatica: '  ', saldo: 10 }),
      );
      expect(errores).toContain('Elija la unidad organizacional.');
      expect(errores).toContain('Escriba la categoría programática.');
    });
  });

  describe('montoDelFormulario', () => {
    it('descarta lo que no es un número finito', () => {
      expect(montoDelFormulario('abc')).toBeNull();
      expect(montoDelFormulario(NaN)).toBeNull();
      expect(montoDelFormulario('')).toBeNull();
      expect(montoDelFormulario(null)).toBeNull();
    });
  });

  describe('aPayload', () => {
    // DRF valida la precisión ANTES de redondear, así que un float del
    // navegador con cola larga muere en un 400 en vez de guardarse.
    it('manda el monto como cadena de dos decimales', () => {
      expect(aPayload(formulario({ saldo: 1489783 })).saldo).toBe('1489783.00');
      expect(aPayload(formulario({ saldo: 0.1 + 0.2 })).saldo).toBe('0.30');
      expect(aPayload(formulario({ saldo: '250000' })).saldo).toBe('250000.00');
    });

    it('conserva el signo negativo', () => {
      expect(aPayload(formulario({ saldo: -1200.5 })).saldo).toBe('-1200.50');
    });

    it('no toca el resto del formulario', () => {
      const payload = aPayload(formulario({ saldo: 100, fuente: 'f1', organismo: null }));
      expect(payload.unidad).toBe('uuid-unidad');
      expect(payload.categoria_programatica).toBe('280 0 004');
      expect(payload.fuente).toBe('f1');
      expect(payload.organismo).toBeNull();
      expect(payload.activo).toBeTrue();
    });
  });

  describe('totalDeSaldos', () => {
    it('descarta lo que no parsea en vez de contarlo como cero', () => {
      const filas = [
        { saldo: '100.50' }, { saldo: 'sin dato' }, { saldo: '-20.50' },
      ] as any;
      expect(totalDeSaldos(filas)).toBe(80);
    });
  });
});
