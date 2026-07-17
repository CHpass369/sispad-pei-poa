import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-root',
  template: `
    <div class="app-layout" [class.auth-mode]="isAuthRoute">
      <app-sidebar *ngIf="!isAuthRoute"
                   (sidebarToggle)="onSidebarToggle($event)"
                   #sidebar></app-sidebar>
      <div class="main-content" [class.main-expanded]="sidebarCollapsed">
        <app-header *ngIf="!isAuthRoute"
                    (toggleSidebar)="onToggleMobileSidebar()"
                    [sidebarCollapsed]="sidebarCollapsed"></app-header>
        <div class="content-area" *ngIf="!isAuthRoute">
          <app-breadcrumbs></app-breadcrumbs>
        </div>
        <main [class.main-auth]="isAuthRoute">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-layout { display: flex; min-height: 100vh; }
    .app-layout.auth-mode { display: block; }
    .main-content {
      flex: 1; margin-left: 260px; transition: margin-left 0.2s ease;
      min-width: 0;
    }
    .main-expanded { margin-left: 64px; }
    .auth-mode .main-content { margin-left: 0; }
    .content-area { padding: 0 1.5rem; }
    main { padding: 0 1.5rem 1.5rem; }
    .main-auth { padding: 0; }

    @media (max-width: 1024px) {
      .main-content { margin-left: 0 !important; }
    }
  `]
})
export class AppComponent implements OnInit {
  sidebarCollapsed = false;

  get isAuthRoute(): boolean {
    return this.router.url.startsWith('/auth');
  }

  constructor(private router: Router, private auth: AuthService) {}

  ngOnInit(): void {
    this.auth.init();
  }

  onSidebarToggle(collapsed: boolean): void {
    this.sidebarCollapsed = collapsed;
  }

  onToggleMobileSidebar(): void {
    const sidebar = document.querySelector('.sidebar') as HTMLElement;
    if (sidebar) {
      sidebar.classList.toggle('sidebar-open');
    }
  }
}
