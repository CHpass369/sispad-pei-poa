import { adminApiErrorMessage } from './admin-api-error';

/**
 * `ErrorInterceptor` is registered globally in `AppModule`, so admin screens
 * never receive a raw `HttpErrorResponse` — they receive the flattened
 * `{message, status, code}`. These cases lock that contract: a helper that only
 * understood the raw shape replaced every backend reason with the caller's
 * generic fallback, which is what hid "la unidad organizacional no pertenece a
 * la gestión fiscal" behind "revise los datos seleccionados".
 */
describe('adminApiErrorMessage', () => {
  const FALLBACK = 'FALLBACK';

  describe('flattened errors (what components actually get)', () => {
    it('surfaces the backend reason for a 400', () => {
      const flattened = {
        status: 400,
        message: 'La unidad organizacional no pertenece a la gestión fiscal.',
      };

      expect(adminApiErrorMessage(flattened, FALLBACK))
        .toBe('La unidad organizacional no pertenece a la gestión fiscal.');
    });

    it('prefers the backend reason over the generic 403 text', () => {
      const flattened = { status: 403, message: 'No puede asignar el rol solicitado.' };

      expect(adminApiErrorMessage(flattened, FALLBACK))
        .toBe('No puede asignar el rol solicitado.');
    });

    it('keeps the domain code message from a 409', () => {
      const flattened = {
        status: 409,
        message: 'Gestión no habilitada.',
        code: 'gestion_no_habilitada',
      };

      expect(adminApiErrorMessage(flattened, FALLBACK)).toBe('Gestión no habilitada.');
    });

    it('never shows Angular transport noise', () => {
      const flattened = {
        status: 0,
        message: 'Http failure response for /api/v2/admin/users/x/approve/: 0 Unknown Error',
      };

      expect(adminApiErrorMessage(flattened, FALLBACK)).toBe(FALLBACK);
    });
  });

  describe('raw response bodies (defensive path)', () => {
    it('reads a string body', () => {
      expect(adminApiErrorMessage({ status: 400, error: 'Rol inexistente.' }, FALLBACK))
        .toBe('Rol inexistente.');
    });

    it('reads the first string of an error array', () => {
      const raw = { status: 400, error: { error: ['La gestión fiscal no existe.'] } };

      expect(adminApiErrorMessage(raw, FALLBACK)).toBe('La gestión fiscal no existe.');
    });

    it('falls back to the authority text for a bodiless 403', () => {
      expect(adminApiErrorMessage({ status: 403 }, FALLBACK))
        .toBe('El backend rechazó la operación por falta de autoridad.');
    });
  });

  it('falls back when there is nothing to show', () => {
    expect(adminApiErrorMessage(null, FALLBACK)).toBe(FALLBACK);
    expect(adminApiErrorMessage({ status: 500 }, FALLBACK)).toBe(FALLBACK);
  });
});
