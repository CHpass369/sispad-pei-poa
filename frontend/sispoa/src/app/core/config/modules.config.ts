export type ModuleSystem = 'sis_pe' | 'sis_poa';

export interface ModuleMetadata {
  codigo: string;
  nombre: string;
  sistema: ModuleSystem;
  capacidades: readonly string[];
}

/** UI grouping only; capability authority remains in the backend catalog. */
export const MODULES_CONFIG: readonly ModuleMetadata[] = [
  {
    codigo: 'instrumento',
    nombre: 'Instrumentos',
    sistema: 'sis_pe',
    capacidades: ['sis_pe.instrumento.read', 'sis_pe.instrumento.create', 'sis_pe.approve'],
  },
  {
    codigo: 'pad',
    nombre: 'PAD',
    sistema: 'sis_pe',
    capacidades: ['sis_pe.pad.view', 'sis_pe.pad.edit', 'sis_pe.pad.validate'],
  },
  {
    codigo: 'pei',
    nombre: 'PEI',
    sistema: 'sis_pe',
    capacidades: ['sis_pe.pei.view', 'sis_pe.pei.edit'],
  },
  {
    codigo: 'articulacion',
    nombre: 'Articulación',
    sistema: 'sis_pe',
    capacidades: [
      'sis_pe.articulacion.view',
      'sis_pe.articulacion.edit',
      'sis_pe.articulacion.manage',
    ],
  },
  {
    codigo: 'indicadores',
    nombre: 'Indicadores',
    sistema: 'sis_pe',
    capacidades: [
      'sis_pe.indicadores.view',
      'sis_pe.indicadores.edit',
      'sis_pe.indicadores.read',
      'sis_pe.indicadores.measure',
    ],
  },
  {
    codigo: 'evaluacion',
    nombre: 'Evaluación',
    sistema: 'sis_pe',
    capacidades: ['sis_pe.evaluacion.view', 'sis_pe.evaluacion.edit', 'sis_pe.approve'],
  },
  {
    codigo: 'poa',
    nombre: 'POA',
    sistema: 'sis_poa',
    capacidades: ['sis_poa.poa.view', 'sis_poa.poa.edit', 'sis_poa.formulate', 'sis_poa.approve'],
  },
  {
    codigo: 'poau',
    nombre: 'POAU',
    sistema: 'sis_poa',
    capacidades: [
      'sis_poa.poau.view',
      'sis_poa.poau.create',
      'sis_poa.poau.edit',
      'sis_poa.poau.submit',
      'sis_poa.poau.review',
      'sis_poa.poau.approve',
    ],
  },
  {
    codigo: 'techos',
    nombre: 'Techos',
    sistema: 'sis_poa',
    capacidades: [
      'sis_poa.techos.view',
      'sis_poa.techos.edit',
      'sis_poa.budget.manage',
      'sis_poa.budget.validate',
      'sis_poa.budget.approve',
      'sis_poa.budget.reopen',
      'sis_poa.budget.audit_read',
    ],
  },
  {
    codigo: 'distribuciones',
    nombre: 'Distribuciones',
    sistema: 'sis_poa',
    capacidades: [
      'sis_poa.distribuciones.view',
      'sis_poa.distribuciones.edit',
      'sis_poa.budget.manage',
      'sis_poa.budget.import',
      'sis_poa.budget.reform',
    ],
  },
  {
    codigo: 'programacion',
    nombre: 'Programación',
    sistema: 'sis_poa',
    capacidades: ['sis_poa.programacion.view', 'sis_poa.programacion.edit', 'sis_poa.formulate'],
  },
  {
    codigo: 'seguimiento',
    nombre: 'Seguimiento',
    sistema: 'sis_poa',
    capacidades: [
      'sis_poa.seguimiento.view',
      'sis_poa.seguimiento.edit',
      'sis_poa.seguimiento.manage',
      'sis_poa.reportes.view',
    ],
  },
];

function moduleCapabilities(system: ModuleSystem, moduleCode: string): string[] {
  const module = MODULES_CONFIG.find(item => (
    item.sistema === system && item.codigo === moduleCode
  ));
  return module ? [...module.capacidades] : [];
}

function systemCapabilities(system: ModuleSystem): string[] {
  return [...new Set(
    MODULES_CONFIG
      .filter(module => module.sistema === system)
      .flatMap(module => module.capacidades),
  )];
}

/** Canonical UI aggregates derived from module metadata. */
export const SIS_PE_CAPABILITIES = systemCapabilities('sis_pe');
export const SIS_PE_PEI_CAPABILITIES = moduleCapabilities('sis_pe', 'pei');
