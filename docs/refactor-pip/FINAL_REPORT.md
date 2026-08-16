# Informe Final del Refactor SISPOA a PIP

**Plataforma:** PIP (Plataforma de Instrumentos de Planificación) — GAM Sacaba
**Documento:** Resumen ejecutivo del refactor SISPOA a PIP
**Estado:** Completado (10 fases, commits verificados)
**Fecha:** 15 de agosto de 2026

Este documento consolida el trabajo realizado entre las fases 1 y 10 del refactor
SISPOA a PIP. Cada fase tuvo commits reales, verificaciones (tests, build,
`manage.py check`) y documentación de frontera en `docs/refactor-pip/`.

---

## 1. Qué existía

- Proyecto construido alrededor de la identidad **"SISPOA"**: Django (`apps/*`) +
  Angular (`frontend/sispoa`) + PostgreSQL 16 + PostGIS 3.4.0.
- Base de datos `gams_sis_poa` en esquema `public`.
- Identidad visible de SISPOA en login, title, sidebar, admin y emails.
- API V1 plana + API V2 parcial con namespaces `platform`, `sis-pe`, `sis-poa`,
  `sis-pro`.
- Sin delimitación explícita de bounded contexts: las apps convivían bajo una
  única identidad de plataforma.

## 2. Qué se encontró (hallazgos de la auditoría)

- Barrido exhaustivo de la Fase 1: **162 archivos y 865 referencias** a SISPOA.
- 4 documentos de auditoría generados:
  - `AUDITORIA_SISPOA.md` (inventario de referencias).
  - `ARQUITECTURA_ACTUAL.md` (estructura del sistema al momento de la auditoría).
  - `DOMAIN_MAP.md` (mapa de dominio).
  - `SCHEMA_MAPPING.md` (**217 tablas mapeadas**).
- Colisión real de nombres detectada y corregida: `VinculoViewSet` compartido por
  `sis-pe/vinculos` y `sis-pro/vinculos`.
- APIs V1 sin headers de deprecación ni ciclo de vida definido.
- Código acoplado de articulación (`CodigoSegmentadoModel`, `CodificadorService`
  de 16 segmentos) que no debía moverse — decisión registrada en ADR-004/ADR-010.

## 3. Qué se refactorizó (por fase, con commits)

| # | Fase | Commit | Resumen |
|---|------|--------|---------|
| 1 | Auditoría | `0f45829` | Barrido completo: 162 archivos, 865 referencias, 4 docs, 217 tablas mapeadas. |
| 2 | PIP CORE / identidad | `3400e22` | Identidad visible SISPOA a PIP en 11 archivos (login, title, sidebar, header, admin, emails, docstrings); docs de diseño: `ARQUITECTURA_OBJETIVO.md` (6 diagramas Mermaid), `DATA_MIGRATION_PLAN.md`, `LEGACY_DEPRECATION.md`, ADR/001-010. |
| 3 | SIS-PE | `776dba5` | AppConfigs `planificacion` ("SIS-PE - Planificación Estratégica"), `pad` ("SIS-PE - PAD"), `codificacion` ("PIP Catálogos"); command `importar_pei` (metodología MET-PEI-OFICIAL, tipos OE/RI/PI); `SIS_PE_BOUNDED_CONTEXT.md`. |
| 4 | SIS-POA | `863e516` | 9 AppConfigs (`gestion`, `budget`, `poau`, `modificaciones`, `seguimiento`, `indicadores`, `recursos`, `techos` [legacy], `presupuesto` [legacy]); `SIS_POA_BOUNDED_CONTEXT.md`. |
| 5 | PIP INTEGRACIÓN | `9ac64da` | `MotorArticulacion` (`apps/articulacion/services/motor.py` — `cadena_descendente`, `cadena_ascendente`, `trazar_instrumento`); AppConfig `articulacion` "PIP INTEGRACIÓN - Articulación"; `services.py` convertido a paquete; `PIP_INTEGRACION_BOUNDED_CONTEXT.md`. |
| 6 | SIS-PRO | `36e6bf4` | AppConfig `inversion` "SIS-PRO - Ciclo de Proyectos"; correcciones semánticas SISPOA a SIS-POA en `inversion` (8); `IntegracionPoaContract` (`apps/inversion/services/integracion_poa.py`); migración `0006`; `SIS_PRO_BOUNDED_CONTEXT.md`. |
| 7 | Frontend | `b6a9ddd` | `package.json` `pip-sacaba`; botón "Enviar a SIS-POA" en SIS-PRO. |
| 8 | APIs | `ed87ef0` | 42 rutas V2 nuevas: `/api/v2/core/` (5), `/api/v2/catalogos/` (13), `/api/v2/geo/` (3), `/api/v2/integracion/` (11 + matrices), `/api/v2/auditoria/` (1); `API_MAPPING.md`. |
| 9 | Tests | `0b45875` | `test_flujo_estrategico.py` (4 tests: cadena PAD a PEI a POA a POAU con códigos de 16 segmentos); `test_flujo_sispro_poa.py` (3 tests: límite de dominio). |
| 10 | Legacy | `ccb080f` | Headers de deprecación RFC 8594 en API V1 (`DeprecationV1Middleware`, Sunset 2027-01-01); fix de colisión `VinculoViewSet` (`sis-pe/vinculos` a `VinculoEstrategicoViewSet`, `sis-pro/vinculos` a `VinculoProyectoViewSet`). |

