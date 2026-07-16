import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-root',
  template: `
    <div class="app-layout" [class.auth-mode]="isAuthRoute">
      <app-sidebar *ngIf="!isAuthRoute"></app-sidebar>
      <div class="main-content">
        <app-header *ngIf="!isAuthRoute"></app-header>
        <main>
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-layout { display: flex; min-height: 100vh; }
    .app-layout.auth-mode { display: block; }
    .main-content { flex: 1; margin-left: 260px; }
    .auth-mode .main-content { margin-left: 0; }
    main { padding: 1.5rem; }
  `]
})
export class AppComponent implements OnInit {
  get isAuthRoute(): boolean {
    return this.router.url.startsWith('/auth');
  }
  constructor(private router: Router, private auth: AuthService) {}
  ngOnInit(): void {
    this.auth.init();
  }
}
