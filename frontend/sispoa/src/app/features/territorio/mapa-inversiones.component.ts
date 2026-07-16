import { Component, OnInit, AfterViewInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

declare var L: any;

@Component({
  standalone: false,
  selector: 'app-mapa-inversiones',
  template: `
    <div class="mapa-page">
      <div class="page-header">
        <h2>Mapa de Inversiones</h2>
        <p class="text-secondary">Localización territorial de proyectos y acciones POA {{ gestion }}</p>
        <div class="filtros">
          <label>Año:</label>
          <select [(ngModel)]="gestion" (change)="cargarMapa()" class="form-control filtro-select">
            <option [value]="2025">2025</option>
            <option [value]="2026">2026</option>
          </select>
        </div>
      </div>
      <div class="map-container" id="mapa"></div>
      <div class="map-legend">
        <div class="legend-item"><span class="dot" style="background:#1B5E3B"></span> Proyectos</div>
        <div class="legend-item"><span class="dot" style="background:#C7952E"></span> Acciones</div>
      </div>
      <p *ngIf="totalPuntos > 0" class="text-secondary" style="margin-top:0.5rem;">
        Mostrando {{ totalPuntos }} localizaciones
      </p>
    </div>
  `,
  styles: [`
    .mapa-page { display: flex; flex-direction: column; height: calc(100vh - 120px); }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; margin-bottom: 0.25rem; }
    .filtros { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
    .filtro-select { width: 100px; padding: 0.25rem 0.5rem; }
    .map-container { flex: 1; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); min-height: 400px; }
    .map-legend { display: flex; gap: 1rem; margin-top: 0.75rem; }
    .legend-item { display: flex; align-items: center; gap: 0.375rem; font-size: 0.8125rem; }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }
  `]
})
export class MapaInversionesComponent implements OnInit, AfterViewInit {
  gestion = 2026;
  totalPuntos = 0;
  private map: any;
  private markersLayer: any;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadLeaflet();
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.cargarMapa(), 500);
  }

  private loadLeaflet(): void {
    if (!(window as any).L) {
      const script = document.createElement('link');
      script.rel = 'stylesheet';
      script.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(script);
      const js = document.createElement('script');
      js.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      js.onload = () => this.cargarMapa();
      document.body.appendChild(js);
    }
  }

  cargarMapa(): void {
    if (!(window as any).L) return;
    const L = (window as any).L;

    if (!this.map) {
      this.map = L.map('mapa').setView([-17.4, -66.05], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; GAM Sacaba',
        maxZoom: 18,
      }).addTo(this.map);
      this.markersLayer = L.featureGroup().addTo(this.map);
    }

    this.markersLayer.clearLayers();
    this.totalPuntos = 0;

    this.api.get<any>('/reportes/mapa/', { gestion: this.gestion }).subscribe({
      next: (geojson) => {
        if (geojson.features) {
          this.totalPuntos = geojson.features.length;
          const layer = L.geoJSON(geojson, {
            pointToLayer: (feature: any, latlng: any) => {
              return L.circleMarker(latlng, {
                radius: 8,
                fillColor: '#1B5E3B',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8,
              });
            },
            onEachFeature: (feature: any, layer: any) => {
              if (feature.properties) {
                layer.bindPopup(`
                  <b>${feature.properties.entidad || 'Sin nombre'}</b><br>
                  ${feature.properties.distrito ? 'Distrito: ' + feature.properties.distrito + '<br>' : ''}
                  ${feature.properties.unidad_territorial || ''}
                `);
              }
            },
          });
          this.markersLayer.addLayer(layer);
          this.map.fitBounds(layer.getBounds().pad(0.1));
        }
      },
    });
  }
}
