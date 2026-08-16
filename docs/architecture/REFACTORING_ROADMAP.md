# Roadmap de Refactorización del PIP-GAMS

Plan por fases para estabilizar el PIP-GAMS hacia la arquitectura TO-BE (`PIP_SYSTEM_MAP.md`). Reglas: un bounded context a la vez; ciclo `AUDIT → TASK → PLAN → BUILD → TEST → REVIEW → COMMIT`; nunca big-bang; nada se retira antes de un cutover probado. IDs de tareas: `PIP-XXX-nnn` referencian `tasks/backlog`.

## Fase 0 — Gobernanza (en curso, bootstrap ETAPA B)

| Aspecto | Contenido |
|---|---|
| Objetivo | Fijar la base documental de gobernanza: AS-IS, dominios, ownership, contratos, roadmap |
| Tareas | PIP-GOV-001: este bootstrap (11 documentos en docs/architecture/); PIP-GOV-002: revisar y aprobar DOMAIN_BOUNDARIES y DATA_OWNERSHIP con el equipo |
| Criterios de salida | Documentos aprobados; todos los hallazgos críticos triageados en tasks/backlog |
| Riesgos | Que la gobernanza quede en papel sin tareas asignadas |

## Fase 1 — CORE stabilization

| Aspecto | Contenido |
|---|---|
| Objetivo | Core estable y sin dependencias de negocio |
| Tareas | PIP-CORE-101: fix doble prefijo organizacion (F-1); PIP-CORE-102: eliminar imports de PlanAnual (F-2); PIP-CORE-103: quitar dependencias de negocio de core (dashboard/validators) — mover a servicios por dominio; PIP-CORE-104: FKs genéricas → FK reales o tablas de vínculo (F-8); PIP-CORE-105: limpiar PermissionsService/getRefreshToken/TablaGenericaComponent (F-16); PIP-CORE-106: CapabilityGuard en rutas legacy (F-18) |
| Criterios de salida | core no importa modelos de negocio; 1252 tests + nuevos pasan; V1 Sunset intacto |
| Riesgos | El ciclo latente obliga a coordinar con todas las apps |

## Fase 2 — SIS-PE stabilization

| Aspecto | Contenido |
|---|---|
| Objetivo | Instrumentos V2 canónicos; articulación contractual |
| Tareas | PIP-PE-201: kernel V2 instrumentos como único escritor (D7); PIP-PE-202: unificar cadena operativa hacia poau V2 (F-4) — congelar escrituras en articulacion_*/indicadores_*; PIP-PE-203: lineamiento PAD → codificacion canónico (D3); PIP-PE-204: strings de catálogo en articulacion → FK (F-10) |
| Criterios de salida | SIS-PE no escribe cadenas operativas ajenas; articulacion lee catálogos por FK |
| Riesgos | La cadena operativa es consumida por 4 apps: orden de migración estricto |

## Fase 3 — SIS-POA stabilization

| Aspecto | Contenido |
|---|---|
| Objetivo | Presupuesto V2 (budget) único; legacy congelado |
| Tareas | PIP-POA-301: designar techo canónico y congelar escrituras techos V1 (F-3/D1); PIP-POA-302: categoría programática única (D2); PIP-POA-303: reformas únicas (D8); PIP-POA-304: FK de gestión fiscal en las 12 apps (F-5/O-1); PIP-POA-305: dividir monolitos budget (F-12) — models/views/services por concepto |
| Criterios de salida | Un único par techo/distribución/asignación en V2; gestión con FK |
| Riesgos | El frontend legacy de techos/presupuesto debe migrar en paralelo (F-13) |

## Fase 4 — SIS-PRO stabilization

| Aspecto | Contenido |
|---|---|
| Objetivo | Proyecto V2 único; preinversión integrada |
| Tareas | PIP-PRO-401: proyecto V2 como único escritor (D5); PIP-PRO-402: contrato presupuesto aprobado → proyectos (C-10); PIP-PRO-403: fuentefinanciamientoedtp → FK catalogo (C-11); PIP-PRO-404: extender EventoOutbox a ejecución |
| Criterios de salida | SIS-PRO sin imports directos a presupuesto; outbox en ciclo completo |
| Riesgos | Ejecución financiera requiere contrato bidireccional con SIS-POA (C-12) |

## Fase 5 — Cross-domain integration

| Aspecto | Contenido |
|---|---|
| Objetivo | Contratos formales y corte V1→V2 |
| Tareas | PIP-X-501: implementar contratos C-1..C-12 (INTEGRATION_CONTRACTS.md); PIP-X-502: reportes leen vía servicios, no modelos directos; PIP-X-503: migrar frontend de V1 a V2 (F-7); PIP-X-504: cutover de features legacy (presupuesto/techos/modificaciones frontend) |
| Criterios de salida | Frontend 100% V2; cero consumidores de V1 salvo ventana de Sunset |
| Riesgos | El mayor: cutover del frontend; requiere ventanas por feature |

## Fase 6 — Hardening

| Aspecto | Contenido |
|---|---|
| Objetivo | Calidad de ingeniería |
| Tareas | PIP-H-601: CI/CD (F-9); PIP-H-602: make targets corregidos (test-backend alineado a pytest.ini, test-frontend real); PIP-H-603: tsconfig strict:true + strictTemplates:true (F-13); PIP-H-604: specs en 28 features sin cobertura (F-14); PIP-H-605: dependencias muertas removidas (F-17) |
| Criterios de salida | CI verde en cada PR; strict activo; cobertura frontend por feature |
| Riesgos | strict:true genera oleada de fixes: hacer por feature |

## Fase 7 — Production readiness

| Aspecto | Contenido |
|---|---|
| Objetivo | Despliegue productivo confiable |
| Tareas | PIP-PROD-701: environment.prod.ts real (F-15); PIP-PROD-702: observabilidad (logs, métricas, alertas); PIP-PROD-703: retiro físico de tablas post-cutover probado (cero DeleteModel hasta aquí); PIP-PROD-704: backup/restore verificado; PIP-PROD-705: estrategia Keycloak/OIDC decidida |
| Criterios de salida | Deploy reproducible, monitoreado, con rollback probado |
| Riesgos | Retiro físico rompe queries externas: solo tras ventana de convivencia |

## Reglas transversales

1. Un bounded context a la vez; fases 1-4 son secuenciales, 5-7 pueden solaparse al final de cada una.
2. Ciclo por tarea: AUDIT → TASK → PLAN → BUILD → TEST → REVIEW → COMMIT.
3. Nunca big-bang; nada se retira antes de cutover probado.
4. Toda duplicación nueva queda prohibida por DATA_OWNERSHIP; las existentes se resuelven en su fase.
5. Cada fase cierra con contrato actualizado y sin deuda nueva (DONE según AGENTS.md).

## Referencias

- `docs/refactor-pip/FINAL_REPORT.md`, `docs/refactor-pip/ARQUITECTURA_OBJETIVO.md`, `docs/refactor-pip/LEGACY_DEPRECATION.md`.
- `docs/refactor-pip/ADR/ADR-001..ADR-010`, `docs/pip_gams/WP14_retiro_legacy.md`.
- `tasks/backlog` — backlog de tareas (IDs PIP-XXX-nnn).
- Complementos: `docs/architecture/PIP_AUDIT_REPORT.md` (hallazgos F-1..F-19), `DUPLICATION_ANALYSIS.md` (D1-D18), `INTEGRATION_CONTRACTS.md` (C-1..C-12).

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.
