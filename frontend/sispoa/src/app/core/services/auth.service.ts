import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, switchMap, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginRequest, LoginResponse, Usuario } from '../models/usuario.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = `${environment.apiUrl}/auth`;
  private tokenKey = environment.tokenKey;
  /** Key legacy (refactor PIP): se migra a tokenKey en el constructor si existe. */
  private legacyTokenKey = 'sispoa_token';
  private userSubject = new BehaviorSubject<Usuario | null>(null);

  user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient) {
    // Migración de sesión (refactor PIP): si el usuario tenía sesión con la key
    // legacy 'sispoa_token', se traslada a la nueva key sin cerrarle la sesión.
    if (this.tokenKey !== this.legacyTokenKey) {
      const legacy = localStorage.getItem(this.legacyTokenKey);
      if (legacy && !localStorage.getItem(this.tokenKey)) {
        localStorage.setItem(this.tokenKey, legacy);
      }
      localStorage.removeItem(this.legacyTokenKey);
    }
    // No llamar loadUser() aquí — crea dependencia circular con el interceptor HTTP
  }

  /** Carga el usuario actual desde la API (llamar después de login o al iniciar app) */
  init(): void {
    const token = this.getToken();
    if (token) {
      this.loadUser();
    }
  }

  login(data: LoginRequest): Observable<Usuario> {
    return this.http.post<LoginResponse>(`${this.api}/login/`, data).pipe(
      tap(res => localStorage.setItem(this.tokenKey, JSON.stringify(res))),
      switchMap(() => this.fetchUser()),
    );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    this.userSubject.next(null);
  }

  getToken(): string | null {
    const stored = localStorage.getItem(this.tokenKey);
    if (!stored) return null;
    try {
      const parsed = JSON.parse(stored) as LoginResponse;
      return parsed.access;
    } catch {
      return null;
    }
  }

  getRefreshToken(): string | null {
    const stored = localStorage.getItem(this.tokenKey);
    if (!stored) return null;
    try {
      return JSON.parse(stored).refresh;
    } catch {
      return null;
    }
  }

  /** Obtiene el usuario de la API y lo emite en userSubject */
  private fetchUser(): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.api}/usuarios/me/`).pipe(
      tap({
        next: user => this.userSubject.next(user),
        error: () => this.logout(),
      }),
    );
  }

  /** Carga el usuario (usado desde init, sin esperar respuesta) */
  loadUser(): void {
    this.fetchUser().subscribe({ error: () => undefined });
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  hasRole(codigo: string): boolean {
    const user = this.userSubject.value;
    return user?.roles_detalle?.some(r => r.codigo === codigo) ?? false;
  }
}
