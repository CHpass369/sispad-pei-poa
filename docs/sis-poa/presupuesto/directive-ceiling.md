# SIS-POA — Techo Directivo (`directive-ceiling`)

## 1. Concepto

El techo directivo es el tope de recursos de la gestión: contenedor por
gestión (`DirectiveCeiling`, OneToOne `GestionFiscal`) con versiones
(`DirectiveCeilingVersion`) que transitan una máquina de estados; la versión
**fijada es inmutable** (patrón `VersionInstrumento`, checksum SHA-256).
La composición deriva `techo_bruto` y `techo_distribuible` como agregaciones
(nunca filas de total).

## 2. Orígenes de recursos (`OrigenRecurso`)

| Origen | Significado |
|---|---|
| `SIGEP` | Recursos del reporte SIGEP (gobierno nacional) |
| `MUNICIPAL` | Recursos propios municipales |
| `SALDO` | Saldo de caja y bancos |
| `OTRO` | Otros ingresos |

Cada `CeilingResource` opcionalmente referencia `RubroRecurso`,
`FuenteFinanciamiento`, `OrganismoFinanciador` y `EntidadTransferencia` de los
catálogos corporativos (versionados por gestión), con `monto >= 0`
(`CheckConstraint` + `clean()`). El documento de respaldo es opcional
(`BudgetDocument`).

## 3. Composición (§22) — `composicion_techo(ceiling)`

Calculada sobre la versión actual (`version_actual`):

```
techo_bruto        = Σ SIGEP + Σ MUNICIPAL + Σ SALDO + Σ OTRO
gastos_obligatorios= Σ MandatoryExpense
techo_distribuible = techo_bruto − gastos_obligatorios
por_fuente         = agregación por fuente de financiamiento ('SIN_FUENTE' si nula)
```

La deducción de gastos obligatorios por FF/OF individual se aplica en la
distribución (`techo_distribuible_por_fuente`); en la composición se resta
del total general. `reservas` queda en 0 en esta fase. Los montos se
serializan como string (`_serializar_montos`).

## 4. Flujo de estados de la versión

```
BORRADOR ──→ EN_REVISION ──→ APROBADO ──→ FIJADO
   ↑            │  ↑
   │            │  └── OBSERVADO (devolver con motivo obligatorio)
   └────────────┘
```

Transiciones (`EstadosTecho.TRANSICIONES`), ejecutadas por
`enviar_a_revision`, `observar`, `aprobar`, `fijar_techo` — cada una registra
`EventoAuditoria` (`enviar/devolver/aprobar/aprobar`). El estado del
`DirectiveCeiling` es espejo del de la versión actual.

## 5. Fijación inmutable (§24) — `fijar_techo(version, usuario)`

`@transaction.atomic`. Validaciones **antes** de congelar:

1. Gestión habilitada (`validar_gestion_para_techo`).
2. `techo_distribuible >= 0` (obligatorios no superan el bruto).
3. Sin montos negativos en recursos ni gastos.
4. `_validar_fuentes_organismos`: rubros/fuentes/organismos/entidades
   presentes deben pertenecer a la gestión (`valor.gestion == gestion.anio`).
5. La versión debe estar `APROBADO` (solo un techo aprobado puede fijarse).

Luego `version.fijar()`:

- `estado = FIJADO`, `inmutable = True`, `hash = calcular_hash()`,
  `fecha_fijacion`, `fijado_por`.
- El checksum es SHA-256 de los datos semánticos ordenados (recursos y
  gastos obligatorios por contenido: origen, códigos, concepto,
  `str(monto)`; estable ante reordenación de filas).
- `ceiling.version_actual = numero` y `estado = FIJADO`.

**Inmutabilidad**: `DirectiveCeilingVersion.save()` y el `clean()` de
`CeilingResource`/`MandatoryExpense` lanzan `ValidationError` si la versión
está fijada; los viewsets de recursos/gastos devuelven **409** al crear/
modificar/eliminar filas de una versión fijada (`_VersionMutableMixin`).
`verificar_hash()` permite auditar la integridad.

## 6. Ajuste de techo (§25) — `ajuste_de_techo(ceiling, usuario)`

Solo si la versión actual está `FIJADO`:

1. Crea la versión `numero = actual + 1` en `BORRADOR` con observación
   "Ajuste de la versión N (fijada)".
2. **Copia** recursos y gastos obligatorios de la fijada (la fijada queda
   intacta, solo lectura).
3. `version_actual` y el estado del techo pasan a la versión nueva.

El ajuste de techo modifica *los recursos*; el ajuste de distribución
(versión nueva de `DistributionVersion`) es distinto y vive en la Fase 7.

## 7. Documentos de respaldo (`BudgetDocument`)

- Tipos: `REPORTE_SIGEP`, `NOTA_MEF`, `RESOLUCION`, `INFORME`,
  `PROYECCION_RECURSOS_PROPIOS`, `OTRO`.
- `sha256` calculado en `save()` sobre el contenido (chunks); `size` del
  archivo; `storage_path` expone la ruta en `MEDIA_ROOT/budget/`.
- Upload vía `POST /documents/` (multipart): máx. 20 MB, mimes permitidos
  (PDF, PNG/JPEG, Excel, Word, CSV, texto).

## 8. API

| Ruta | Propósito | Permiso |
|---|---|---|
| `GET/POST /directive-ceilings/` · `GET/PATCH/DELETE /{id}/` | CRUD (create exige gestión habilitada y techo único; crea v1 BORRADOR) | manage (escritura) |
| `POST /{id}/submit/` · `observe/` · `approve/` · `freeze/` | transiciones | `sis_poa.budget.approve` |
| `GET /{id}/composition/` | composición (§22) | autenticado |
| `GET/POST /resources/` · `/{id}/` (?version=) | recursos del techo | manage (escritura) |
| `GET/POST /mandatory-expenses/` · `/{id}/` (?version=) | gastos obligatorios | manage (escritura) |
| `POST /documents/` · `GET /documents/?gestion=` | documentos de respaldo | manage (create/destroy) |

El endpoint `freeze` valida todo el §24 y devuelve el techo con la versión
fijada (hash incluido). Sin versión actual (`version_actual=0`) las
transiciones responden error.
