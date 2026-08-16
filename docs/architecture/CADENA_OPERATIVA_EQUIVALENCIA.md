# Cadena Operativa — Documento de Equivalencia (TASK PIP-PE-001)

Documento de equivalencia y auditoría de divergencia de la cadena operativa
(acción → operación → actividad → tarea) entre las implementaciones
`articulacion_*`, `indicadores_*` y `poau_*`. Auditoría **read-only** (2026-08-16),
sin cambios de código funcional.

## 1. Propósito y método

Mapear semántica y campos de las implementaciones coexistentes, auditar la
divergencia de datos reales y alinear el plan de corte con
`docs/refactor-pip/LEGACY_DEPRECATION.md` (WP-14 / punto 17). Referencia
`docs/architecture/DUPLICATION_ANALYSIS.md` (D4), `DATA_OWNERSHIP.md` (O-6),
`PIP_SYSTEM_MAP.md` §6; no duplica su contenido.

## 2. Hallazgo principal: cuál es la cadena canónica

> **La cadena canónica V2 del SIS-POA es `poau.models_v2`** (`PoAInstitucional →
> AccionCortoPlazo → Operacion → Actividad → Tarea → ProgramacionActividad`),
> NO `articulacion_*`. Evidencia:
>
> - `backend/apps/poau/migration_v2.py:1-6` — "Importa la cadena operativa
>   **legacy** (articulacion.AccionPOA → …) a la **jerarquía canónica V2**".
> - `LEGACY_DEPRECATION.md:36` (punto 17) — `indicadores_*` es "Duplicado de la
>   jerarquía canónica de **poau V2**".
> - `docs/architecture/DUPLICATION_ANALYSIS.md:12,37` (D4) — "poau V2 canónica;
>   indicadores REMOVE_LATER". `PIP_SYSTEM_MAP.md:88` — "única canónica (poau V2)".
> - `/api/v2/sis-poa/` expone `poas/acciones/operaciones/actividades/tareas`
>   desde `poau.views_v2` (`config/urls_v2.py:143-148`).

`articulacion_*` es la cadena de **articulación SIS-PE** (motor de matrices
PAD-PEI-POA) y, para el SIS-POA, la **fuente legacy del puente** hacia la
canónica V2. Esta tarea asume esa realidad: la convergencia va
`articulacion_* → poau V2` (y `indicadores_*` se retira sin datos que migrar).

## 3. Las implementaciones y sus modelos

| # | Implementación | Modelos (nivel) | Líneas | Rutas expuestas |
|---|---|---|---|---|
| A | `articulacion` (SIS-PE, motor matrices) | `AccionPOA` → `OperacionPOAU` → `ActividadPOAU` → `TareaPOAU` | `articulacion/models.py` :434, :528, :606, :704 | V1 `/api/v1/articulacion/{acciones-poa,operaciones,actividades,tareas}/` (`articulacion/urls.py:20-24`); matrices V2 `/api/v2/integracion/` |
| B | `indicadores` (SIS-PE, legacy) | `Indicador` (:7), `MetaProgramada` (:48), `Operacion` (:70) → `Tarea` (:97), `Producto` (:114) | `indicadores/models.py` | V1 raíz `/api/v1/{indicadores,metas-programadas,operaciones,tareas,productos,medios-verificacion,supuestos}/` (`indicadores/urls.py`; montado en `config/urls.py:29`) |
| C | `poau` V1 (SIS-POA, legacy) | `POAU` → `POAUActividad` (+ `EjecucionFisica`/`Financiera`) | `poau/models.py` :7, :48, :112, :151 | V1 `/api/v1/poau/{poaus,actividades,ejecucion-fisica,ejecucion-financiera}/` (`poau/urls.py`; `config/urls.py:40`) |
| D | `poau` V2 (**canónica**) | `PoAInstitucional` → `AccionCortoPlazo` → `Operacion` → `Actividad` → `Tarea` (+ `ProgramacionActividad`) | `poau/models_v2.py` :31, :74, :113, :147, :177, :207 | V2 `/api/v2/sis-poa/{poas,acciones,operaciones,actividades,tareas,programaciones}/` (`config/urls_v2.py:143-148`) |
| E | `planificacion` V1 (SIS-PE, legacy) | `AccionMedianoPlazo` (:104) → `AccionCortoPlazo` (:131) | `planificacion/models.py` | V1 `/api/v1/{acciones-mediano-plazo,acciones-corto-plazo}/` (`planificacion/urls.py:14-15`) |

