# SIS-POA — Base de Datos del Ciclo Presupuestario

Todas las tablas del ciclo viven en el schema público de PostgreSQL 16
(prefix `budget_` salvo `gestion_gestionfiscal`, reutilizada). Montos siempre
`NUMERIC(18,2)`; códigos `VARCHAR` (ceros iniciales preservados); IDs `UUID`
(heredados del proyecto). El prefijo de tabla de cada modelo es el nombre de
la clase (p. ej. `budget_directiveceiling`).

## 1. Gestión fiscal (reutilizada)

### `gestion_gestionfiscal` — entidad de gestión del ciclo
- `anio` (único), `estado`, `descripcion`, `anio_inicio_plurianual`,
  `anio_fin_plurianual`, `fecha_apertura`, `fecha_cierre`, `activa`.
- **Estados del ciclo** (nuevos códigos, `services.ESTADO_*`):
  `CONFIGURACION → HABILITADA → EN_FORMULACION → VIGENTE → CERRADA`.
  Los estados legacy se conservan (mapeo: `preparacion≈CONFIGURACION`,
  `abierta≈HABILITADA`, `formulacion≈EN_FORMULACION`, `cerrada≈CERRADA`).
- Relacionada vía `CicloFormulacion`/`EtapaFormulacion` (herencia de configuración).

## 2. Techo directivo

### `budget_directiveceiling`
| Campo | Tipo | Notas |
|---|---|---|
| `gestion` | FK OneToOne `gestion_gestionfiscal` | un techo por gestión |
| `estado` | VARCHAR(20) | espejo del estado de la versión actual |
| `version_actual` | PositiveInteger | número de la versión vigente |

### `budget_directiveceilingversion`
- `ceiling` FK, `numero` PositiveInteger, `estado` (BORRADOR/EN_REVISION/OBSERVADO/APROBADO/FIJADO), `hash` CHAR(64) SHA-256, `fecha_fijacion`, `fijado_por` FK `accounts_usuario`, `observaciones`, `inmutable` bool.
- **Constraint**: `UNIQUE (ceiling, numero)` → `uniq_techo_version_numero`.

### `budget_ceilingresource` — recurso (ingreso) del techo por origen
- `version` FK, `origen` (SIGEP/MUNICIPAL/SALDO/OTRO), FKs opcionales a `catalogos_rubrorecurso`, `catalogos_fuentefinanciamiento`, `catalogos_organismofinanciador`, `catalogos_entidadtransferencia`, `concepto`, `monto`, `documento` FK `budget_budgetdocument` (SET_NULL).
- **Constraint**: `CHECK (monto >= 0)` → `check_ceilingresource_monto_positivo`.

### `budget_mandatoryexpense` — gasto obligatorio (descuenta del techo bruto)
- `version` FK, `da`/`ue` FKs organizacionales, `programa`, `actividad` (VARCHAR, ceros), `denominacion`, `fuente`, `organismo`, `objeto_gasto` FKs catálogos, `entidad_transferencia`, `monto`, `documento` FK.
- **Constraint**: `CHECK (monto >= 0)` → `check_mandatoryexpense_monto_positivo`.

### `budget_budgetdocument` — documento de respaldo (SIGEP, nota MEF…)
- `gestion` FK (índice), `tipo` (REPORTE_SIGEP/NOTA_MEF/RESOLUCION/INFORME/PROYECCION_RECURSOS_PROPIOS/OTRO), `nombre`, `mime_type`, `size`, `sha256` (calculado en `save()` por chunks), `fecha_documento`, `archivo` FileField (`MEDIA_ROOT/budget/`), `metadata_json`.

## 3. Categorías programáticas

### `budget_programmaticcategory`
- `gestion` FK, `codigo` VARCHAR(20), `denominacion`, `nivel` (PROGRAMA/SUBPROGRAMA/PROYECTO/ACTIVIDAD), `parent` FK self (CASCADE), `vigencia_desde/hasta`, `estado` (ACTIVA/INACTIVA), `origen`, `normativa`, `observaciones`.
- **Constraint**: `UNIQUE (gestion, codigo)` → `budget_categoria_gestion_codigo_uniq`; índice `(gestion, parent)`.
- `clean()` exige parent de la misma gestión y nivel estrictamente más profundo.

## 4. Distribución presupuestaria

### `budget_distributionversion`
- `gestion` FK, `numero`, `estado` (EstadosTecho), `hash`, `fecha_fijacion`, `fijado_por`, `observaciones`, `inmutable`.
- **Constraint**: `UNIQUE (gestion, numero)` → `uniq_distribution_version_numero`.

### `budget_allocation` — apertura programática
- `gestion` FK, `version` FK `budget_distributionversion` (SET_NULL), FKs opcionales: `unidad_organizacional`, `distrito`, `da`, `ue`, `categoria` (→ `budget_programmaticcategory`), `proyecto_codigo`, `codigo_sisin`, `actividad_codigo` (VARCHAR), `denominacion`, `tipo_apertura` (DETAIL), `estado` (BORRADOR/ACTIVA/CERRADA), `orden`.
- Índices: `(gestion, version)`, `(gestion, categoria)`, `(gestion, distrito)`.
- `total` = agregación de `AllocationSource` (nunca columna ni fila).

### `budget_allocationsource` — asignación normalizada por FF/OF
- `allocation` FK (CASCADE), `fuente` FK, `organismo` FK (ambos opcionales), `monto`.
- **Constraints**: `CHECK (monto >= 0)` → `check_allocationsource_monto_positivo`;
  `UNIQUE (allocation, fuente, organismo)` con `nulls_distinct=False` →
  `uniq_allocation_fuente_organismo` (una fila por llave, aun con NULL).

