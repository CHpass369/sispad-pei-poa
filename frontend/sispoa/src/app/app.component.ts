import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { AuthService } from './core/services/auth.service';
import { CapabilitiesService } from './core/services/capabilities.service';
import { GestionHabilitadaService } from './core/services/gestion-habilitada.service';

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
    private gestion: GestionHabilitadaService,
  ) {}

  ngOnInit(): void {
    this.auth.init();
    if (this.auth.isAuthenticated()) {
      // Capacidades para el menú dinámico (ADR-003).
      this.capabilities.cargar().subscribe({
        error: () => undefined,
      });
      // Gestión habilitada: el candado de SIS-POA (ADR-007). Se carga una sola
      // vez al arranque y de ahí la absorben todos los módulos, en vez de que
      // cada pantalla clave su propio año.
      this.gestion.cargar().subscribe({
        error: () => undefined,
      });
    }
  }
}