Nota: `indicadores.Operacion`/`Producto` referencian **`planificacion.AccionCortoPlazo`**
(V1) como padre, no a la cadena de 4 niveles; la topología legacy de `indicadores`
es un árbol de 2 niveles (Operación → Tarea, con Producto paralelo), **no** la
cadena de 4 niveles. (verificado en `indicadores/models.py:72-75,126-129`).

## 4. Mapeo semántico nivel por nivel

| Nivel | `articulacion` (A) | `indicadores` (B) | `poau` V2 (D, canónico) | Puente A→D |
|---|---|---|---|---|
| POA / gestión | — (pertenece a `AccionPOA.gestion`) | — | `PoAInstitucional` (`gestion`, `codigo='P-{g}`) | `importar_poa_v2`: 1 POA por gestión |
| Acción | `AccionPOA` (`codigo_accion`, `gestion`) | via `planificacion.AccionCortoPlazo` (E) | `AccionCortoPlazo` (`codigo`, `poa`) | `_crear_instancia('accion', poa, None, …)` |
| Operación | `OperacionPOAU` (`codigo_operacion`, FK `accion_poa`) | `Operacion` (`codigo`, FK `planificacion.AccionCortoPlazo`) | `Operacion` (`codigo`, FK `accion`) | `_crear_instancia('operacion', poa, accion_v2, …)` |
| Actividad | `ActividadPOAU` (`codigo_actividad`, FK `operacion`) | — (sin equivalente; `Producto` es paralelo a operación) | `Actividad` (`codigo`, FK `operacion`) | `_crear_instancia('actividad', poa, operacion_v2, …)` |
| Tarea | `TareaPOAU` (`codigo_tarea`, FK `actividad`) | `Tarea` (`codigo`, FK `Operacion`) — **padre distinto** | `Tarea` (`codigo`, FK `actividad`) | `_crear_instancia('tarea', poa, actividad_v2, …)` |
| Programación | `programacion_mensual` (JSON) en A | — | `ProgramacionActividad` (`anio`, `tipo` física/financiera, `programado`/`ejecutado`) | `_crear_instancia` copia campos a `atributos` JSON |

### 4.1 Equivalencias de campos

| Concepto | `articulacion` | `indicadores` | `poau` V2 | `poau` V1 |
|---|---|---|---|---|
| Código | `codigo_accion` / `codigo_operacion` / `codigo_actividad` / `codigo_tarea` | `codigo` | `codigo` (único por padre) | `codigo` (único por poau) |
| Nombre | `denominacion` | `nombre` | `nombre` | `nombre` |
| Gestión | `AccionPOA.gestion` (IntegerField, :483) | `MetaProgramada.gestion` (no en cadena); `Operacion` hereda de `planificacion.AccionCortoPlazo.gestion` | `PoAInstitucional.gestion` / `ProgramacionActividad.anio` | `POAU.gestion` (:25) |
| Padre | FK en cada nivel (A) | `Operacion→planificacion.AcccionCortoPlazo`; `Tarea→Operacion`; `Producto→AccionCortoPlazo` | FK en cada nivel (D) | `POAUActividad.poau` |
| Estado | `estado` (`REFERENCIAL`/`ENVIADO`/`APROBADO`/`OBSERVADO`, default `REFERENCIAL`) | `activo` (bool) en Operacion/Tarea/Producto | `estado` (`EstadosPoA`: `borrador`/`en_formulacion`/`en_revision`/`observado`/`aprobado`, default `borrador`) | `POAU.estado` (`borrador`/`enviado`/`aprobado`/`rechazado`) |
| Meta | `meta_gestion` (Accion), `meta_anual` (Operacion/Actividad) | `meta_anual` (Indicador), `MetaProgramada.meta_anual` | `atributos['meta_gestion'/'meta_anual']` (JSON) | `POAUActividad.meta_fisica_anual`, `meta_q1..q4` |
| Presupuesto | `presupuesto_programado` (Accion), `total_programado` (Operacion/Actividad) | — | `atributos['total_programado']` (JSON) | `POAUActividad.presupuesto_anual` |
| Responsable | `responsable`/`cargo_responsable` | — | `atributos['responsable']` | `POAU.responsable` (FK usuario) |
| Fechas | `fecha_inicio`/`fecha_fin` (Accion/Operacion/Actividad/Tarea) | `fecha_inicio`/`fecha_fin` (Operacion) | `atributos` (JSON) | — |

