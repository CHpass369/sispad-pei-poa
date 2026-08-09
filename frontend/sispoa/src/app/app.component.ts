import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { AuthService } from './core/services/auth.service';
import { CapabilitiesService } from './core/services/capabilities.service';

@Component({
  standalone: false,
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<router-outlet></router-outlet>`,
})
export class AppComponent implements OnInit {
  constructor(
    private auth: AuthService,
    private capabilities: CapabilitiesService,
  ) {}

  ngOnInit(): void {
    this.auth.init();
    // Carga de capacidades para el menú dinámico (ADR-003).
    if (this.auth.isAuthenticated()) {
      this.capabilities.cargar().subscribe({
        error: () => undefined,
      });
    }
  }
}
