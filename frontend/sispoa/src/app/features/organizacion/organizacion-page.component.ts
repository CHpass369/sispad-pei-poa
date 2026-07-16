import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

type TabId = 'unidades' | 'da' | 'ue';

@Component({
  selector: 'app-organizacion-page',
  standalone: false,
  templateUrl: './organizacion-page.component.html',
})
export class OrganizacionPageComponent {
  tabActivo: TabId = 'unidades';

  tabs: { id: TabId; label: string }[] = [
    { id: 'unidades', label: 'Unidades' },
    { id: 'da', label: 'DA (Direcciones Administrativas)' },
    { id: 'ue', label: 'UE (Unidades Ejecutoras)' },
  ];

  activarTab(tab: TabId): void {
    this.tabActivo = tab;
  }
}
