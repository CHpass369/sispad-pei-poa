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

## FINAL REPORT

Decisión 2021/2025 (creadas o excluidas, con evidencia), tablas migradas, contratos verificados.