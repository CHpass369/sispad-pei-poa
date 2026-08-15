import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { Usuario } from '../../core/models/usuario.model';

@Component({
  standalone: false,
  selector: 'app-header',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="topbar">
      <button class="icon-btn" (click)="toggleSidebar.emit()" aria-label="Contraer menú" title="Contraer menú">
        <lucide-angular [name]="'menu'" [size]="18"></lucide-angular>
      </button>
      <div class="search">
        <lucide-angular [name]="'search'" [size]="14"></lucide-angular>
        <input type="text" placeholder="Buscar módulos, instrumentos, proyectos…" aria-label="Buscar">
        <kbd>⌘K</kbd>
      </div>
      <div class="topbar-right">
        @if (auth.user$ | async; as user) {
          <span class="topbar-pill"><span class="dot"></span> Gestión 2027</span>
          <div class="avatar" [attr.aria-label]="'Usuario: ' + user.first_name + ' ' + user.last_name">{{ initials(user) }}</div>
          <button class="btn btn-outline btn-sm" (click)="auth.logout()">Salir</button>
        }
      </div>
    </header>
    `,
  styles: [`
    .topbar {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 26px;
      background: var(--pip-card);
      border-bottom: 1px solid var(--pip-line);
      position: sticky; top: 0; z-index: 20;
    }
    .icon-btn {
      width: 34px; height: 34px; border-radius: 8px;
      border: 1px solid var(--pip-line); background: var(--pip-surface);
      cursor: pointer; font-size: 15px; color: var(--pip-ink);
      display: grid; place-items: center;
    }
    .icon-btn:hover { border-color: var(--pip-green-500); }
    .search {
      flex: 1; max-width: 420px;
      display: flex; align-items: center; gap: 8px;
      background: var(--pip-surface);
      border: 1px solid var(--pip-line);
      border-radius: 8px;
      padding: 7px 12px;
    }
    .search input {
      border: none; background: none; outline: none;
      font-family: inherit; font-size: 13px; color: var(--pip-ink); width: 100%;
    }
    .search input::placeholder { color: var(--pip-ink-soft); }
    .search kbd {
      margin-left: auto; font-family: var(--font-mono); font-size: 10px;
      background: #fff; border: 1px solid var(--pip-line); border-radius: 4px;
      padding: 1px 5px; color: var(--pip-ink-soft);
    }
    .topbar-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
    .topbar-pill {
      font-size: 11.5px; font-weight: 600;
      border: 1px solid var(--pip-line); border-radius: 20px;
      padding: 4px 12px; background: var(--pip-surface); color: var(--pip-ink);
      display: flex; align-items: center; gap: 6px;
    }
    .topbar-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--pip-gold); }
    .avatar {
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--pip-green-700); color: #fff;
      display: grid; place-items: center;
      font-size: 12px; font-weight: 600;
    }
    .btn-sm { padding: 0.375rem 0.75rem; font-size: 0.75rem; }

    @media (max-width: 860px) {
      .topbar { padding: 10px 16px; }
      .search { max-width: 180px; }
      .topbar-pill { display: none; }
    }
  `]
})
export class HeaderComponent {
  @Output() toggleSidebar = new EventEmitter<void>();

  constructor(public auth: AuthService) {}

  initials(user: Usuario): string {
    return ((user.first_name?.[0] ?? '') + (user.last_name?.[0] ?? '')).toUpperCase();
  }
}
