import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService) {}

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(req).pipe(
      catchError((err: HttpErrorResponse) => {
        if (err.status === 401) {
          this.auth.logout();
        }
        let message = err.message || 'Error de conexión';
        try {
          const body = err.error;
          if (typeof body === 'object' && body !== null) {
            const errors = body.error || body;
            if (typeof errors === 'object') {
              message = Object.entries(errors)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
                .join('; ');
            } else if (typeof errors === 'string') {
              message = errors;
            }
          }
        } catch {}
        return throwError(() => ({ message, status: err.status }));
      })
    );
  }
}
