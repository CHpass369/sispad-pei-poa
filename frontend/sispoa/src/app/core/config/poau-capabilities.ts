/**
 * Capacidades que habilitan las tres pantallas POAU de una unidad:
 * `/sis-poa/poaus` (Matriz), `/poau` (Físico) y `/poau_recursos` (Recursos).
 *
 * Existen porque `sis_poa.formulate` no sirve para gobernarlas: esa capacidad
 * también abre Presupuesto de Gastos, Presupuesto de Recursos, el Dashboard
 * POA, Priorización POA y el POA completo. Un encargado o validador de POAU
 * necesita entrar a las tres pantallas de su unidad SIN que eso le entregue el
 * resto de SIS-POA, así que las rutas y el menú se clavan acá.
 *
 * El alcance territorial no vive en esta lista: lo aplica el backend con
 * `ScopeResolver` sobre `AlcanceOrganizacional`. Estas capacidades deciden
 * QUÉ pantalla se ve; el alcance decide DE QUÉ unidad son los datos.
 */
export const POAU_CAPABILITIES = [
  'sis_poa.poau.view',
  'sis_poa.poau.create',
  'sis_poa.poau.edit',
  'sis_poa.poau.submit',
  'sis_poa.poau.review',
  'sis_poa.poau.approve',
];
