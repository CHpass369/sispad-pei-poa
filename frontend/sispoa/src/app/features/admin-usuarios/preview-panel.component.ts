import { Component, Input } from '@angular/core';
import { AdminAccessPreviewResponse } from './admin-usuarios.service';

@Component({
  selector: 'app-preview-panel',
  standalone: false,
  template: `
    @if (preview) {
      <aside class="preview-panel" aria-labelledby="access-preview-title">
        <h4 id="access-preview-title">Vista previa del acceso</h4>
        <p>{{ preview.effective_uos.length }} unidad(es) y {{ preview.capabilities.length }} permiso(s) efectivo(s).</p>
        <p><strong>Permisos:</strong> {{ capabilitySummary }}</p>
        <p><strong>Unidades:</strong> {{ unitSummary }}</p>
        <ul>
          @for (module of preview.modules; track module.codigo) {
            @if (module.visible) { <li>{{ module.codigo }} · {{ module.sistema }}</li> }
          }
        </ul>
      </aside>
    }
  `,
})
export class PreviewPanelComponent {
  @Input() preview: AdminAccessPreviewResponse | null = null;

  get capabilitySummary(): string {
    return this.preview?.capabilities.map(capability => capability.nombre).join(', ') || 'Ninguno';
  }

  get unitSummary(): string {
    return this.preview?.effective_uos.map(unit => `${unit.codigo} · ${unit.nombre}`).join(', ') || 'Ninguna';
  }
}