## 5. Reglas de negocio por nivel

| Nivel | Reglas detectadas |
|---|---|
| POA (`PoAInstitucional`) | `estado` en {revisión, aprobado} requiere `version_pei` vinculada (`models_v2.py:60-67`, `EstadosPoA.REQUIERE_PEI`). `codigo` único (`P-{gestion}`). |
| Acción | `articulacion.AcccionPOA`: código único global (`codigo_accion unique=True`); unique `(producto_pei, gestion, correlativo)`; `gestion` es campo **entero suelto** (deuda F-5 / PIP-DB-007). `poau v2.AcccionCortoPlazo`: unique `(poa, codigo)`; FK `nodo_pei`, `unidad`. |
| Operación | `articulacion.OperacionPOAU`: `tipo_operacion` obligatorio; unique `(accion_poa, correlativo)`. V2: unique `(accion, codigo)`. El puente copia `tipo_operacion` a `atributos`. |
| Actividad | `articulacion.ActividadPOAU`: M2M `normativas` (through `ActividadNormativa`); unique `(operacion, correlativo)`. V2: unique `(operacion, codigo)`; `ProgramacionActividad` exige `programado/ejecutado >= 0` y unique `(actividad, anio, tipo)`. |
| Tarea | `articulacion.TareaPOAU`: M2M `normativas` (through `TareaNormativa`); unique `(actividad, correlativo)`. V2: unique `(actividad, codigo)`. |
| Codificación | `articulacion_*` extienden `CodigoSegmentadoModel` (segmentos ACP/OP/ACT/TAR, `codigo_normalizado`, `estado_codigo`, `articulacion_incompleta`). `indicadores_*` y `poau V2` NO usan código segmentado. |

## 6. El puente `poau/migration_v2.py`

- `importar_poa_v2(lote='poa', dry_run=False, gestion=None)` (:46): por gestión
  crea `PoAInstitucional` y recorre `AccionPOA → OperacionPOAU → ActividadPOAU →
  TareaPOAU`, creando V2 con `get_or_create` y registrando `LegacyMigrationMap`
  (`_registrar_mapa`, :160).
- `_crear_instancia` (:118) mapea `denominacion→nombre`, `codigo_*→codigo` y
  copia `presupuesto_programado/meta_gestion/meta_anual/total_programado/
  responsable` a `atributos` (JSON).
- `comparar_duplicados_poa` (:226): reporta coincidencia de códigos entre
  `articulacion` y `indicadores` (operaciones/tareas).
- **Deuda detectada (idempotencia parcial)**: `get_or_create` por `(poa, codigo)`
  evita duplicados, pero **no re-sincroniza** filas ya creadas si el origen cambió;
  no hay transacción global ni rollback del lote; el `estado` V2 siempre es
  `borrador` aunque el origen esté `APROBADO`; `LegacyMigrationMap` se sobrescribe
  por lote sin versionado de checksum en cada corrida (solo `legacy_audit
  --reconciliar` lo actualiza a posteriori). Tarea derivada: PIP-PE-004.

## 7. Auditoría de divergencia de datos (2026-08-16, read-only)

Conteos reales por nivel y gestión (DB local, `manage.py shell`):

