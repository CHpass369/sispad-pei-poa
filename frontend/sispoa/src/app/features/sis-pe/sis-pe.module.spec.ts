import { CapabilityGuard } from '../../core/guards/capability.guard';
import {
  SIS_PE_CAPABILITIES,
  SIS_PE_PEI_CAPABILITIES,
} from '../../core/config/modules.config';
import { SIS_PE_ROUTES } from './sis-pe.module';

describe('SisPeModule routes', () => {
  it('aligns the dashboard entry guard with the canonical SIS-PE aggregate', () => {
    const dashboard = SIS_PE_ROUTES.find(route => route.path === 'dashboard');

    expect(dashboard?.canActivate).toContain(CapabilityGuard);
    expect(dashboard?.data?.['capacidades']).toEqual(SIS_PE_CAPABILITIES);
  });

  it('protects PEI with its canonical view and edit capabilities', () => {
    const pei = SIS_PE_ROUTES.find(route => route.path === 'pei');

    expect(pei?.canActivate).toContain(CapabilityGuard);
    expect(pei?.data?.['capacidades']).toEqual(SIS_PE_PEI_CAPABILITIES);
    expect(pei?.data?.['capacidades']).not.toContain('sis_pe.instrumento.read');
  });

  it('does not broaden the instrument-only route with unrelated SIS-PE capabilities', () => {
    const instrumentos = SIS_PE_ROUTES.find(route => route.path === 'instrumentos');

    expect(instrumentos?.data?.['capacidades']).toEqual(['sis_pe.instrumento.read']);
    expect(instrumentos?.data?.['capacidades']).not.toContain('sis_pe.pei.view');
  });
});
