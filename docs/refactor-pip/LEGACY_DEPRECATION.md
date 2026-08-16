# FASE 2 — PLAN DE DEPRECACIÓN LEGACY (SISPOA → PIP)

> Catálogo de referencias legacy del refactor SISPOA → PIP, con consumidores, riesgo, estrategia de deprecación y plazo sugerido.
> Fuentes: `AUDITORIA_SISPOA.md` (inventario clasificado), `ARQUITECTURA_ACTUAL.md` (baseline), `SCHEMA_MAPPING.md` (destino de tablas).

---

## 1. Regla general

**No se elimina ninguna compatibilidad hasta validar sus consumidores.** La condición para retirar cada referencia es el cutover V2 del dominio correspondiente (palanca `LEGACY_MENU_VISIBLE` del frontend, `cutover.config.ts`) y la validación de las integraciones SIS-PRO ↔ SIS-POA (paquete de transferencia, outbox). La deprecación es escalonada:

1. Marcar como deprecado (`DeprecationWarning` en backend, header HTTP `Deprecation` en respuestas API, etiqueta "V1" en el frontend).
2. Ventana de observación con monitoreo de consumidores.
3. Retirar (404 / eliminación) SOLO tras la ventana y con el respaldo documentado.

## 2. Inventario de referencias legacy

