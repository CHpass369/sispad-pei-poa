import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  standalone: false,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="app-layout">
      <app-sidebar (sidebarToggle)="sidebarCollapsed = $event"></app-sidebar>
      <div class="main-content" [class.main-expanded]="sidebarCollapsed">
        <app-header></app-header>
        <div class="content-area">
          <app-breadcrumbs></app-breadcrumbs>
        </div>
        <main>
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-layout { display: flex; min-height: 100vh; }
    .main-content { flex: 1; margin-left: 260px; transition: margin-left 0.2s ease; min-width: 0; }
    .main-expanded { margin-left: 64px; }
    .content-area { padding: 0 1.5rem; }
    main { padding: 0 1.5rem 1.5rem; }
  `]
})
export class LayoutComponent {
  sidebarCollapsed = false;
}
