/**
 * Saldo presupuestario disponible por unidad organizacional y categoría
 * programática.
 *
 * Fuente: planilla `PLANILLA_REVISION_UNIDADES_saldo_y_unidad_organizacional`
 * (revisión de unidades, 2026-09-03). Columna B categoría programática,
 * columna D código de unidad organizacional, columna E nombre de la unidad y
 * columna J el saldo, que es el monto original menos el personal eventual.
 *
 * Dos precisiones sobre el traslado de la planilla a este catálogo:
 *
 * - La planilla trae 199 filas y este catálogo 174 entradas. Veinte filas
 *   repiten el par (unidad, categoría) — `097 0 001` de `SP-DPD-19` aparece
 *   dieciséis veces — y sus saldos se suman: el monto disponible para
 *   programar en una categoría es todo lo que esa unidad tiene ahí, no la
 *   última fila leída.
 * - Cinco filas de `TRASPASOS EMAPAS` no declaran unidad organizacional
 *   (4.989.000,00 Bs. en transferencias a una entidad externa) y quedan fuera:
 *   sin unidad no hay forma de alcanzarlas desde el selector.
 *
 * `SD-000-55` en `280 0 004` queda con saldo negativo (-11.521,00 Bs.): la
 * planilla lo marca «SALDO NEGATIVO – revisar» y se traslada tal cual, porque
 * redondearlo a cero inventaría un margen que la unidad no tiene.
 */

export interface SaldoUnidadCategoria {
  /** Código de la unidad organizacional en el catálogo PIP. */
  codigoUnidad: string;
  nombreUnidad: string;
  /** Categoría programática, con el formato `NNN N NNN` de la planilla. */
  categoriaProgramatica: string;
  denominacion: string;
  /** Saldo disponible para programar, en bolivianos. */
  saldo: number;
  /** Filas de la planilla que se sumaron en esta entrada. */
  filasOrigen: number;
}