### `budget_reserve` — reserva presupuestaria sobre una fuente
- `gestion` FK, `version` FK (SET_NULL), `fuente`, `organismo` FKs, `tipo` (DISTRITAL/DISTRIBUCION/OTRA), `monto`, `motivo`, `estado` (ACTIVA/LIBERADA).
- **Constraint**: `CHECK (monto >= 0)` → `check_reserve_monto_positivo`; índices `(gestion, estado)`, `(gestion, version)`.

## 5. Importador Excel (staging)

### `budget_budgetimport`
- `gestion` FK, `perfil` (SISPOA_GASTOS_HISTORICO/SISPOA_GASTOS_ACTUAL/OTRO), `filename`, `mime_type`, `size`, `sha256`, `hoja_seleccionada`, `mapeo_json` (mapeo columnas + fuentes), `estado` (STAGING/VALIDADO/CORREGIDO/APLICADO/RECHAZADO), `tipo_importacion` (GASTOS), `archivo` FileField (`budget/imports/`), `creado_por`. Índice `(gestion)`.

### `budget_importdetalle`
- `importacion` FK, `fila` (1-based), `clasificacion` (PROGRAM_HEADER/SUBPROGRAM_HEADER/DETAIL/SUBTOTAL/TOTAL/EMPTY/UNKNOWN), `datos_json` (campos normalizados + `_raw` con valores/tipos/formatos originales), `estado` (PENDIENTE/VALIDO/ERROR), `errores_json`. Índice `(importacion, estado)`.

### `budget_importerror`
- `importacion` FK, `detalle` FK opcional, `fila`, `campo`, `valor_original`, `valor_normalizado`, `severidad` (INFO/WARNING/ERROR/CRITICAL), `mensaje`, `accion` (REEMPLAZAR/NORMALIZAR/ASIGNAR/IGNORAR/NINGUNA), `resuelto` bool. Índice `(importacion, severidad)`.

## 6. Distribución territorial

### `budget_territorialdistribution`
- `gestion` FK, `version` FK (SET_NULL), `fuente`, `organismo` FKs, `metodo` (MANUAL/MONTO_FIJO/PORCENTAJE/POBLACION/FORMULA), `bolsa_total`, `estado` (BORRADOR/CALCULADA/APLICADA), `observaciones`.
- **Constraint**: `CHECK (bolsa_total >= 0)` → `check_territorialdistribution_bolsa_positiva`; índice `(gestion)`.

### `budget_territorialallocation`
- `distribucion` FK, `distrito` FK, `poblacion`, `porcentaje` NUMERIC(7,4) (escala 0-100), `monto_calculado`, `ajuste`, `monto_final` (invariante: `SUM(monto_final) = bolsa_total` exacto).
- **Constraint**: `UNIQUE (distribucion, distrito)` con `nulls_distinct=False` → `uniq_distribucion_territorial_distrito`.

## 7. Objetos del gasto

### `budget_expenseobjectallocation`
- `allocation` FK (CASCADE), `objeto_gasto` FK `catalogos_objetogasto` (PROTECT), `monto`.
- **Constraints**: `CHECK (monto >= 0)` → `check_expenseobjectallocation_monto_positivo`;
  `UNIQUE (allocation, objeto_gasto)` → `uniq_allocation_objeto_gasto`; índice `(allocation, objeto_gasto)`.

## 8. Reformulaciones

### `budget_reform`
- `gestion` FK, `tipo` (TRASPASO/INCREMENTO/DISMINUCION/NUEVA_APERTURA/CIERRE_APERTURA/CAMBIO_FUENTE/AJUSTE_DISTRIBUCION), `estado` (BORRADOR/EN_REVISION/OBSERVADA/APROBADA/APLICADA/RECHAZADA), `motivo`, `resolucion`, `documento` FK (SET_NULL), `version_origen`/`version_resultante` FKs `budget_distributionversion` (resultante NULL en esta fase), `solicitada_por` FK (PROTECT), `aprobada_por` FK (SET_NULL), `fecha_aplicacion`. Índice `(gestion)`.

### `budget_reformmovement`
- `reform` FK (CASCADE), `tipo` (TRASPASO/INCREMENTO/DISMINUCION/CAMBIO_FUENTE), `apertura_origen`/`apertura_destino` FKs `budget_allocation` (PROTECT), `fuente`/`organismo` FKs, `monto`, `saldo_antes`/`saldo_despues` (histórico del `AllocationSource` afectado), `motivo`.
- **Constraint**: `CHECK (monto >= 0)` → `check_reformmovement_monto_positivo`.

## 9. Resumen de constraints

| Tipo | Tablas |
|---|---|
| `CHECK (monto/bolsa >= 0)` | `ceilingresource`, `mandatoryexpense`, `allocationsource`, `reserve`, `territorialdistribution`, `expenseobjectallocation`, `reformmovement` |
| `UNIQUE` compuesto | `(ceiling, numero)`, `(gestion, numero)` distribución, `(gestion, codigo)` categoría, `(allocation, fuente, organismo)` con `nulls_distinct=False`, `(distribucion, distrito)` con `nulls_distinct=False`, `(allocation, objeto_gasto)` |

No existen filas de total: los agregados (`techo`, `distribuido`, `reservado`,
`disponible`) se calculan siempre por SQL sobre estas tablas.
