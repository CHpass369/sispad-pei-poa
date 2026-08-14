import { Pipe, PipeTransform } from '@angular/core';

/**
 * Pipe `moneda`: formatea montos como `Bs 1.234.567,89` (es-BO).
 *
 * Acepta números o strings (la API V2 serializa los Decimal como string,
 * convención COERCE_DECIMAL_TO_STRING de DRF).
 *
 * Declarado en el módulo budget (`BudgetModule`): por ahora es de uso
 * exclusivo del ciclo presupuestario; si otra feature lo necesita, se
 * mueve a un SharedModule.
 */
@Pipe({ name: 'moneda', standalone: false })
export class MonedaPipe implements PipeTransform {
  transform(valor: number | string | null | undefined): string {
    const numero =
      typeof valor === 'string' ? parseFloat(valor) : (valor ?? 0);
    if (Number.isNaN(numero)) return 'Bs 0,00';
    const formateado = new Intl.NumberFormat('es-BO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numero);
    return `Bs ${formateado}`;
  }
}