| # | Referencia legacy | Dónde | Consumidor actual | Riesgo de deprecación | Estrategia | Plazo sugerido |
|---|---|---|---|---|---|---|
| 1 | API v1 (`/api/v1/`) | `config/urls.py`, `environment.ts: apiUrl = '/api/v1'` | Frontend (módulos legacy V1: planificacion, pad, articulacion, indicadores, poau, inversion, presupuesto, techos, recursos, seguimiento, modificaciones, consolidacion) | **Alto**: el frontend legacy escribe y lee V1 hasta su cutover por dominio | Deprecated API: mantener read-only tras el cutover del dominio; header `Deprecation: true`; 404 tras ventana (plan maestro §17, §20 Contract) | 1-2 ciclos de gestión tras cutover completo de cada dominio |
| 2 | Namespace `/api/v1/` (raíz sin versión) | Views montadas en prefijo raíz (app `planificacion` bajo dos prefijos) | Integraciones ad-hoc y scripts | Medio: documentación histórica | Deprecated API; consolidar en `/api/v2/{platform,sis-pe,sis-poa,sis-pro}` | Junto al punto 1 |
| 3 | Apps `presupuesto` legacy (6 tablas) | `backend/apps/presupuesto/`, tablas `presupuesto_programapresupuestario`, `presupuesto_proyectopresupuestario`, `presupuesto_actividadpresupuestaria`, `presupuesto_categoriaprogramatica`, `presupuesto_asignacionpresupuestariaunidad`, `presupuesto_lineapresupuestaria` | Frontend `features/presupuesto`; reportes históricos | **Alto** (colisión de prefijo con budget `presupuesto_*`; datos históricos de presupuesto) | DEPRECATE con datos: mover a `public_legacy` (nunca DROP); el dominio lo cubre `budget` V2 (`/api/v2/sis-poa/budget/`); compat view read-only si reportes externos lo exigen | Tras cutover budget V2 + validación de reportes históricos |
| 4 | App `techos` legacy (3 tablas) | `backend/apps/techos/`, tablas `techos_techopresupuestario`, `techos_distribuciontecho`, `techos_movimientotecho` | `TechoViewSetV2` (ya sirve V2); frontend `features/techos` | Medio: `TechoViewSetV2` es el adaptador V2 existente | DEPRECATE datos; el servicio V2 (`budget.DirectiveCeiling`) reemplaza el dominio | Tras validar que `TechoViewSetV2` consume solo V2 |
| 5 | `PerfilImportacion.SISPOA_GASTOS_HISTORICO` / `SISPOA_GASTOS_ACTUAL` | `budget/models.py:872-878,964`, `importer.py`, migración `0004_*`, tests, `imports.component.html/.ts` | Importación de planillas SIGEP (23 ocurrencias; valor persistido en `Importacion.perfil`) | **Alto** (renombrar rompe histórico y tests) | KEEP con coexistencia: valores actuales intactos; perfiles nuevos `PIP_*` solo cuando se reemplace el formato de planilla; alias de mapeo en el importador | Decisión en fase de datos; sin fecha de retiro |
| 6 | `tokenKey: 'sispoa_token'` (localStorage JWT) | `frontend/sispoa/src/environments/environment.ts` y `.prod.ts` | Todos los usuarios autenticados | **Medio-alto**: renombrar cierra sesión global | Migración de sesión: doble lectura (nuevo tokenKey con fallback al viejo) durante una ventana; luego escritura nueva y limpieza | Junto a la fase de identidad visible (fase 2 del plan maestro), con comunicación |
| 7 | BD `gams_sis_poa` | `.env`, `settings.py` default, `docker-compose*.yml`, docs | Backend, scripts de backup (`sispoa_db_*.dump`) | **Alto** (renombrar BD = dump/restore o `ALTER DATABASE` + roles; rompe backups viejos) | Alias: mantener `gams_sis_poa` como link/symlink de `gams_pip` durante la transición; los backups viejos conservan su nombre | Fase de infraestructura (plan maestro fase 12); no en fase de código |
| 8 | Usuario/rol BD `sispoa` (y `sispoa_user` en docs) | `.env`, `settings.py`, `INSTALACION.md`, `manual_administrador.md` | Conexiones de aplicación y administración | Alto | Adapter: crear rol `pip` con los mismos privilegios y migrar conexiones; `sispoa` queda como rol legacy sin uso | Junto al punto 7 |
| 9 | DNS `sispoa.gamsacaba.gob.bo` / rutas `/var/log/sispoa/`, `/var/www/sispoa/` | `settings_production.py`, nginx, docs de despliegue | Producción (TLS, ALLOWED_HOSTS, CORS) | **Alto** (DNS + certificados) | Alias: mantener el dominio legacy redirigiendo a `pip.*` durante la ventana; después solo el nuevo | Fase de despliegue con ventana planificada |
| 10 | Bucket MinIO `sispoa-docs` y endpoint `sispoa-minio` | `settings_storage.py`, `docker-compose*.yml`, docs | Almacenamiento documental (django-storages S3) | Medio: renombrar bucket requiere copiar objetos | Alias: bucket nuevo `pip-docs` con copia de objetos y registro de migración; endpoint docker renombrado con healthcheck | Fase de infraestructura |
| 11 | Servicios docker `sispoa-*` | `docker-compose*.yml` (postgres, redis, backend, frontend, nginx, celery-worker/beat, minio, geoserver, keycloak), nginx includes | Despliegue completo | **Alto** (DNS interno, healthchecks, scripts) | RENAME coordinado por plan de despliegue; nunca aislado | Fase de infraestructura |
| 12 | Realm Keycloak `sispoa`, clients `sispoa-frontend`/`sispoa-backend` | `infra/keycloak/realm-export.json`, nginx, `settings_oidc` | OIDC (cuando `OIDC_RP_CLIENT_ID` presente) | **Alto** (reimportar realm, rotar secret, re-registrar usuarios) | Plan separado: realm `pip` nuevo con migración de usuarios y clientes; SimpleJWT sigue funcionando mientras tanto | Fase de infraestructura; el OIDC es futuro (ADR-009) |
| 13 | Usuario Linux `sispoa` / `/home/sispoa` | `docs/despliegue.md`, crontab, backups | Operación del servidor | Medio | Adapter: usuario `pip` con mismos permisos; migrar crontab y jobs de backup | Junto al punto 7 |
| 14 | Identidad visible "SISPOA Sacaba" (login, título, sidebar, header, admin, email, Swagger, endpoint raíz) | `login.component.ts`, `index.html`, `sidebar/header.component.ts`, `core/admin.py`, `accounts/views.py`, `settings.py` SPECTACULAR, `views_root.py` | Usuarios finales | Bajo-Medio (cambio visible; los documentos oficiales impresos NO se reescriben) | RENAME directo con coordinación de identidad institucional; encabezado de consolidación con fecha de corte (`workflow/consolidacion.py`) | Fase 2 (identidad visible) |
| 15 | `sistema_origen='SISPOA'` (valor persistido) | `inversion/models_preinversion.py:194`, `SolicitudReformulacion` | SIS-PRO (reformulaciones originadas por SIS-POA) | **Alto** (renombrar rompe histórico) | KEEP del valor + mapeo en `pip_integracion.referencia_externa`; etiquetas de display → "SIS-POA" | Fase de datos |
| 16 | `flujo_*` legacy (workflow POA) | `flujo_envio_formulacion`, `flujo_revision`, `flujo_observacion`, `flujo_aprobacion` | Flujo legacy de formulación | Medio | DEPRECATE datos en `public_legacy`; el motor V2 (`flujo_definicion`/`flujo_instancia` → `pip_core`) ya lo reemplaza | Tras cutover workflow V2 |
| 17 | Jerarquía operativa legacy en `indicadores` (`operacion`, `tarea`, `producto`) | `indicadores_operacion/tarea/producto` | Duplicado de la jerarquía canónica de `poau` V2 | Medio (datos duplicados) | REMOVE_LATER: retirar tras cutover V2 y reconciliación (WP-14) | Tras validar jerarquía canónica SIS-POA |
| 18 | Logs `logs/sispoa.log` | `settings.py:249` logging | Operación | Bajo (renombrar pierde rotación histórica) | RENAME con coexistencia temporal de archivos | Junto a la identidad visible |

