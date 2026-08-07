import { buildOperacionTree } from './matriz-poapoau.component';

describe('buildOperacionTree', () => {
  it('uses the nested M3 contract without secondary CRUD payloads', () => {
    const result = buildOperacionTree([{
      codigo_operacion: '2027.001.001',
      denominacion: 'Servicios jurídicos',
      actividades: [{
        codigo_actividad: '2027.001.001.001',
        denominacion: 'Atender procesos',
        tareas: [{ codigo_tarea: '2027.001.001.001.001', denominacion: 'Revisar antecedentes' }],
      }],
    }]);

    expect(result.operaciones.length).toBe(1);
    expect(result.operaciones[0].actividades.length).toBe(1);
    expect(result.operaciones[0].actividades[0].tareas[0].denominacion).toBe('Revisar antecedentes');
    expect(result.stats).toEqual({ ops: 1, acts: 1, tars: 1 });
  });

  it('keeps empty activities visible and reports zero child counts', () => {
    const result = buildOperacionTree([{
      codigo_operacion: '2027.001.001',
      denominacion: 'Operación sin desglose',
      actividades: [],
    }]);

    expect(result.operaciones.length).toBe(1);
    expect(result.operaciones[0].actividades).toEqual([]);
    expect(result.stats).toEqual({ ops: 1, acts: 0, tars: 0 });
  });
});