| Nivel | `articulacion` (A) | `indicadores` (B) | `poau` V1 (C) | `poau` V2 (D) | `planificacion` V1 (E) |
|---|---|---|---|---|---|
| POA | — | — | `POAU`=**0** | `PoAInstitucional`=**2** (2027, 2028) | — |
| Acción | `AccionPOA`=**1** (gestion **2027**, `REFERENCIAL`) | — | — | `AccionCortoPlazo`=**1** (`borrador`) | `AccionCortoPlazo`=**0** |
| Operación | `OperacionPOAU`=**1** (`REFERENCIAL`) | `Operacion`=**0** | — | `Operacion`=**1** | — |
| Actividad | `ActividadPOAU`=**1** | — | `POAUActividad`=**0** | `Actividad`=**1** | — |
| Tarea | `TareaPOAU`=**1** | `Tarea`=**0** | — | `Tarea`=**1** | — |
| Producto | — | `Producto`=**0** | — | — | — |
| Indicador | — | `Indicador`=**0**, `MetaProgramada`=**0** | — | — | — |
| Programación | — | — | `EjecucionFisica/Financiera`=**0** | `ProgramacionActividad`=**3** (2027 fis+fin, 2028 fin) | — |
| Trazabilidad | — | — | — | `LegacyMigrationMap`=**348** (cadena: 4 `reconciliado` lote `poa-2027`) | — |

### 7.1 Divergencias detectadas

1. **`indicadores_*` está vacío en toda la cadena** (Operacion/Tarea/Producto/
   Indicador/MetaProgramada = 0). El corte (REMOVE_LATER) **no requiere
   reconciliación de datos**: no hay registros que migrar ni consumidores de
   datos. Riesgo de datos para el retiro: **nulo**.
2. **La cadena canónica ya está poblada vía el puente**: los 4 niveles de
   `articulacion` (2027) tienen su equivalente V2 y están **reconciliados** en
   `LegacyMigrationMap` (lote `poa-2027`, estado `reconciliado`). No hay
   divergencia A→D en datos actuales.
3. **`poau` V1 y `planificacion.AcccionCortoPlazo` están vacíos** (0 registros):
   sin datos que reconciliar ni depurar.
4. **Inconsistencia menor en V2**: `PoAInstitucional` P-2028 existe sin acciones
   (0), pero hay una `ProgramacionActividad` con `anio=2028` colgada de la
   actividad ACT-01 del POA P-2027 (programación 2028 bajo POA 2027). Además
   `PoAInstitucional.gestion=2028` es **huérfana** (GestionFiscal solo 2026/2027;
   ver `GESTION_FISCAL_AUDIT.md:98,139`). Se resuelve en la fase de datos
   (PIP-DB-005 / PIP-PE-002).
5. **Estados no homogéneos entre cadenas**: `articulacion_*` en `REFERENCIAL`,
   V2 en `borrador` — coherente con el puente (default `borrador`), pero la
   auditoría de corte debe verificar que no existan `APROBADO`/`ENVIADO` en
   origen sin reflejo en V2 (hoy no los hay).

### 7.2 Consultas de auditoría usadas

```bash
cd backend
.venv\Scripts\python manage.py shell -c "from apps.articulacion.models import AccionPOA; print(AccionPOA.objects.count())"
.venv\Scripts\python manage.py shell -c "from apps.indicadores.models import Operacion, Tarea, Producto; print(Operacion.objects.count(), Tarea.objects.count(), Producto.objects.count())"
.venv\Scripts\python manage.py shell -c "from apps.poau.models import POAU, POAUActividad; from apps.poau.models_v2 import PoAInstitucional, Operacion, Actividad, Tarea; print(POAU.objects.count(), PoAInstitucional.objects.count(), Operacion.objects.count())"
```

## 8. Impacto frontend del corte de `indicadores_*`

Consumidores en `frontend/sispoa/src/app/features/`:

| Feature | Componente/Servicio | Endpoint legacy | Impacto al cortar |
|---|---|---|---|
| `indicadores` | `indicadores.component.ts:62` | GET `/indicadores/` | **Roto** — el listado de indicadores deja de cargar |
| `portal-publico` | `portal-publico.service.ts:68` (`listarIndicadores`) + `portal-indicadores.component.ts` | GET `/indicadores/` | **Roto** — portal público pierde el banco de indicadores (público) |
| `layout/sidebar` | `sidebar.component.ts:225` ítem `/indicadores` (`legacy: true`) | — | Ocultar vía palanca `LEGACY_MENU_VISIBLE['/indicadores']=false` |
| `core/config/cutover.config.ts:24` | palanca `'/indicadores': true` | — | Roadmap ya prevé el corte (paso 3: "cuando la jerarquía canónica V2 esté operativa") |

