import { Component, Input, TemplateRef } from '@angular/core';

export interface Columna {
  key: string;
  label: string;
}

export interface Accion {
  label: string;
  handler: (fila: unknown) => void;
}

@Component({
  selector: 'app-tabla-generica',
  standalone: false,
  templateUrl: './tabla-generica.component.html',
})
export class TablaGenericaComponent {
  @Input() columns: Columna[] = [];
  @Input() data: any[] = [];
  @Input() acciones: Accion[] = [];
  @Input() loading = false;

  // Paginación
  @Input() pageSize = 10;
  currentPage = 1;

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.data.length / this.pageSize));
  }

  get paginatedData(): any[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.data.slice(start, start + this.pageSize);
  }

  previousPage(): void {
    if (this.currentPage > 1) this.currentPage--;
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) this.currentPage++;
  }
}
