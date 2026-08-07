import {
  ARTICULATION_MANAGEMENT,
  buildReportUrl,
  mapM1Rows,
  mapM2Rows,
  mapM4Rows,
  mapM5Rows,
} from './matrices-contracts';

describe('articulation matrix API contracts', () => {
  it('uses the direct M1 payload and keeps its visible aliases', () => {
    const rows = mapM1Rows({ results: [{
      cod_resultado_pad: '01',
      resultado_pad: 'Resultado PAD 2027',
      cod_producto_pei: '01',
      producto_pei: 'Producto PEI 2027',
      estado: 'PROVISIONAL',
    }] });

    expect(rows.length).toBe(1);
    expect(rows[0].codigo_resultado_pad).toBe('01');
    expect(rows[0].codigo_producto_pei).toBe('01');
    expect(rows[0].resultado_pad).toBe('Resultado PAD 2027');
    expect(rows[0].producto_pei).toBe('Producto PEI 2027');
  });

  it('returns an empty M1 list for an empty paginated payload', () => {
    expect(mapM1Rows({ results: [] })).toEqual([]);
  });

  it('preserves the M2 product name supplied by the matrix endpoint', () => {
    const rows = mapM2Rows([{
      producto_pei: 'product-id',
      producto_pei_nombre: 'Nombre contractual 2027',
    }]);

    expect(rows[0].producto_pei_nombre).toBe('Nombre contractual 2027');
  });

  it('uses the direct M2 product alias when the preferred name is absent', () => {
    const rows = mapM2Rows([{ producto_pei: 'Nombre de respaldo API' }]);

    expect(rows[0].producto_pei_nombre).toBe('Nombre de respaldo API');
  });

  it('keeps M4 visible fields without replacing API aliases', () => {
    const rows = mapM4Rows([{
      accion_nombre: 'Acción 2027',
      operacion_nombre: 'Operación 2027',
      categoria_programatica: '000 0 001',
      ejecutado_total: '52000.00',
    }]);

    expect(rows[0].accion_poa_nombre).toBe('Acción 2027');
    expect(rows[0].categoria_programatica).toBe('000 0 001');
  });

  it('keeps M5 classifier and financing fields from the matrix payload', () => {
    const rows = mapM5Rows([{
      actividad_nombre: 'Actividad 2027',
      grupo_gasto: '2',
      fuente_financiamiento: '20',
      organismo_financiador: '210',
    }]);

    expect(rows[0].actividad_nombre).toBe('Actividad 2027');
    expect(rows[0].fuente_financiamiento).toBe('20');
    expect(rows[0].organismo_financiador).toBe('210');
  });

  it('builds report URLs once under the API base and defaults to 2027', () => {
    expect(buildReportUrl('/api/v1/reportes/articulacion_matriz_pad_pei/'))
      .toBe('/api/v1/reportes/articulacion_matriz_pad_pei/?gestion=2027');
    expect(buildReportUrl('/reportes/articulacion_matriz_pei_poa/'))
      .toBe('/api/v1/reportes/articulacion_matriz_pei_poa/?gestion=2027');
    expect(buildReportUrl('reportes/articulacion_presupuesto_seguimiento/'))
      .toBe('/api/v1/reportes/articulacion_presupuesto_seguimiento/?gestion=2027');
    expect(buildReportUrl('/reportes/articulacion_objetos_gasto/'))
      .toBe('/api/v1/reportes/articulacion_objetos_gasto/?gestion=2027');
    expect(buildReportUrl('/reportes/matriz_completa_xlsx/'))
      .toBe('/api/v1/reportes/matriz_completa_xlsx/?gestion=2027');
  });

  it('defaults the complete matrix to the 2027 demonstration management', () => {
    expect(ARTICULATION_MANAGEMENT).toBe(2027);
  });
});