## 3. Estrategias de deprecación (definiciones)

| Estrategia | Descripción | Uso |
|---|---|---|
| **Alias** | El nombre legacy sigue resolviendo al nuevo (redirect DNS, bucket copiado, doble tokenKey) | Puntos 6, 7, 9, 10 |
| **Deprecated API** | Endpoint legacy responde con header `Deprecation: true` y `Warning: 299`; log de uso por consumidor | Puntos 1, 2 |
| **Compat view** | Vista SQL read-only en el esquema de compatibilidad con el mismo nombre y forma de la tabla legacy | Puntos 3, 4, 16 (reportes externos) |
| **Adapter** | Capa de servicio que traduce legacy ↔ V2 sin duplicar datos (p. ej. `TechoViewSetV2`, importador de perfiles `PIP_*`) | Puntos 4, 5, 8, 13 |
| **KEEP con coexistencia** | El valor/dato legacy se conserva tal cual; lo nuevo usa convención PIP | Puntos 5, 15 |

## 4. Reglas de implementación de la deprecación

1. **Nunca en silencio**: toda respuesta deprecada lleva header `Deprecation` (RFC 8594) y el backend loguea `DeprecationWarning` con el consumidor (User-Agent, ruta) para medir uso real.
2. **Frontend**: los módulos V1 ya tienen etiqueta "V1" en el sidebar (`sidebar.component.ts:54`) y la palanca `LEGACY_MENU_VISIBLE`; la deprecación de API debe ir acompañada de los ítems ocultos.
3. **Integraciones SIS-PRO ↔ SIS-POA**: el paquete de transferencia y el outbox (`evento_outbox`, `mensaje_entrante`) son contratos; su deprecación requiere que AMBOS lados migren (SIS-POA V2 consumiendo el paquete de solo lectura), nunca unilateralmente (`AUDITORIA_SISPOA.md` §3.3).
4. **Ventana mínima**: 1 ciclo de gestión (una gestión fiscal completa) entre el marcar y el retirar para las referencias de datos; 30 días para las de infraestructura no persistente.
5. **Retiro**: el 404 o eliminación solo con respaldo `-Fc` verificado y registro en `nucleo_mapa_migraciones_legacy` (`pip_core.mapa_migraciones_legacy`).

## 5. Secuencia recomendada de deprecación

| Orden | Bloque | Referencias |
|---|---|---|
| 1 | Identidad visible | 14 (fase 2 del plan maestro) |
| 2 | Frontend cutover V2 por dominio | 1, 2, 3, 4, 16, 17 (palanca `LEGACY_MENU_VISIBLE`, orden de retiro documentado en `ARQUITECTURA_ACTUAL.md` §7) |
| 3 | Datos protegidos | 5, 15 (decisión explícita en fase de datos) |
| 4 | Sesión y despliegue | 6, 9 |
| 5 | Infraestructura | 7, 8, 10, 11, 12, 13, 18 |

---

## 6. Estado de la deprecación (FASE 10 — Legacy / deprecación)

Actualizado en la FASE 10 del refactor. Este bloque solo marca y documenta;
no retira ninguna compatibilidad (regla general §1).

### 6.1 Marcado en esta fase

