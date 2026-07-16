import { Component } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-header',
  template: `
    <header class="header">
      <div class="header-left">
        <h2>{{ pageTitle }}</h2>
      </div>
      <div class="header-right">
        <span class="user-info">
          {{ (auth.user$ | async)?.first_name }} {{ (auth.user$ | async)?.last_name }}
        </span>
        <button class="btn btn-outline btn-sm" (click)="auth.logout()">Salir</button>
      </div>
    </header>
  `,
  styles: [`
    .header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 1rem 1.5rem; background: var(--header-bg);
      border-bottom: 1px solid var(--border);
    }
    .header-left h2 { font-size: 1.25rem; font-weight: 700; margin: 0; }
    .header-right { display: flex; align-items: center; gap: 1rem; }
    .user-info { font-size: 0.875rem; color: var(--text-secondary); }
    .btn-sm { padding: 0.375rem 0.75rem; font-size: 0.75rem; }
  `]
})
export class HeaderComponent {
  pageTitle = 'SISPOA Sacaba';
  constructor(public auth: AuthService) {}
}