## 4. Qué se renombró (identidad PIP vs SIS-POA)

- **SISPOA como identidad de plataforma** se renombró a **PIP** en la capa visible:
  login, title, sidebar, header, admin, emails y docstrings (11 archivos, Fase 2).
- **SISPOA como instrumento presupuestario** se renombró a **SIS-POA** en la
  semántica de dominio: bounded context operativo (`apps/budget`, `poau`,
  `modificaciones`, `seguimiento`, etc.) y en `inversion` (8 correcciones, Fase 6).
- No se aplicó ningún reemplazo global; cada cambio fue semántico y por contexto.

## 5. Qué se migró (EJECUTADO el 2026-08-15)

- **Migración física de esquemas COMPLETADA**: 168 tablas de dominio movidas de
  `public` a 9 esquemas PIP (`pip_core` 29, `pip_catalogo` 21, `sis_pe` 35,
  `sis_poa` 39, `sis_pro` 34, `pip_integracion` 4, `pip_auditoria` 1,
  `pip_geo` 4, `reportes` 1). `search_path` multi-esquema configurado en
  `settings.py` con `public` primero (PostGIS + migraciones futuras intactas).
  Backup previo: `backups/gams_sis_poa_pre_refactor_20260815_133116.dump`.
- **Base de datos renombrada**: `gams_sis_poa` → **`gams_pip`** (ALTER DATABASE,
  0 conexiones activas; `.env`, docker-compose y settings actualizados).
- **`tokenKey` migrado**: `sispoa_token` → `pip_token` con migración de sesión
  en `AuthService` (preserva la sesión del usuario, no la cierra).
- **Perfiles de importación renombrados**: `SISPOA_GASTOS_*` → `PIP_GASTOS_*`
  (migración de datos 0011 + AlterField 0012; backend, frontend y tests).
- Tablas con acción MERGE/SPLIT/DEPRECATE/REMOVE_LATER quedan en `public` como
  legacy (requieren cutover de datos V2, fases futuras): `presupuesto_*` legacy,
  `techos_*`, `flujo_*` v1, `articulacion_*` legacy, `indicadores_*`,
  `evaluacion_*`, `poau_*` legacy, `catalogos_seed_t4_propiedad`.

## 6. Qué permanece legacy (documentado, NO deprecado)

- Apps legacy `presupuesto`/`techos`/`flujo v1`/`articulacion legacy`: conviven
  en `public` con el cutover V2 (palanca `LEGACY_MENU_VISIBLE`).
- Tablas MERGE/SPLIT (`poau_poau`, `articulacion_accionpoa`, `indicadores_*`,
  `evaluacion_*`): requieren decisión de datos antes de migrar.
- DNS `sispoa.gamsacaba.gob.bo`, bucket `sispoa-docs`, realm Keycloak
  `sispoa`: la infraestructura del REPO (docker-compose, .env.example, scripts,
  realm-export, nginx, docs de despliegue) ya fue renombrada a `pip-*`
  (contenedores `pip-postgres`/`pip-redis`/`pip-minio`/`pip-keycloak`/...,
  bucket `pip-docs`, realm `pip`); el DNS y los nombres en el servidor real de
  despliegue quedan pendientes de coordinar en la fase de despliegue.
