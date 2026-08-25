import { Component, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="login-page">
      <div class="login-card">
        <div class="login-header">
          <img class="logo-institucional" src="assets/images/logo-sacaba-horizontal.png"
               alt="Gobierno Autónomo Municipal de Sacaba" width="800" height="252">
          <h1>Plataforma Integral de Planificación</h1>
          <p>Planificación estratégica, operativa y de inversión</p>
        </div>
        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="login-form">
          <div class="field">
            <label>Correo electrónico</label>
            <input formControlName="email" type="email" class="form-control"
              placeholder="usuario@gamsacaba.gob.bo" autocomplete="email">
            </div>
            <div class="field">
              <label>Contraseña</label>
              <input formControlName="password" type="password" class="form-control"
                placeholder="••••••••" autocomplete="current-password">
              </div>
              @if (error) {
                <p class="error-msg">{{ error }}</p>
              }
              <button type="submit" class="btn btn-primary btn-block"
                [disabled]="loginForm.invalid || loading">
                {{ loading ? 'Ingresando...' : 'Ingresar' }}
              </button>
            </form>
            <div class="register-entry">
              <span>¿No tienes una cuenta?</span>
              <a routerLink="/auth/register">Crear cuenta</a>
            </div>
            <div class="login-footer">
              <small>Gobierno Autónomo Municipal de Sacaba</small>
            </div>
          </div>
        </div>
    `,
  styles: [`
    .login-page {
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
      padding: 1rem;
    }
    .login-card {
      width: 100%; max-width: 400px; background: white; border-radius: 12px;
      overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .login-header {
      padding: 2rem 2rem 0; text-align: center;
    }
    .login-header .logo-institucional {
      width: 100%; max-width: 260px; height: auto; margin-bottom: 1.25rem;
    }
    .login-header h1 {
      font-size: 1.15rem; color: var(--text); margin-bottom: 0.25rem;
      text-wrap: balance; letter-spacing: -0.01em;
    }
    .login-header p { color: var(--text-secondary); font-size: 0.875rem; }
    .login-form { padding: 2rem; }
    .field { margin-bottom: 1rem; }
    .field label { display: block; margin-bottom: 0.375rem; font-weight: 500; font-size: 0.875rem; }
    .btn-block { width: 100%; justify-content: center; padding: 0.75rem; }
    .error-msg { color: var(--warn); font-size: 0.8125rem; margin-bottom: 0.75rem; }
    .register-entry {
      display: flex; justify-content: center; gap: 0.375rem; flex-wrap: wrap;
      padding: 0 2rem 1.5rem; color: var(--pip-ink-soft); font-size: 0.875rem;
    }
    .register-entry a { color: var(--pip-green-700); font-weight: 600; }
    .register-entry a:hover { color: var(--pip-green-600); text-decoration: underline; }
    .login-footer {
      padding: 1rem 2rem; text-align: center; background: var(--bg);
      color: var(--text-secondary);
    }
  `]
})
export class LoginComponent {
  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });
  loading = false;
  error = '';

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  onSubmit(): void {
    if (this.loginForm.invalid) return;
    this.loading = true;
    this.error = '';
    this.cdr.markForCheck();
    const credentials = this.loginForm.getRawValue();
    this.auth.login({
      email: credentials.email ?? '',
      password: credentials.password ?? '',
    }).subscribe({
      next: () => this.router.navigate(['/sistemas']),
      error: (err) => {
        this.error = err.message || 'Credenciales inválidas';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }
}
