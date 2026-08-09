# ADR-001 — Base de datos única PostgreSQL/PostGIS

- **Estado:** Aprobado (WP-01)
- **Fecha:** 2026-08-09
- **Decisores:** Arquitectura PIP-GAMS

## Contexto

PIP-GAMS albergará SIS-PE, SIS-POA y SIS-PRO con fuerte consistencia
transaccional y trazabilidad entre cadenas estratégica, operativa y de
proyectos (nodo → POA → proyecto → seguimiento). Se consideró separar bases
por SIS.

## Decisión

**Una sola base PostgreSQL/PostGIS principal para PIP-GAMS.**

- Durante el refactor inicial se conserva el esquema físico existente.
- La separación principal es por apps/tablas/servicios.
- Separación por schemas PostgreSQL se evalúa solo después de estabilizar V2
  (analítica, publicación o integraciones); no es requisito.
- **Keycloak/OIDC usa base/esquema y credenciales separados** de los datos de
  negocio (misma instancia PostgreSQL, base propia).

## Consecuencias

- Migraciones Django unificadas y transaccionales entre dominios.
- Consultas de trazabilidad directas (sin ETL entre bases).
- Mayor disciplina de modelado para no acoplar dominios (contratos por
  servicios/selectors).
- Riesgo de contención de recursos mitigado con índices, selectors y
  materialized views para dashboards pesados.

## Alternativas descartadas

- Una base por SIS: rompe trazabilidad transaccional y duplica catálogos.
- Microservicios con bases propias: descartado en esta etapa (principio §3.16
  del plan maestro).