- `ArticulacionPADPEI` con 0 filas en BD: la cadena PAD a PEI se puebla con el
  management command `python manage.py importar_matrices <matrices.xlsx>` (la
  fuente XLSX de matrices de articulación es externa, no está versionada en el
  repo) o con el seed `core/demo_articuladores.py` para datos de demostración.
- API V1: sigue activa, ahora con headers de deprecación (Sunset 2027-01-01).
- Apps `techos` y `presupuesto` (legacy v1): conviven con `budget` v2 mediante
  la palanca de cutover `LEGACY_MENU_VISIBLE`.
- Colisión de tablas `presupuesto_categoria_programatica` (v2) vs
  `presupuesto_categoriaprogramatica` (legacy): convivencia documentada.
- `ArticulacionPADPEI` con 0 filas en BD: cadena PAD a PEI sin poblar (seed
  futuro).
- Infraestructura nombrada SISPOA: DNS `sispoa.gamsacaba.gob.bo`, bucket
  `sispoa-docs`, nombres `sispoa-*` en docker-compose.

## 7. Qué esquemas/módulos existen ahora (apps por bounded context)

| Bounded context | Apps |
|-----------------|------|
| **PIP CORE** | `core`, `accounts`, `organizacion`, `gestion`?, `workflow`, `documentos`, `notificaciones`, `acciones_correctivas` |
| **PIP CATÁLOGOS** | `catalogos`, `codificacion`, `normativa` |
| **SIS-PE** | `planificacion`, `pad` |
| **SIS-POA** | `budget`, `poau`, `modificaciones`, `seguimiento`, `recursos`, `indicadores`, `techos` (legacy), `presupuesto` (legacy) |
| **SIS-PRO** | `inversion` |
| **PIP INTEGRACIÓN** | `articulacion` |
| **PIP AUDITORÍA** | `auditoria` |
| **PIP GEO** | `territorio` |
| **REPORTES** | `reportes` |
| Otros | `evaluacion` |

## 8. Qué APIs cambiaron

- **API V2 por bounded context** (Fase 8, commit `ed87ef0`): 42 rutas nuevas.
  - `/api/v2/core/`: 5 rutas.
  - `/api/v2/catalogos/`: 13 rutas.
  - `/api/v2/geo/`: 3 rutas.
  - `/api/v2/integracion/`: 11 rutas + matrices.
  - `/api/v2/auditoria/`: 1 ruta.
  - Mapa completo en `API_MAPPING.md`.
- **API V1** (Fase 10, commit `ccb080f`): sin cambios de contrato, ahora con
  headers de deprecación RFC 8594 vía `DeprecationV1Middleware` y Sunset
  `2027-01-01`.

## 9. Qué migraciones se crearon

- **`0006` en `apps/inversion`** (Fase 6, commit `36e6bf4`): migración del
  bounded context SIS-PRO.
- **Renombres de tabla del commit `9961550`** (previo al refactor, base
  estructural): 51 modelos + 4 tablas M2M renombrados a español con prefijos
  `presupuesto_`, `catalogo_`, `cuentas_`, `nucleo_`, `flujo_`.

## 10. Qué tests se ejecutaron (por fase, resumen)

- FASE 4 (SIS-POA): suites completas verdes — **320+ tests**.
- FASE 5 (PIP INTEGRACIÓN): suites completas verdes — **378 tests**.
- FASE 6 (SIS-PRO): **40 tests** del bounded context.
- FASE 9 (flujos maestros): **7 tests** (4 `test_flujo_estrategico` + 3
  `test_flujo_sispro_poa`).
- FASE 10 (legacy): **4 tests** de deprecación + **38 tests** de regresión.
- Verificación transversal en cada fase: `manage.py check` sin issues y build
  del frontend OK.

## 11. Deuda técnica

