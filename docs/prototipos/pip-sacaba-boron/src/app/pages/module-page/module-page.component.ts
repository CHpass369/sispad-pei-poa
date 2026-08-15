import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-module-page',
  standalone: true,
  templateUrl: './module-page.component.html',
  styleUrl: './module-page.component.scss'
})
export class ModulePageComponent {
  private route = inject(ActivatedRoute);
  title = this.route.snapshot.data['title'] as string;
  area = this.route.snapshot.data['area'] as string;
  kind = this.route.snapshot.data['kind'] as string;

  readonly rows = [
    { code: '01.01.001', name: 'Fortalecimiento de la gestión institucional', unit: 'Planificación', amount: 'Bs 1.250.000', state: 'Validado' },
    { code: '01.02.004', name: 'Gestión territorial y administración de tierras', unit: 'Catastro', amount: 'Bs 3.480.000', state: 'En revisión' },
    { code: '02.03.012', name: 'Mejoramiento de infraestructura municipal', unit: 'Obras Públicas', amount: 'Bs 8.720.000', state: 'Borrador' },
    { code: '03.01.008', name: 'Gestión ambiental y resiliencia urbana', unit: 'Medio Ambiente', amount: 'Bs 2.150.000', state: 'Validado' }
  ];
}
