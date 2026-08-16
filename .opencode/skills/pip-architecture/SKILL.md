---
name: pip-architecture
description: "Use when: arquitectura PIP, bounded contexts, dominios, dependencias, ownership, integración por contratos, modularidad, acoplamiento, ADRs. Reglas de arquitectura de la Plataforma Integral de Planificación (GAM Sacaba)."
---

# Arquitectura PIP

Guía de arquitectura de PIP (Django 6/DRF + Angular 21 + PostgreSQL 17/PostGIS). Referencia normativa: `docs/architecture/*.md` (PIP_SYSTEM_MAP, DOMAIN_BOUNDARIES, DATA_OWNERSHIP, INTEGRATION_CONTRACTS, DUPLICATION_ANALYSIS, MODULE_INVENTORY, DATA_MODEL_AS_IS, DEPENDENCY_MAP, AS_IS_ARCHITECTURE, PIP_AUDIT_REPORT, REFACTORING_ROADMAP) e histórico en `docs/refactor-pip/`.

## Bounded contexts

| Dominio | Apps backend | Features frontend |
|---|---|---|
| CORE | core, accounts, organizacion, territorio, workflow, documentos, notificaciones, auditoria, reportes, acciones_correctivas, normativa | auth, admin-usuarios, auditoria, documentos, gestion, normativa, notificaciones, organizacion, reportes, sistemas, workflow, dashboard |
| SHARED/INFRA | catalogos, codificacion | catalogos |
| SIS-PE | planificacion, pad, articulacion, evaluacion, indicadores | sis-pe, articulacion, matrices-pad, pad, indicadores, territorio, evaluacion, consolidacion, portal-publico |
| SIS-POA | gestion, budget, poau, recursos, techos, presupuesto, modificaciones, seguimiento | sis-poa (+budget), planificacion, poau, presupuesto, techos, recursos, seguimiento, modificaciones |
| SIS-PRO | inversion | inversion, sis-pro |

## Reglas de dependencia

- CORE es la base: SIS-PE, SIS-POA y SIS-PRO dependen de CORE. CORE NUNCA depende de la lógica de los sistemas.
- SHARED (catalogos, codificacion) es usado por todos; no depende de ningún sistema.
- Entre sistemas: integración por CONTRATOS (Dominio → Application service → Contrato → otro dominio), nunca acceso indiscriminado a tablas de otro dominio.
- La integración SIS-PE→SIS-POA se realiza por articulación (motor articulacion), SIS-POA→SIS-PRO por vínculos (vinculoproyectoactividad → poau_actividad).

## Reglas de modularidad

- Nuevos desarrollos: API V2 por dominios `/api/v2/{platform,core,catalogos,geo,integracion,auditoria,sis-pe,sis-poa,budget,sis-pro,me}/`. API V1 es legacy (Sunset 2027-01-01).
- SEARCH BEFORE CREATE: ante cualquier nuevo componente, busca el equivalente (grep, codegraph, DUPLICATION_ANALYSIS.md). Prefiere REUSE → EXTEND → LOCAL REFACTOR.
- No renombrar ni borrar tablas sin tarea aprobada (el renombrado masivo del 15-08-2026 ya rompió queries externas).
- Techos, distribuciones y asignaciones son funcionalidades de SIS-POA, no sistemas independientes.

## Decisiones

Documentar ADRs en `docs/adr/` (ver ADR_TEMPLATE.md). Distinguir siempre ESTADO ACTUAL (AS_IS) de ARQUITECTURA OBJETIVO (ver docs/refactor-pip/ARQUITECTURA_OBJETIVO.md).
