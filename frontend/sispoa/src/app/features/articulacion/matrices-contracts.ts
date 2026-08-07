import { environment } from '../../../environments/environment';

export const ARTICULATION_MANAGEMENT = 2027;

export type ApiCollection<T> = T[] | { results?: T[] } | null | undefined;

export interface MatrixRow {
  [key: string]: unknown;
  codigo_resultado_pad?: string;
  cod_resultado_pad?: string;
  codigo_producto_pad?: string;
  cod_producto_pad?: string;
  codigo_resultado_pei?: string;
  cod_resultado_pei?: string;
  codigo_producto_pei?: string;
  cod_producto_pei?: string;
  producto_pei_nombre?: string;
  producto_pei?: string;
  accion_poa_nombre?: string;
  accion_nombre?: string;
}

export interface M1Row extends MatrixRow {
  codigo_resultado_pad: string;
  codigo_producto_pad: string;
  codigo_resultado_pei: string;
  codigo_producto_pei: string;
}

export interface M2Row extends MatrixRow {
  producto_pei_nombre: string;
}

export interface M4Row extends MatrixRow {
  accion_poa_nombre: string;
}

export interface NodoArbol {
  id: string;
  codigo_completo: string;
  codigo: string;
  nombre: string;
  nivel: string;
  tipo_plan: string;
  plan_nombre: string;
  hijos?: NodoArbol[];
  articulaciones?: any[];
}

export interface MatrizResponse {
  data: NodoArbol[];
  stats: {
    total: number;
    por_nivel: Record<string, number>;
  };
}

export function unwrapRows<T>(response: ApiCollection<T>): T[] {
  if (Array.isArray(response)) return response;
  return response?.results || [];
}

export function mapM1Rows(response: ApiCollection<MatrixRow>): M1Row[] {
  return unwrapRows(response).map((row) => ({
    ...row,
    codigo_resultado_pad: row.codigo_resultado_pad || row.cod_resultado_pad || '',
    codigo_producto_pad: row.codigo_producto_pad || row.cod_producto_pad || '',
    codigo_resultado_pei: row.codigo_resultado_pei || row.cod_resultado_pei || '',
    codigo_producto_pei: row.codigo_producto_pei || row.cod_producto_pei || '',
  }));
}

export function mapM2Rows(response: ApiCollection<MatrixRow>): M2Row[] {
  return unwrapRows(response).map((row) => ({
    ...row,
    producto_pei_nombre: row.producto_pei_nombre || row.producto_pei || '—',
  }));
}

export function mapM4Rows(response: ApiCollection<MatrixRow>): M4Row[] {
  return unwrapRows(response).map((row) => ({
    ...row,
    accion_poa_nombre: row.accion_poa_nombre || row.accion_nombre || '—',
  }));
}

export function mapM5Rows(response: ApiCollection<MatrixRow>): MatrixRow[] {
  return unwrapRows(response).map((row) => ({ ...row }));
}

export function buildReportUrl(
  path: string,
  gestion: string | number = ARTICULATION_MANAGEMENT,
): string {
  const base = environment.apiUrl.replace(/\/+$/, '');
  const endpoint = path
    .replace(/^\/?api\/v1(?=\/|$)/, '')
    .replace(/^\/+/, '');
  const separator = endpoint.includes('?') ? '&' : '?';
  return `${base}/${endpoint}${separator}gestion=${gestion}`;
}