**No consumen `indicadores_*` legacy** (usan `articulacion` o V2): los features
`articulacion/*` (llaman `/articulacion/operaciones/`, `/articulacion/tareas/`,
`/articulacion/acciones-poa/`, matrices V2) y `poau/*` (`/poau/poaus/`). El
`formulacion-wizard` de `planificacion` escribe operaciones en el formulario pero
persiste vía `/formulacion/enviar/` (V1 formulación), no a `indicadores_*`.

**Backend que referencia `indicadores_*`** (debe migrarse o deprecarse en la
tarea de corte): `planificacion/views.py:17,162-185` (FormulacionViewSet crea
Indicador/MetaProgramada/Operacion), `workflow/consolidacion.py:25`
(Operacion/Producto), `reportes/services.py:899,1047,1174`
(Indicador/MetaProgramada/Supuesto), `scripts/seed_demo.py:501`, `poau/migration_v2.py:228`
(`comparar_duplicados_poa`), `core/services/limpieza_datos_simulados.py:63`,
comandos `importar_matriz_base.py`/`importar_reales.py`, y tests
(`test_sis_poa_v2.py:272`, `workflow/tests.py:33`, `pad/tests/test_comprehensive.py`).

## 9. Plan de convergencia y tareas derivadas

| Fase | Tarea | Alcance |
|---|---|---|
| 1 | **PIP-PE-002** | Reconciliación de datos cadena operativa: verificar checksums A→D (lote `poa-2027`), resolver POA P-2028 sin acciones + `ProgramacionActividad` anio 2028 huérfana, verificar estados origen/v2. |
| 2 | **PIP-PE-003** | Corte de `indicadores_*` (REMOVE_LATER, punto 17): deprecación blanda (`DeprecationWarning`, header, ocultar menú), migrar `portal-publico` a fuente V2 (`/api/v2/integracion/indicadores/` → `articulacion.IndicadorCadena`), migrar/neutralizar consumidores backend (FormulacionViewSet, consolidacion, reportes), luego retiro por tarea aprobada. |
| 3 | **PIP-PE-004** | Refactor del puente `poau/migration_v2.py`: idempotencia real (re-sync por checksum, transacción por lote, rollback), mapeo de estados origen→V2, gestión canónica vía `GestionFiscal`. |

Orden respeta la secuencia REMOVE_LATER de `LEGACY_DEPRECATION.md` (corte tras
cutover V2 y reconciliación) y la regla de deprecación escalonada (§1, §4).

## 10. Riesgos y deuda

- **Medio**: si aparecen datos nuevos en `indicadores_*` antes del corte (hoy 0),
  la reconciliación deja de ser trivial. Mitigación: auditoría en la tarea de corte.
- `poau/migration_v2.py` sin idempotencia total ni mapeo de estados.
- `articulacion.AcccionPOA.gestion` y `PoAInstitucional.gestion` como enteros
  sueltos (F-5): el 2028 huérfano es evidencia (PIP-DB-005/007).
- `indicadores_*` tiene dos modelos con significado solapado (`Indicador` vs
  `articulacion.IndicadorCadena`): el corte debe decidir el destino del banco
  municipal de indicadores (hoy vacío).
- El puente copia campos a `atributos` (JSON no tipado): la convergencia final
  debe decidir qué campos pasan a columnas reales en V2.

## 11. Referencias

- `docs/refactor-pip/LEGACY_DEPRECATION.md` (punto 17, §4, WP-14).
- `docs/architecture/DUPLICATION_ANALYSIS.md` (D4), `DATA_OWNERSHIP.md` (O-6),
  `PIP_SYSTEM_MAP.md` §6, `GESTION_FISCAL_AUDIT.md` §5, `PIP_AUDIT_REPORT.md` (F-4/F-5).
- `docs/refactor-pip/ADR/ADR-004-articulation-model.md`.
- Código: `backend/apps/{articulacion,indicadores,poau,planificacion}/{models.py,models_v2.py,migration_v2.py,views.py,views_v2.py,urls.py}`; `backend/config/urls.py`, `urls_v2.py`.
- Frontend: `frontend/sispoa/src/app/features/{indicadores,portal-publico}/*`, `layout/sidebar.component.ts`, `core/config/cutover.config.ts`.

Documento de auditoría — creado en TASK PIP-PE-001 (2026-08-16, read-only).