export const SALDOS_UNIDAD_CATEGORIA: SaldoUnidadCategoria[] = [
  { codigoUnidad: 'EM-000-05', nombreUnidad: 'TRANSPARENCIA', categoriaProgramatica: '340 0 099', denominacion: 'TRANSPARENCIA', saldo: 250000, filasOrigen: 1 },
  { codigoUnidad: 'EM-D01', nombreUnidad: 'SUBALCALDÍA DISTRITO 1', categoriaProgramatica: '343 0 001', denominacion: 'SUB ALCALDIA DISTRITO 1', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'EM-D02', nombreUnidad: 'SUBALCALDÍA DISTRITO 2', categoriaProgramatica: '343 0 010', denominacion: 'SUB ALCALDIA DISTRITO 2', saldo: 300000, filasOrigen: 1 },
  { codigoUnidad: 'EM-DCR-03', nombreUnidad: 'COMUNICACIÓN E IMAGEN INSTITUCIONAL', categoriaProgramatica: '344 0 004', denominacion: 'COORD. Y REL.INT. - COMUNICACIÓN', saldo: 300000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '330 0 080', denominacion: 'SEGURIDAD CIUDADANA', saldo: 144563, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '330 0 081', denominacion: 'SEGURIDAD CIUDADANA', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '331 0 014', denominacion: 'SEGURIDAD CIUDADANA', saldo: 480000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '331 0 015', denominacion: 'SEGURIDAD CIUDADANA', saldo: 740400, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '331 0 016', denominacion: 'SEGURIDAD CIUDADANA', saldo: 1011940, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '331 0 022', denominacion: 'SEGURIDAD CIUDADANA', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54', nombreUnidad: 'ADMINISTRACIÓN SEGURIDAD CIUDADANA Y MOVILIDAD MUNICIPAL', categoriaProgramatica: '332 0 007', denominacion: 'SEGURIDAD CIUDADANA', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-54-1', nombreUnidad: 'REGULACIÓN Y ORDENAMIENTO DE LA MOVILIDAD', categoriaProgramatica: '271 0 008', denominacion: 'REGULACIÓN Y ORDENAMIENTO DE MOVILIDAD MUNICIPAL', saldo: 31000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-55', nombreUnidad: 'INTENDENCIA MUNICIPAL', categoriaProgramatica: '280 0 004', denominacion: 'INTENDENCIA MUNICIPAL', saldo: -11521, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-55', nombreUnidad: 'INTENDENCIA MUNICIPAL', categoriaProgramatica: '280 0 005', denominacion: 'INTENDENCIA MUNICIPAL', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SD-000-55', nombreUnidad: 'INTENDENCIA MUNICIPAL', categoriaProgramatica: '281 0 003', denominacion: 'INTENDENCIA MUNICIPAL', saldo: 200000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-1', nombreUnidad: 'ADULTO MAYOR', categoriaProgramatica: '253 0 005', denominacion: 'ADULTO MAYOR', saldo: 94555, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-13', nombreUnidad: 'PREVENCIÓN CONTRA LA VIOLENCIA SLIM-DNA', categoriaProgramatica: '251 0 092', denominacion: 'PREVENCION CONTRA LA VIOLENCIA SLIM-DNA', saldo: 16000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-13', nombreUnidad: 'PREVENCIÓN CONTRA LA VIOLENCIA SLIM-DNA', categoriaProgramatica: '261 0 001', denominacion: 'PREVENCION CONTRA LA VIOLENCIA SLIM-DNA', saldo: 168000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-2', nombreUnidad: 'UMADIS', categoriaProgramatica: '250 0 081', denominacion: 'UMADIS', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-2', nombreUnidad: 'UMADIS', categoriaProgramatica: '250 0 089', denominacion: 'UMADIS', saldo: 3687000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-2', nombreUnidad: 'UMADIS', categoriaProgramatica: '254 0 006', denominacion: 'UMADIS', saldo: 163532, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-3', nombreUnidad: 'SERVICIO LEGAL INTEGRAL MUNICIPAL (SLIM)', categoriaProgramatica: '250 0 060', denominacion: 'SLIM', saldo: 365515, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-3', nombreUnidad: 'SERVICIO LEGAL INTEGRAL MUNICIPAL (SLIM)', categoriaProgramatica: '251 0 017', denominacion: 'SLIM', saldo: 163780, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-4', nombreUnidad: 'DEFENSORÍA DE LA NIÑEZ Y ADOLESCENCIA (DNA)', categoriaProgramatica: '260 0 003', denominacion: 'DNA', saldo: 70098, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-4', nombreUnidad: 'DEFENSORÍA DE LA NIÑEZ Y ADOLESCENCIA (DNA)', categoriaProgramatica: '260 0 004', denominacion: 'DNA', saldo: 344683, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 005', denominacion: 'ASUNTOS DE GENERO', saldo: 428000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 009', denominacion: 'ASUNTOS DE GENERO', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 010', denominacion: 'ASUNTOS DE GENERO', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 012', denominacion: 'ASUNTOS DE GENERO', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 015', denominacion: 'ASUNTOS DE GENERO', saldo: 90000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 023', denominacion: 'ASUNTOS DE GENERO', saldo: 110000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 028', denominacion: 'ASUNTOS DE GENERO', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-5', nombreUnidad: 'ASUNTOS DE GÉNERO', categoriaProgramatica: '252 0 030', denominacion: 'ASUNTOS DE GENERO', saldo: 29000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-52-6', nombreUnidad: 'ATENCIÓN A LA INFANCIA Y JUVENTUDES', categoriaProgramatica: '255 0 010', denominacion: 'JUVENTUDES', saldo: 80000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-1', nombreUnidad: 'ALIMENTO COMPLEMENTARIO', categoriaProgramatica: '211 0 004', denominacion: 'ALIMENTO COMPLEMENTARIO', saldo: 36239000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-3', nombreUnidad: 'PROGRAMAS EDUCACIÓN', categoriaProgramatica: '215 0 015', denominacion: 'PROGRAMAS EDUCACION', saldo: 6786695, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-4', nombreUnidad: 'EQUIPAMIENTO U.E.', categoriaProgramatica: '214 0 034', denominacion: 'EQUIPAMIENTO DE U.E.', saldo: 60000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-4', nombreUnidad: 'EQUIPAMIENTO U.E.', categoriaProgramatica: '214 0 038', denominacion: 'EQUIPAMIENTO DE U.E.', saldo: 8500000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-4', nombreUnidad: 'EQUIPAMIENTO U.E.', categoriaProgramatica: '214 0 046', denominacion: 'EQUIPAMIENTO DE U.E.', saldo: 850000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-4', nombreUnidad: 'EQUIPAMIENTO U.E.', categoriaProgramatica: '214 0 051', denominacion: 'EQUIPAMIENTO DE U.E.', saldo: 300000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-5', nombreUnidad: 'MANTENIMIENTO U.E.', categoriaProgramatica: '217 0 001', denominacion: 'MANTENIMIENTO DE U.E.', saldo: 6000000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-5', nombreUnidad: 'MANTENIMIENTO U.E.', categoriaProgramatica: '217 0 006', denominacion: 'MANTENIMIENTO DE U.E.', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 001', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 3786152, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 028', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 4485555, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 029', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 72000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 039', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 2814828, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 041', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 546400, filasOrigen: 2 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 042', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 2900000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-6', nombreUnidad: 'SERVICIOS DE EDUCACIÓN', categoriaProgramatica: '210 0 044', denominacion: 'SERVICIOS DE EDUCACIÓN', saldo: 179200, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-53-7', nombreUnidad: 'UAIN@', categoriaProgramatica: '212 0 005', denominacion: 'UAIN@', saldo: 2573727, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-56', nombreUnidad: 'DEPORTES Y PROMOCIÓN', categoriaProgramatica: '220 0 003', denominacion: 'DEPORTES Y PROMOCIÓN', saldo: 500000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-56', nombreUnidad: 'DEPORTES Y PROMOCIÓN', categoriaProgramatica: '220 0 009', denominacion: 'DEPORTES Y PROMOCIÓN', saldo: 1623175, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '230 0 003', denominacion: 'CULTURA', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '230 0 005', denominacion: 'CULTURA', saldo: 30000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '230 0 007', denominacion: 'CULTURA', saldo: 294935, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '230 0 008', denominacion: 'CULTURA', saldo: 130000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '230 0 009', denominacion: 'CULTURA', saldo: 130000, filasOrigen: 1 },
  { codigoUnidad: 'SD-DDH-57', nombreUnidad: 'CULTURA', categoriaProgramatica: '231 0 004', denominacion: 'CULTURA', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SF-000-39', nombreUnidad: 'GOBIERNO ELECTRÓNICO', categoriaProgramatica: '342 0 021', denominacion: 'GOBIERNO ELECTRONICO', saldo: 250000, filasOrigen: 1 },
  { codigoUnidad: 'SF-DIF-25', nombreUnidad: 'TESORERÍA Y CRÉDITO PÚBLICO', categoriaProgramatica: '099 0 002', denominacion: 'TESORERÍA Y CRÉDITO PÚBLICO', saldo: 6261225, filasOrigen: 1 },
  { codigoUnidad: 'SF-DIF-25', nombreUnidad: 'TESORERÍA Y CRÉDITO PÚBLICO', categoriaProgramatica: '210 0 088', denominacion: 'TESORERÍA Y CRÉDITO PÚBLICO', saldo: 41304, filasOrigen: 1 },
  { codigoUnidad: 'SF-DIF-25', nombreUnidad: 'TESORERÍA Y CRÉDITO PÚBLICO', categoriaProgramatica: '250 0 088', denominacion: 'TESORERÍA Y CRÉDITO PÚBLICO', saldo: 6195553, filasOrigen: 1 },
  { codigoUnidad: 'SF-DIF-25', nombreUnidad: 'TESORERÍA Y CRÉDITO PÚBLICO', categoriaProgramatica: '340 0 088', denominacion: 'TESORERÍA Y CRÉDITO PÚBLICO', saldo: 870969, filasOrigen: 1 },
  { codigoUnidad: 'SF-DIF-25', nombreUnidad: 'TESORERÍA Y CRÉDITO PÚBLICO', categoriaProgramatica: '340 0 097', denominacion: 'TESORERÍA Y CRÉDITO PÚBLICO', saldo: 5000, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRH-26', nombreUnidad: 'ADMINISTRACIÓN Y DESARROLLO DE PERSONAL', categoriaProgramatica: '099 0 001', denominacion: 'ADMINISTRACIÓN DE PERSONAL (SAP)', saldo: 39999, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRH-26-1', nombreUnidad: 'ORGANIZACIÓN Y ADMINISTRATIVA', categoriaProgramatica: '344 0 022', denominacion: 'ORGANIZACIÓN ADMINISTRATIVA SOA', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRH-26-3', nombreUnidad: 'ADMINISTRACIÓN DE PERSONAL', categoriaProgramatica: '341 0 001', denominacion: 'ADMINISTRACIÓN DE PERSONAL SOA', saldo: 364089, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRT-37', nombreUnidad: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', categoriaProgramatica: '300 0 003', denominacion: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', saldo: 162183, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRT-37', nombreUnidad: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', categoriaProgramatica: '301 0 002', denominacion: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRT-37', nombreUnidad: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', categoriaProgramatica: '350 0 003', denominacion: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', saldo: 114753, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRT-37', nombreUnidad: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', categoriaProgramatica: '351 0 002', denominacion: 'ADMINISTRACIÓN DE SERVICIOS MUNICIPALES', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SF-DRT-38', nombreUnidad: 'COBRANZA COACTIVA', categoriaProgramatica: '344 0 024', denominacion: 'RECAUDACIÓN DE TRIBUTOS EN MORA', saldo: 500000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 001', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 002', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 005', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 20000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 010', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 596584, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 019', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 130000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DOP-41', nombreUnidad: 'INFRAESTRUCTURA VIAL Y SEÑALIZACIÓN', categoriaProgramatica: '180 0 037', denominacion: 'PLANTA DE ASFALTO Y SEÑALIZACION VIAL-LABORATORIO', saldo: 80000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 001', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 500000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 002', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 200000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 003', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 700000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 008', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 280000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 009', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 510000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 010', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 30000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 011', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 19000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 013', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 105970, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 020', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 71607, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 023', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 41460.34, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '160 0 024', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 121394, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '161 0 004', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '161 0 005', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 300000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-42', nombreUnidad: 'MANTENIMIENTO DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', categoriaProgramatica: '162 0 005', denominacion: 'MANTENIMIENTO  DE INFRAESTRUCTURA ELÉCTRICA Y SEMAFORIZACIÓN', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SI-DTS-43', nombreUnidad: 'TRANSPORTES Y MAQUINARIA', categoriaProgramatica: '270 0 004', denominacion: 'TRANSPORTES Y MAQUINARIA', saldo: 5404583, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-47', nombreUnidad: 'GESTIÓN DE RIESGOS', categoriaProgramatica: '310 0 006', denominacion: 'GESTIÓN DE RIESGOS', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-47', nombreUnidad: 'GESTIÓN DE RIESGOS', categoriaProgramatica: '310 0 012', denominacion: 'GESTIÓN DE RIESGOS', saldo: 223807, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-47', nombreUnidad: 'GESTIÓN DE RIESGOS', categoriaProgramatica: '311 0 010', denominacion: 'GESTIÓN DE RIESGOS', saldo: 270000, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-48', nombreUnidad: 'PARQUES JARDINES Y SERVICIOS AGROFORESTALES', categoriaProgramatica: '131 0 001', denominacion: 'PARQUES, JARDINES Y SERVICIOS FORESTALES', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-48', nombreUnidad: 'PARQUES JARDINES Y SERVICIOS AGROFORESTALES', categoriaProgramatica: '131 0 010', denominacion: 'PARQUES, JARDINES Y SERVICIOS FORESTALES', saldo: 3643046, filasOrigen: 1 },
  { codigoUnidad: 'SM-000-48', nombreUnidad: 'PARQUES JARDINES Y SERVICIOS AGROFORESTALES', categoriaProgramatica: '132 0 022', denominacion: 'PARQUES, JARDINES Y SERVICIOS FORESTALES', saldo: 70000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '100 0 008', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 160980, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 010', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 10000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 013', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 30000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 016', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 140000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 017', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 40000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 019', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 40000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 020', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 230000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '101 0 025', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 82958.3, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '102 0 012', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 30000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '102 0 018', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 80000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '103 0 004', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 213400, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '104 0 001', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 70000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '104 0 003', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 41274, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49', nombreUnidad: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', categoriaProgramatica: '104 0 004', denominacion: 'FORTALECIMIENTO Y DESARROLLO PRODUCTIVO', saldo: 20000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-49-3', nombreUnidad: 'CENTRO MUNICIPAL DE SEMILLAS Y BIOINSUMOS', categoriaProgramatica: '101 0 015', denominacion: 'CENTRO MUNICIPAL DE SEMILLAS Y BIOINSUMOS', saldo: 632112, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-50', nombreUnidad: 'TURISMO', categoriaProgramatica: '240 0 002', denominacion: 'TURISMO', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-50', nombreUnidad: 'TURISMO', categoriaProgramatica: '240 0 004', denominacion: 'TURISMO', saldo: 168794, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-50', nombreUnidad: 'TURISMO', categoriaProgramatica: '240 0 005', denominacion: 'TURISMO', saldo: 80000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-51', nombreUnidad: 'MATADERO', categoriaProgramatica: '290 0 004', denominacion: 'MATADERO', saldo: 181636, filasOrigen: 1 },
  { codigoUnidad: 'SM-DDP-51', nombreUnidad: 'MATADERO', categoriaProgramatica: '291 0 002', denominacion: 'MATADERO', saldo: 40000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DMA-44', nombreUnidad: 'CONTROL AMBIENTAL', categoriaProgramatica: '130 0 010', denominacion: 'CONTROL AMBIENTAL', saldo: 178493, filasOrigen: 1 },
  { codigoUnidad: 'SM-DMA-44', nombreUnidad: 'CONTROL AMBIENTAL', categoriaProgramatica: '140 0 001', denominacion: 'CONTROL AMBIENTAL', saldo: 3500000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DMA-45', nombreUnidad: 'LICENCIAS AMBIENTALES', categoriaProgramatica: '130 0 016', denominacion: 'LICENCIAS AMBIENTALES', saldo: 30000, filasOrigen: 1 },
  { codigoUnidad: 'SM-DMA-46', nombreUnidad: 'AREAS PROTEGIDAS Y BIODIVERSIDAD', categoriaProgramatica: '133 0 001', denominacion: 'AREAS PROTEGIDAS Y BIODIVERSIDAD', saldo: 183726, filasOrigen: 1 },
  { codigoUnidad: 'SP-DCM-22', nombreUnidad: 'CATASTRO MULTIFINALITARIO', categoriaProgramatica: '191 0 001', denominacion: 'CATASTRO MULTIFINALITARIO', saldo: 903974, filasOrigen: 1 },
  { codigoUnidad: 'SP-DGU-20', nombreUnidad: 'GESTIÓN URBANA MUNICIPAL', categoriaProgramatica: '190 0 005', denominacion: 'SERVICIOS DE URBANISMO-ARCHIVOS DE URBANISMO', saldo: 40000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DGU-21-2', nombreUnidad: 'SANEAMIENTO DE BIENES INMUEBLES MUNICIPALES', categoriaProgramatica: '170 0 018', denominacion: 'SANEAMIENTO DE BIENES INMUEBLES MUNICIPALES', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DGU-21-2', nombreUnidad: 'SANEAMIENTO DE BIENES INMUEBLES MUNICIPALES', categoriaProgramatica: '170 0 051', denominacion: 'SANEAMIENTO DE BIENES INMUEBLES', saldo: 451430, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '111 0 009', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 60152.3, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 001', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 350000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 004', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 532878.77, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 006', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 213690, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 010', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 540000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 014', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 542449, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 016', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 284863.98, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 025', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 757050, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '120 0 026', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '131 0 018', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 125000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '131 0 025', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 990000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 001', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 002', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 027', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 125910, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 041', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 130000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 048', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 80000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 049', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '170 0 060', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '171 0 020', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '180 0 007', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 247202, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '212 0 010', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 150000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '222 0 007', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 100000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '222 0 020', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 38500, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '222 0 022', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 850000, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '301 0 004', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 143214, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-17', nombreUnidad: 'DISEÑO DE PROYECTOS DE PREINVERSION', categoriaProgramatica: '344 0 016', denominacion: 'PROYECTOS DE PRE-INVERSION', saldo: 493226, filasOrigen: 1 },
  { codigoUnidad: 'SP-DPD-19', nombreUnidad: 'PROGRAMACIÓN DE OPERACIONES Y SEGUIMIENTO POA', categoriaProgramatica: '097 0 001', denominacion: 'PROGRAMACIÓN DE OPERACIONES Y SEGUIMIENTO  POA', saldo: 51003766.93, filasOrigen: 16 },
  { codigoUnidad: 'SS-DAS-58', nombreUnidad: 'ADMINISTRATIVO HOSPITAL SOLOMON KLEIN', categoriaProgramatica: '201 0 003', denominacion: 'ADMINISTRATIVO HOSPITAL SOLOMON KLEIN', saldo: 8335946, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-59', nombreUnidad: 'ADMINISTRATIVO HOSPITAL MÉXICO', categoriaProgramatica: '201 0 002', denominacion: 'ADMINISTRATIVO HOSPITAL MEXICO', saldo: 8239236, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '200 0 099', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 33750034, filasOrigen: 3 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '200 0 150', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 4500, filasOrigen: 3 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 001', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 11827231, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 004', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 9623308, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 005', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 200000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 008', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 200000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 011', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 90000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60', nombreUnidad: 'ADMINISTRATIVO DE PROGRAMAS Y ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', categoriaProgramatica: '201 0 014', denominacion: 'ESTABLECIMIENTOS DE SALUD DE 1º NIVEL', saldo: 360000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 001', denominacion: 'PROGRAMAS DE SALUD', saldo: 170000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 002', denominacion: 'PROGRAMAS DE SALUD', saldo: 53000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 003', denominacion: 'PROGRAMAS DE SALUD', saldo: 1520695, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 005', denominacion: 'PROGRAMAS DE SALUD', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 006', denominacion: 'PROGRAMAS DE SALUD', saldo: 50000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-60-3', nombreUnidad: 'PROGRAMAS DE SALUD', categoriaProgramatica: '204 0 007', denominacion: 'PROGRAMAS DE SALUD', saldo: 20000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-61-1', nombreUnidad: 'FARMACIA INSTITUCIONAL MUNICIPAL', categoriaProgramatica: '203 0 001', denominacion: 'FARMACIA (FIM)', saldo: 1800000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-62', nombreUnidad: 'CONTROL SANITARIO Y ZOONOSIS', categoriaProgramatica: '204 0 004', denominacion: 'CONTROL SANITARIO Y ZOONOSIS', saldo: 856685, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-63-1', nombreUnidad: 'MANTENIMIENTO DE ESTABLECIMIENTOS DE SALUD', categoriaProgramatica: '202 0 001', denominacion: 'MANTENIMIENTO DE ESTABLECIMIENTOS DE SALUD', saldo: 300000, filasOrigen: 1 },
  { codigoUnidad: 'SS-DAS-63-1', nombreUnidad: 'MANTENIMIENTO DE ESTABLECIMIENTOS DE SALUD', categoriaProgramatica: '202 0 006', denominacion: 'MANTENIMIENTO DE ESTABLECIMIENTOS DE SALUD', saldo: 82401, filasOrigen: 1 },
];

/** Índice `codigoUnidad` → sus categorías, armado una sola vez. */
const POR_UNIDAD = SALDOS_UNIDAD_CATEGORIA.reduce((mapa, s) => {
  const lista = mapa.get(s.codigoUnidad);
  if (lista) { lista.push(s); } else { mapa.set(s.codigoUnidad, [s]); }
  return mapa;
}, new Map<string, SaldoUnidadCategoria[]>());

/** Las categorías con saldo de una unidad, o vacío si no figura en la planilla. */
export function saldosDeUnidad(codigoUnidad: string): SaldoUnidadCategoria[] {
  return POR_UNIDAD.get((codigoUnidad || '').trim()) ?? [];
}

/**
 * El saldo de una categoría dentro de una unidad.
 *
 * Devuelve `null` —y no cero— cuando el par no está en la planilla: no es lo
 * mismo «no hay nada disponible» que «esta combinación no fue revisada».
 */
export function saldoDisponible(
  codigoUnidad: string, categoriaProgramatica: string,
): number | null {
  const categoria = (categoriaProgramatica || '').trim();
  const entrada = saldosDeUnidad(codigoUnidad)
    .find(s => s.categoriaProgramatica === categoria);
  return entrada ? entrada.saldo : null;
}
