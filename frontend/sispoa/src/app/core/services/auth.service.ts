import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LoginRequest, LoginResponse, Usuario } from '../models/usuario.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = `${environment.apiUrl}/auth`;
  private tokenKey = environment.tokenKey;
  private userSubject = new BehaviorSubject<Usuario | null>(null);

  user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient) {
    // No llamar loadUser() aquí — crea dependencia circular con el interceptor HTTP
  }

  /** Carga el usuario actual desde la API (llamar después de login o al iniciar app) */
  init(): void {
    const token = this.getToken();
    if (token) {
      this.loadUser();
    }
  }

  login(data: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.api}/login/`, data).pipe(
      tap(res => {
        localStorage.setItem(this.tokenKey, JSON.stringify(res));
        this.loadUser();
      })
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

  loadUser(): void {
    this.http.get<Usuario>(`${this.api}/usuarios/me/`).subscribe({
      next: user => this.userSubject.next(user),
      error: () => this.logout(),
    });
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  hasRole(codigo: string): boolean {
    const user = this.userSubject.value;
    return user?.roles_detalle?.some(r => r.codigo === codigo) ?? false;
  }
}
