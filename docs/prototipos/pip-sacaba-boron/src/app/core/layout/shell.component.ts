import { Component, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface NavItem {
  label: string;
  route: string;
  icon: string;
  group?: string;
}

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgClass],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss'
})
export class ShellComponent {
  collapsed = signal(false);
  mobileOpen = signal(false);
  dark = signal(false);

  readonly nav: NavItem[] = [
    { label: 'Panel principal', route: '/dashboard', icon: 'grid', group: 'PIP' },
    { label: 'SIS-PE', route: '/sis-pe', icon: 'strategy', group: 'Sistemas' },
    { label: 'SIS-POA', route: '/sis-poa', icon: 'calendar', group: 'Sistemas' },
    { label: 'SIS-PRO', route: '/sis-pro', icon: 'project', group: 'Sistemas' },
    { label: 'Catálogos maestros', route: '/catalogos', icon: 'database', group: 'Transversal' },
    { label: 'Administración', route: '/administracion', icon: 'shield', group: 'Transversal' }
  ];

  toggleTheme(): void {
    const next = !this.dark();
    this.dark.set(next);
    document.documentElement.dataset['theme'] = next ? 'dark' : 'light';
  }

  iconPath(icon: string): string {
    const paths: Record<string, string> = {
      grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
      strategy: 'M4 18h4V9H4v9Zm6 0h4V4h-4v14Zm6 0h4v-7h-4v7Z',
      calendar: 'M5 4v3M19 4v3M4 9h16M5 6h14a1 1 0 0 1 1 1v13H4V7a1 1 0 0 1 1-1Z',
      project: 'M4 7h16v13H4zM8 7V4h8v3M8 12h8M8 16h5',
      database: 'M4 6c0-2 16-2 16 0s-16 2-16 0Zm0 0v6c0 2 16 2 16 0V6m-16 6v6c0 2 16 2 16 0v-6',
      shield: 'M12 3 5 6v5c0 4.5 2.8 8 7 10 4.2-2 7-5.5 7-10V6l-7-3Zm-3 9 2 2 4-5'
    };
    return paths[icon] ?? paths['grid'];
  }
}
