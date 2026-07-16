import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CatalogosService, CatalogoItem } from './catalogos.service';

export interface TipoCatalogo {
  valor: string;
  etiqueta: string;
}

@Component({
  standalone: false,
  selector: 'app-catalogo-lista',
  templateUrl: './catalogo-lista.component.html',
})
export class CatalogoListaComponent implements OnInit {
  tipos: TipoCatalogo[] = [
    { valor: 'clasificadores-institucionales', etiqueta: 'Clasificadores Institucionales' },
    { valor: 'rubros', etiqueta: 'Rubros' },
    { valor: 'objetos-gasto', etiqueta: 'Objetos de Gasto' },
    { valor: 'fuentes', etiqueta: 'Fuentes' },
    { valor: 'organismos', etiqueta: 'Organismos' },
    { valor: 'entidades-transferencia', etiqueta: 'Entidades de Transferencia' },
    { valor: 'finalidades-funciones', etiqueta: 'Finalidades y Funciones' },
    { valor: 'unidades-medida', etiqueta: 'Unidades de Medida' },
    { valor: 'tipos-operacion', etiqueta: 'Tipos de Operación' },
    { valor: 'tipos-producto', etiqueta: 'Tipos de Producto' },
    { valor: 'tipos-proyecto', etiqueta: 'Tipos de Proyecto' },
    { valor: 'tipos-financiamiento', etiqueta: 'Tipos de Financiamiento' },
  ];

  tipoSeleccionado = '';
  gestion = new Date().getFullYear();
  searchTerm = '';
  loading = false;
  data: CatalogoItem[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private catalogosService: CatalogosService,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const tipo = params.get('tipo');
      if (tipo) {
        this.tipoSeleccionado = tipo;
        this.cargar();
      }
    });
  }

  onTipoChange(): void {
    this.router.navigate(['/catalogos', this.tipoSeleccionado]);
  }

  cargar(): void {
    if (!this.tipoSeleccionado) return;

    this.loading = true;
    const params: { gestion?: number; search?: string } = {};

    if (this.gestion) params.gestion = this.gestion;
    if (this.searchTerm.trim()) params.search = this.searchTerm.trim();

    this.catalogosService.listar(this.tipoSeleccionado, params).subscribe({
      next: (res) => {
        this.data = res;
        this.loading = false;
      },
      error: () => {
        this.data = [];
        this.loading = false;
      },
    });
  }

  buscar(): void {
    this.cargar();
  }

  /** Abre el selector de archivos y envía el archivo seleccionado al endpoint de importación */
  importarArchivo(): void {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.csv';
    input.onchange = () => {
      const file = input.files?.item(0);
      if (!file || !this.tipoSeleccionado) return;

      const formData = new FormData();
      formData.append('archivo', file);

      this.loading = true;
      this.catalogosService.importar(this.tipoSeleccionado, formData).subscribe({
        next: (res) => {
          alert(`Importación exitosa: ${res.cantidad} registros procesados.`);
          this.cargar();
        },
        error: () => {
          alert('Error al importar el archivo. Verifique el formato e intente nuevamente.');
          this.loading = false;
        },
      });
    };
    input.click();
  }

  /** Columnas dinámicas para la tabla genérica (se infieren de la data) */
  get columnas() {
    if (this.data.length === 0) return [];
    const keys = Object.keys(this.data[0] as object);
    return keys.map(k => ({
      key: k,
      label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    }));
  }
}
