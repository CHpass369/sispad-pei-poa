import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

/** Error aplanado que reciben los componentes. */
export interface ErrorApi {
  message: string;
  status: number;
  /** Código de dominio, cuando el backend lo manda (p. ej. `gestion_no_habilitada`). */
  code?: string;
}

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService) {}

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((err: HttpErrorResponse) => {
        if (err.status === 401) {
          this.auth.logout();
        }
        return throwError(() => this.aplanar(err));
      })
    );
  }

  /**
   * Aplana el cuerpo del error en `{message, status, code}`.
   *
   * El `code` viaja aparte porque el mensaje solo no alcanza para decidir:
   * un 409 puede ser una versión fijada o una gestión no habilitada, y la
   * pantalla reacciona distinto a cada uno.
   */
  private aplanar(err: HttpErrorResponse): ErrorApi {
    const salida: ErrorApi = {
      message: err.message || 'Error de conexión',
      status: err.status,
    };
    const body = err.error;
    if (typeof body !== 'object' || body === null) {
      return salida;
    }
    const errores = body.error ?? body;
    if (typeof errores === 'string') {
      salida.message = errores;
      return salida;
    }
    if (typeof errores !== 'object' || errores === null) {
      return salida;
    }
    if (typeof errores.code === 'string') {
      salida.code = errores.code;
    }
    // `detail` es el contrato de error de dominio del backend
    // (`{error: {detail, code}}`); el resto son errores por campo.
    if (errores.detail !== undefined) {
      salida.message = Array.isArray(errores.detail)
        ? errores.detail.join(' ')
        : String(errores.detail);
      return salida;
    }
    salida.message = Object.entries(errores)
      .filter(([clave]) => clave !== 'code')
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join('; ') || salida.message;
    return salida;
  }
}
