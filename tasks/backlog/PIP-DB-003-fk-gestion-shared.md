# TASK PIP-DB-003: FK gestión fiscal — SHARED (catalogos, codificacion)

## DOMINIO

`shared` (catalogos, codificacion)

## OBJECTIVE

Fase 2: convertir los campos `gestion` de SHARED a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Requiere data migration: `codificacion.VersionCatalogoPlan` tiene años huérfanos **2021 y 2025** (6 filas). `catalogos.CatalogoBase` es abstracto → la FK afecta 13 subclases.

## SCOPE

- Apps: `catalogos` (VersionClasificador, CatalogoBase→13 subclases, VersionCatalogo), `codificacion` (VersionCatalogoPlan, SecuenciaCodigo, HomologacionCodigo, EjecucionMigracionSIM).
- Data migration (solo si la gestión es real): decidir por evidencia si 2021/2025 deben crearse como `GestionFiscal` o excluirse. **Prohibido inventar gestiones falsas** para satisfacer la FK.
- Migración por app: integer → FK `PROTECT`.

## OUT OF SCOPE

- Otros dominios (PIP-DB-002, 004-007).
- Codificación normativa sin API: confirmar que no rompe `articulacion`.

## INVARIANTS

- `GestionFiscal` canónica intacta.
- CatalogoBase migrado en una sola tarea (impacto 13 tablas).

## DATABASE IMPACT

Data migration (VersionCatalogoPlan) + FKs por app. Índices existentes sobre `gestion` se conservan.

## API IMPACT

`/api/v2/catalogos/` serializers: `gestion` entero pasaría a `gestion` (id UUID) — revisar contratos.

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §4 (huérfanos), §6 (PROTECT).

## ROLLBACK

Reversa de data migration (restaurar enteros) + FKR.

## DECISIÓN DE DOMINIO (2026-08-16, §4.1 GESTION_FISCAL_AUDIT)

Los años huérfanos **2021/2025 de `codificacion.VersionCatalogoPlan` NO son gestiones fiscales**: son versiones oficiales de catálogos de los planes `PDES-2021-2025` y `PGDES-AP2025` (año de vigencia del plan). **NO se crea GestionFiscal** para ellos → `VersionCatalogoPlan.gestion` **NO se FK-iza** (excepción plurianual gobernada; regla escrita en el modelo). El resto de SHARED (CatalogoBase→13 subclases, VersionCatalogo, clasificadores) no tiene huérfanos → FK directa.

## FINAL REPORT

Decisión 2021/2025 (creadas o excluidas, con evidencia), tablas migradas, contratos verificados.