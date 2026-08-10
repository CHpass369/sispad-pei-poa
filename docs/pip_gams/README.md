# PIP-GAMS — Documentación de arquitectura

Documentación de la Plataforma Integral de Planificación del GAM Sacaba
(SIS-PE + SIS-POA + SIS-PRO sobre núcleo transversal).

## Documentos

| Documento | Contenido |
|---|---|
| [Glosario](glosario.md) | Nomenclatura oficial: PIP-GAMS, SIS-PE/SIS-POA/SIS-PRO, conceptos y reglas de naming |
| [Domain Map](domain_map.md) | Equivalencias de los 68 modelos legacy → destino V2 |
| [Política de metodologías](politica_metodologias.md) | Versiones de metodología, estados y semver |
| [ADR-001](adr/ADR-001-base-unica.md) | Base de datos única PostgreSQL/PostGIS |
| [ADR-002](adr/ADR-002-api-v2.md) | API V2 con namespaces por sistema |
| [ADR-003](adr/ADR-003-iam.md) | IAM: identidad OIDC + autorización por capacidades |
| [ADR-004](adr/ADR-004-migracion.md) | Estrategia Expand/Migrate/Contract + LegacyMigrationMap |
| [WP-00 baseline](../pip_gams/WP00_baseline.md) | Estado congelado y verificado de partida |

## Estado de work packages

| WP | Nombre | Estado |
|---|---|---|
| WP-00 | Baseline reproducible | ✅ Completado |
| WP-01 | Glosario, domain map y ADRs | ✅ Completado |
| WP-02 | API namespaces `/api/v2/` | ✅ Completado |
| WP-03 | IAM capabilities + menú dinámico | ✅ Completado |
| WP-04 | Kernel estratégico V2 (modelos) | ✅ Completado |
| WP-05 | LegacyMigrationMap + dry-run | ✅ Completado |
| WP-06 | Importación PGDESA/PDESA | ✅ Completado |
| WP-07 | Migración PAD | ✅ Completado |
| WP-08 | Workflow, evaluación y ajustes SIS-PE | ✅ Completado |
| WP-09 | Frontend SIS-PE V2 y corte | ✅ Completado (módulo SIS-PE + menú por capacidades) |
| WP-10 | SIS-POA V2 | ✅ Completado (jerarquía canónica + importación) |
| WP-11 | SIS-PRO V2 | ✅ Completado (ciclo del proyecto + trazabilidad) |
| WP-12 | Infraestructura y servicios | ✅ Completado (health, beat, logging, pinning, Keycloak separado) |
| WP-13 | Calidad, rendimiento y seguridad | ✅ Completado (N+1, E2E, cobertura, restauración ensayada) |
