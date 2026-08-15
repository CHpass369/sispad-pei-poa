# ADR-010 — Estrategia de migración incremental SISPOA → PIP

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-003, ADR-009; plan maestro §2.2, §20, §21, §32; `AUDITORIA_SISPOA.md` §6

## Contexto

El proyecto es un sistema en producción (dominio `sispoa.gamsacaba.gob.bo`, BD `gams_sis_poa` con 217 tablas, 92 migraciones aplicadas, frontend Angular 19 compilado en `static_assets`), con datos históricos sensibles (importaciones `SISPOA_GASTOS_*`, reformulaciones con `sistema_origen='SISPOA'`, documentos oficiales impresos) y consumidores internos que no pueden dejar de operar. El plan maestro §32 fija la estrategia: "preservar → normalizar → versionar → migrar → validar → cortar → retirar", sin reconstrucción desde cero y sin big-bang. Cualquier enfoque que renombre todo de una vez, mueva apps masivamente o elimine compatibilidad antes de validar consumidores destruye datos o detiene la operación.

## Decisión

La migración es incremental, por capas y con compatibilidad temporal, en este orden:

1. **Auditoría → mapa**: inventario clasificado de referencias, arquitectura actual, mapa de dominios y mapeo de esquemas (Fase 1 ya completada: `AUDITORIA_SISPOA.md`, `ARQUITECTURA_ACTUAL.md`, `DOMAIN_MAP.md`, `SCHEMA_MAPPING.md`).
2. **Identidad**: rename semántico de la identidad visible de plataforma (PIP) por capa y sin replace global (ADR-001).
3. **Core**: núcleo transversal e IAM primero (capacidades, alcances, `me/capabilities`, autorización backend uniforme), independiente de cada SIS (plan maestro FASE 2).
4. **Bounded contexts**: SIS-PE V2 primero (kernel estratégico genérico), luego SIS-POA V2 (jerarquía canónica única + ciclo presupuestario V2), luego SIS-PRO V2 (evolución de `inversion`), según el orden de fases del plan maestro (3-11).
5. **Frontend**: cutover V2 por dominio con la palanca `LEGACY_MENU_VISIBLE` y etiqueta "V1" en el menú; las rutas legacy siguen accesibles por URL hasta su retiro (reversible).
6. **APIs**: `/api/v1/` se mantiene temporalmente con deprecación escalonada (header `Deprecation`, luego 404 tras ventana); V2 es el contrato estable.
7. **Datos**: migración por grupos con backup, MIGRATE + VALIDATE por grupo y esquemas objetivos (ADR-003, `DATA_MIGRATION_PLAN.md`); valores de datos protegidos con coexistencia (KEEP) hasta la fase de datos.
8. **Tests**: suites de contrato V2 (`backend/tests/`) y reconciliación de registros como condición para retirar cualquier legacy (plan maestro §20, FASE 14).
9. **Legacy**: deprecación escalonada con validación de consumidores; infraestructura (BD, Docker, Keycloak, MinIO, DNS) en planes dedicados con ventanas (`LEGACY_DEPRECATION.md`).
10. **Preservación**: datos y funcionalidad intactos en cada paso; rollback definido por grupo; NUNCA `DROP SCHEMA ... CASCADE` al inicio.

## Consecuencias

Positivas:

- El sistema permanece operativo durante todo el refactor: cada fase entrega valor sin ventana de detención (salvo el REMOVE LEGACY, planificado).
- El riesgo se acota por grupo: un fallo de migración afecta un dominio, no la plataforma.
- La compatibilidad temporal permite medir consumidores reales antes de retirar cada referencia legacy.

Negativas:

- El período de convivencia legacy/V2 duplica temporalmente conceptos y exige disciplina (prohibido crear una tercera representación; plan maestro §2.2).
- El refactor es largo y de mantenimiento constante: cada fase exige tests, reconciliación y documentación (Definition of Done del plan maestro §29).
- Los renames de infraestructura quedan al final y dependen de ventanas de despliegue externas (DNS, Keycloak), no del ritmo del código.

## Alternativas consideradas

1. **Reescritura desde cero (greenfield PIP)**: descartada por el plan maestro §32: pierde 200 modelos, 217 tablas y datos históricos sin valor equivalente.
2. **Big-bang (migración total en una ventana)**: descartado: riesgo inaceptable de pérdida de datos y de detención prolongada del servicio; contradice el plan maestro §3.13.
3. **Renombrar masivamente apps y tablas al inicio**: descartado por el plan maestro §5.1: los app labels y migraciones son el estado histórico de la base; se reorganizan primero los límites, servicios y contratos.
