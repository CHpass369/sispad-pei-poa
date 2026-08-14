/**
 * Palanca de cutover V2 → retiro gradual del legacy (ADR-004 / WP-14).
 *
 * Controla la visibilidad de los ítems del menú marcados `legacy: true`.
 * Girar una ruta a `false` oculta su módulo V1 del menú cuando el dominio
 * ya está cubierto por la UI V2. Las rutas siguen existiendo (solo se
 * ocultan del menú; el acceso directo por URL sigue disponible), por lo
 * que el cambio es reversible y de bajo riesgo.
 *
 * Default: TODO visible (comportamiento histórico). El roadmap de retiro
 * del WP-14 define el orden por dominio:
 *
 *   1. planificacion legacy     → cuando SIS-PE V2 cubra PAD/PEI/Articulación
 *   2. pad + articulacion       → cuando la reconciliación PAD esté al 100%
 *   3. indicadores              → cuando la jerarquía canónica V2 esté operativa
 *   4. poau                     → cuando el cutover SIS-POA esté completo
 *   5. inversion                → cuando la cartera V2 sea la oficial
 *   6. resto de V1              → cutover completo + periodo de observación
 */
export const LEGACY_MENU_VISIBLE: Record<string, boolean> = {
  // SIS-PE
  '/articulador': true,
  '/articulacion': true,
  '/indicadores': true,
  '/territorio': true,
  '/evaluacion': true,
  // SIS-POA
  '/poau': true,
  '/recursos': true,
  '/planificacion/formulacion': true,
  '/seguimiento': true,
  '/modificaciones': true,
  '/consolidacion': true,
  // SIS-PRO
  '/inversion': true,
};