| Ítem | Estado |
|---|---|
| API V1 (`/api/v1/`) | **Marcada**: toda respuesta con path `api/v1/*` lleva `Deprecation: true`, `Sunset: Sun, 01 Jan 2027 00:00:00 GMT` y `Link: <.../LEGACY_DEPRECATION.md>; rel="deprecation"` (RFC 8594). Implementado como middleware `apps.core.middleware.DeprecationV1Middleware` (registrado en `MIDDLEWARE` de `config/settings.py` y `config/settings_test_sqlite.py`; `settings_production.py` lo hereda). Las fechas y el enlace son configurables vía `API_V1_SUNSET` / `API_V1_DEPRECATION_LINK`. **No** aplica a `/api/v2/` ni a `/health/`. |
| Apps `techos` y `presupuesto` | Ya marcadas `(legacy)` en su `verbose_name` (FASE 4); sin cambios en esta fase. |
| Fix `VinculoViewSet` (BUG preexistente) | `config/urls_v2.py` importaba `VinculoViewSet` sin alias para dos routers: el segundo import (planificación) pisaba al de inversión, y `sis-pro/vinculos/` servía datos de SIS-PE. Corregido con alias `VinculoEstrategicoViewSet` (SIS-PE) y `VinculoProyectoViewSet` (SIS-PRO). |

### 6.2 Pendiente (NO se toca por riesgo de datos/sesión)

| Referencia | Motivo de no tocar | Plazo |
|---|---|---|
| `tokenKey: 'sispoa_token'` (localStorage JWT) | Renombrar cierra sesión global; requiere migración de sesión con doble lectura (estrategia Alias, §2 punto 6) | Junto a la fase de identidad visible; ventana de doble lectura |
| `PerfilImportacion.SISPOA_GASTOS_HISTORICO/ACTUAL` | Renombrar rompe histórico persistido y tests; estrategia KEEP con coexistencia (§2 punto 5) | Decisión en fase de datos; sin fecha de retiro |
| BD `gams_sis_poa` (y usuario/rol `sispoa`) | Renombrar = dump/restore + roles + backups viejos; fase de infraestructura (§2 puntos 7-8) | Plan maestro fase 12 |
| DNS, buckets MinIO, servicios docker, realm Keycloak, usuario Linux | Infraestructura con ventana planificada (§2 puntos 9-13) | Fases de despliegue/infraestructura |

### 6.3 Plazo

- **Sunset sugerido API V1: 2027-01-01** (`API_V1_SUNSET` en `config/settings.py`), 1-2 ciclos de gestión tras el cutover completo de cada dominio (§2 punto 1).
- El retiro (404/eliminación) solo tras la ventana de observación, con monitoreo de consumidores y respaldo `-Fc` verificado (§4).

### 6.4 Evidencia de auditoría — punto 17 (cadena operativa `indicadores_*`)

Auditoría TASK PIP-PE-001 (2026-08-16, read-only; `docs/architecture/CADENA_OPERATIVA_EQUIVALENCIA.md`):

- **`indicadores_*` está vacío** (0 registros en `operacion`, `tarea`, `producto`, `indicador`, `metaprogramada`): el retiro **no requiere reconciliación de datos** y su riesgo de datos es nulo.
- La cadena canónica `poau` V2 ya está poblada y **reconciliada** desde `articulacion` (lote `poa-2027`, `LegacyMigrationMap` = `reconciliado`, 4 niveles).
- **Aclaración de canonicidad**: la jerarquía canónica V2 del SIS-POA es `poau.models_v2` (`PoAInstitucional → AccionCortoPlazo → Operacion → Actividad → Tarea`), expuesta en `/api/v2/sis-poa/`. `articulacion_*` es la cadena de articulación SIS-PE y la **fuente legacy** del puente `poau/migration_v2.py` (su propio docstring la llama "cadena operativa legacy"). `indicadores_*` es un **duplicado adicional** de esa jerarquía con topología distinta (2 niveles, padre `planificacion.AcccionCortoPlazo`).
- Consumidores a migrar antes del retiro: frontend `features/indicadores`, `features/portal-publico` (`GET /indicadores/`); backend `planificacion/views.py` (FormulacionViewSet), `workflow/consolidacion.py`, `reportes/services.py`, `scripts/seed_demo.py`, `poau/migration_v2.py:228`, comandos `importar_matriz_base`/`importar_reales`.
- Plan de corte derivado: `tasks/backlog/PIP-PE-002` (reconciliación), `PIP-PE-003` (corte), `PIP-PE-004` (refactor puente). El alcance de REMOVE_LATER se **mantiene** (nada que cambiar): sigue tras cutover V2 y reconciliación.
