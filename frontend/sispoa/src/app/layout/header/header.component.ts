import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-header',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="header">
      <div class="header-left">
        <button class="hamburger-btn" (click)="toggleSidebar.emit()" title="Menú">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>
        <h2>{{ pageTitle }}</h2>
      </div>
      <div class="header-right">
        <ng-container *ngIf="auth.user$ | async as user">
          <span class="user-info">{{ user.first_name }} {{ user.last_name }}</span>
        </ng-container>
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
    .header-left { display: flex; align-items: center; gap: 1rem; }
    .header-left h2 { font-size: 1.25rem; font-weight: 700; margin: 0; }
    .header-right { display: flex; align-items: center; gap: 1rem; }
    .user-info { font-size: 0.875rem; color: var(--text-secondary); }
    .btn-sm { padding: 0.375rem 0.75rem; font-size: 0.75rem; }

    .hamburger-btn {
      display: none; background: none; border: none; cursor: pointer;
      padding: 0.375rem; border-radius: 4px; flex-direction: column;
      gap: 4px;
    }
    .hamburger-line {
      display: block; width: 20px; height: 2px; background: var(--text-primary, #333);
      border-radius: 1px; transition: transform 0.2s;
    }

    @media (max-width: 1024px) {
      .hamburger-btn { display: flex; }
    }
  `]
})
export class HeaderComponent {
  @Input() sidebarCollapsed = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  pageTitle = 'SISPOA Sacaba';
  constructor(public auth: AuthService) {}
}