1. Wizard PEI: UI frontend por pasos (backend listo: kernel V2 + `importar_pei`).
2. Motor PAD a PEI: herramientas visuales de articulación.
3. Wizard POA y motor PEI a POA.
4. Wizard POAU y motor POA a POAU.
5. Programación presupuestaria avanzada.
6. Integración SIS-PRO completa (contrato `IntegracionPoaContract` listo).
7. Seguimiento integral.
8. Dashboards / BI.
9. Cutover de datos de tablas MERGE/SPLIT que siguen en `public` (según
   `DATA_MIGRATION_PLAN.md`); la migración física de esquemas ya se ejecutó
   (sección 5).
10. Coordinar el DNS del despliegue (`pip.gamsacaba.gob.bo` propuesto) con la
    migración de infraestructura del repo a `pip-*`.

## 12. Qué debe hacerse después

Ejecutar el roadmap de la sección 11 en orden de prioridad de negocio, y al
cerrar cada entregable aplicar el **criterio final de éxito**:

- Verificar que las afirmaciones de **PIP**, **SIS-PE**, **SIS-POA** y
  **SIS-PRO** se cumplen contra el sistema real (cada bounded context expone su
  AppConfig, sus rutas V2 y sus fronteras documentadas).
- Confirmar que la identidad PIP es consistente en login, title, sidebar, admin,
  emails y APIs V2.
- Confirmar que el bounded context operativo SIS-POA (rutas `/sis-poa/`,
  capacidades `sis_poa.*`, apps `budget`) sigue intacto y operativo.
- Confirmar que el legacy documentado sigue disponible hasta su deprecación
  formal (API V1 con Sunset 2027-01-01).
- Ejecutar las suites de tests por bounded context antes de considerar cerrado
  cualquier cambio.

---

## Resumen por fase

| Fase | Commit | Entregables | Verificación |
|------|--------|-------------|--------------|
| 1 — Auditoría | `0f45829` | 4 docs (`AUDITORIA_SISPOA`, `ARQUITECTURA_ACTUAL`, `DOMAIN_MAP`, `SCHEMA_MAPPING`); 162 archivos y 865 referencias inventariados; 217 tablas mapeadas | Revisión documental |
| 2 — PIP CORE / identidad | `3400e22` | Identidad PIP en 11 archivos; `ARQUITECTURA_OBJETIVO.md` (6 diagramas), `DATA_MIGRATION_PLAN.md`, `LEGACY_DEPRECATION.md`, ADR/001-010 | `manage.py check` OK |
| 3 — SIS-PE | `776dba5` | AppConfigs `planificacion`/`pad`/`codificacion`; command `importar_pei` (MET-PEI-OFICIAL, OE/RI/PI); `SIS_PE_BOUNDED_CONTEXT.md` | Tests SIS-PE verdes |
| 4 — SIS-POA | `863e516` | 9 AppConfigs (incl. `techos`/`presupuesto` legacy); `SIS_POA_BOUNDED_CONTEXT.md` | 320+ tests verdes |
| 5 — PIP INTEGRACIÓN | `9ac64da` | `MotorArticulacion` (bidireccional + trazar); AppConfig `articulacion`; `services.py` como paquete; `PIP_INTEGRACION_BOUNDED_CONTEXT.md` | 378 tests verdes |
| 6 — SIS-PRO | `36e6bf4` | AppConfig `inversion`; 8 correcciones semánticas; `IntegracionPoaContract`; migración `0006`; `SIS_PRO_BOUNDED_CONTEXT.md` | 40 tests SIS-PRO verdes |
| 7 — Frontend | `b6a9ddd` | `package.json` `pip-sacaba`; "Enviar a SIS-POA" en SIS-PRO | Build frontend OK |
| 8 — APIs | `ed87ef0` | 42 rutas V2 por bounded context; `API_MAPPING.md` | Build + check OK |
| 9 — Tests | `0b45875` | `test_flujo_estrategico.py` (4), `test_flujo_sispro_poa.py` (3) | 7 tests verdes |
| 10 — Legacy | `ccb080f` | Headers RFC 8594 en V1 (Sunset 2027-01-01); fix colisión `VinculoViewSet` | 4 deprecación + 38 regresión verdes |

---

*Documento de cierre del refactor SISPOA a PIP. Para detalles técnicos,
consultar los documentos de fase en `docs/refactor-pip/` y los ADR/001-010.*
