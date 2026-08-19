import { ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { MatricesPadService } from '../matrices-pad.service';
import {
  AcuerdoInternacionalOption,
  CompatibilidadAcuerdo,
  CompatibilidadesAcuerdosService,
} from './compatibilidades-acuerdos.service';
import { PadWizardComponent } from './pad-wizard.component';

describe('PadWizardComponent agreement cascade', () => {
  let component: PadWizardComponent;
  let serviceSpy: jasmine.SpyObj<CompatibilidadesAcuerdosService>;

  const ods: AcuerdoInternacionalOption = {
    id: 'ods-id', tipo_acuerdo: 'ODS', codigo: '6.6', denominacion: 'Agua',
  };
  const ndc: AcuerdoInternacionalOption = {
    id: 'ndc-id', tipo_acuerdo: 'NDC', codigo: 'NDC-1', denominacion: 'Clima',
  };
  const ndt: AcuerdoInternacionalOption = {
    id: 'ndt-id', tipo_acuerdo: 'NDT', codigo: 'NDT-1', denominacion: 'Tierra',
  };
  const kmgbf: AcuerdoInternacionalOption = {
    id: 'kmgbf-id', tipo_acuerdo: 'COMPROMISO_3030', codigo: '3', denominacion: 'Target 3',
  };

  const relation = (
    origen: AcuerdoInternacionalOption,
    destino: AcuerdoInternacionalOption,
    tipo_relacion: CompatibilidadAcuerdo['tipo_relacion'] = 'OFICIAL_EXPLICITA',
  ): CompatibilidadAcuerdo => ({
    id: `${origen.id}-${destino.id}`,
    origen,
    destino,
    tipo_relacion,
    tipo_relacion_display: tipo_relacion,
    estado: tipo_relacion === 'SUGERENCIA_SEMANTICA' ? 'CANDIDATA' : 'VALIDADA',
    estado_display: 'Validada',
    confianza: tipo_relacion === 'SUGERENCIA_SEMANTICA' ? 'BAJA' : 'ALTA',
    confianza_display: tipo_relacion === 'SUGERENCIA_SEMANTICA' ? 'Baja' : 'Alta',
    fuente_url: '', fuente_titulo: '', fuente_version: '', localizador: '',
    evidencia: 'Prueba', justificacion: 'Prueba', activo: true,
  });

  beforeEach(() => {
    serviceSpy = jasmine.createSpyObj<CompatibilidadesAcuerdosService>(
      'CompatibilidadesAcuerdosService', ['listar'],
    );
    serviceSpy.listar.and.callFake(query => {
      if (query.destinoTipo === 'NDC') {
        return of({ count: 1, next: null, previous: null, results: [relation(ods, ndc)] });
      }
      if (query.destinoTipo === 'NDT') {
        return of({ count: 1, next: null, previous: null, results: [relation(ndc, ndt)] });
      }
      return of({ count: 1, next: null, previous: null, results: [relation(ndt, kmgbf)] });
    });

    component = new PadWizardComponent(
      {} as ApiService,
      {} as MatricesPadService,
      { snapshot: { paramMap: { get: () => null } } } as unknown as ActivatedRoute,
      { markForCheck: jasmine.createSpy('markForCheck') } as unknown as ChangeDetectorRef,
      serviceSpy,
    );
    component.acuerdos = [ods, ndc, ndt, kmgbf];
  });

  it('filters NDC, NDT and KMGBF in sequence', () => {
    component.cabecera.codOds = '6.6';
    component.onOdsChange();
    expect(component.catalogoNdc.map(option => option.codigo)).toEqual(['NDC-1']);

    component.cabecera.codNdc = 'NDC-1';
    component.onNdcChange();
    expect(component.catalogoNdt.map(option => option.codigo)).toEqual(['NDT-1']);

    component.cabecera.codNdt = 'NDT-1';
    component.onNdtChange();
    expect(component.catalogo3030.map(option => option.codigo)).toEqual(['3']);
  });

  it('clears downstream selections when an upstream value changes', () => {
    component.cabecera.codOds = '6.6';
    component.cabecera.codNdc = 'NDC-1';
    component.cabecera.codNdt = 'NDT-1';
    component.cabecera.compromiso3030 = '3';

    component.onOdsChange();

    expect(component.cabecera.codNdc).toBe('N/A');
    expect(component.cabecera.codNdt).toBe('N/A');
    expect(component.cabecera.compromiso3030).toBe('N/A');
  });

  it('labels semantic suggestions and warns that they are not normative', () => {
    const suggestion = relation(ods, ndc, 'SUGERENCIA_SEMANTICA');
    serviceSpy.listar.and.returnValue(of({
      count: 1, next: null, previous: null, results: [suggestion],
    }));
    component.cabecera.codOds = '6.6';
    component.onOdsChange();

    expect(component.etiquetaCompatibilidad(component.catalogoNdc[0])).toContain('Sugerencia IA');
    expect(component.mensajeCascada('NDC')).toContain('no constituyen compatibilidad normativa');
  });
});
