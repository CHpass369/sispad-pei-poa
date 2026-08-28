import {
  MODULES_CONFIG,
  SIS_PE_CAPABILITIES,
  SIS_PE_PEI_CAPABILITIES,
} from './modules.config';

describe('module metadata registry', () => {
  it('contains typed modules for SIS-PE and SIS-POA only', () => {
    expect(MODULES_CONFIG.length).toBeGreaterThan(0);
    expect(MODULES_CONFIG.map(module => module.codigo)).toEqual([
      'instrumento', 'pad', 'pei', 'articulacion', 'indicadores', 'evaluacion',
      'poa', 'poau', 'techos', 'distribuciones', 'programacion', 'seguimiento',
    ]);
    expect(MODULES_CONFIG.every(module =>
      module.sistema === 'sis_pe' || module.sistema === 'sis_poa',
    )).toBeTrue();
    expect(MODULES_CONFIG.some(module => String(module.sistema) === 'sis_pro')).toBeFalse();
  });

  it('references existing capability codes without defining new namespaces', () => {
    const capabilityCodes = MODULES_CONFIG.flatMap(module => module.capacidades);

    expect(capabilityCodes).toContain('sis_pe.pad.view');
    expect(capabilityCodes).toContain('sis_poa.poau.view');
    expect(capabilityCodes.every(code =>
      code.startsWith('sis_pe.') || code.startsWith('sis_poa.'),
    )).toBeTrue();
    expect(MODULES_CONFIG.every(module =>
      module.capacidades.length > 0 && module.capacidades.every(code => code.includes('.')),
    )).toBeTrue();
  });

  it('derives the canonical SIS-PE aggregate and PEI capabilities from module metadata', () => {
    const sisPeCapabilities = MODULES_CONFIG
      .filter(module => module.sistema === 'sis_pe')
      .flatMap(module => module.capacidades);
    const peiCapabilities = MODULES_CONFIG
      .find(module => module.codigo === 'pei')
      ?.capacidades;

    expect(SIS_PE_CAPABILITIES).toEqual([...new Set(sisPeCapabilities)]);
    expect(SIS_PE_PEI_CAPABILITIES).toEqual(peiCapabilities);
    expect(SIS_PE_PEI_CAPABILITIES).toEqual(['sis_pe.pei.view', 'sis_pe.pei.edit']);
  });
});
