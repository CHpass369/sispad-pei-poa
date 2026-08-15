# SIS-POA — Importador Excel (`excel-importer`)

## 1. Flujo (staging — nunca aplicar directo)

```
upload → parsear_libro → validar_importacion → aplicar_importacion
(STAGING)    (ImportDetalle)   (ImportError)      (aperturas BORRADOR)
```

1. **`parsear_libro`**: lee la planilla (openpyxl, XLSX/CSV), detecta el
   header (puede estar desplazado: logos, títulos, filas vacías), clasifica
   las filas y construye `ImportDetalle` con datos normalizados.
2. **`validar_importacion`**: severidades por fila; con ERROR/CRITICAL la
   importación queda en STAGING con los hallazgos (`ImportError`); sin
   ERROR/CRITICAL pasa a **VALIDADO**.
3. **`aplicar_importacion`**: SOLO sin CRITICAL sin resolver; crea aperturas
   **BORRADOR** (no consumen disponibilidad — la fijación de la Fase 7
   valida el total) y registra auditoría.

## 2. Perfiles (`PerfilImportacion` / `PERFILES`)

| Perfil | Columnas esperadas | Mapeo |
|---|---|---|
| `SISPOA_GASTOS_HISTORICO` | 17 columnas GASTOS (N°, UNIDAD EJECUTIVA, DISTRITO, DA, UE, V, PROG., SISIN, ACT., DENOMINACIÓN, Saldo, CT, RE, ORE, IDH, TGN, Total) | `_MAPEO_GASTOS_HISTORICO` |
| `SISPOA_GASTOS_ACTUAL` | ídem (reutiliza el mapeo histórico) | ídem + corrección por usuario |
| `OTRO` | ninguna | mapeo manual |

- **Fuentes por defecto por columna de monto** (`FUENTES_DEFAULT`):
  `ct→41`, `re→20`, `ore→20`, `idh→41`, `tgn→11`. Configurable por el
  usuario (`mapeo_json['fuentes']`); la validación verifica que el código
  exista en `catalogos.FuenteFinanciamiento` para la gestión.
- El mapeo efectivo = defaults del perfil + overrides del usuario
  (`POST /imports/{id}/map/`); se guarda en `mapeo_json`.

## 3. Detección de header (`detectar_header`)

- Coincidencia por **nombre de columna normalizado** (sin acentos/
  mayúsculas/puntuación); la fila con más columnas esperadas presentes es
  el header; `None` si no hay ≥ 3 coincidencias → error de parseo.
- Se detecta por hoja; si la hoja seleccionada no tiene header se busca
  también ahí (y se reporta 400 si ninguna).

## 4. Clasificación de filas (`clasificar_fila`, columna V)

| Valor V | Clasificación | Tratamiento |
|---|---|---|
| `P`/`PROGRAMA` | `PROGRAM_HEADER` | se descarta |
| `SP`/`SUBPROGRAMA` | `SUBPROGRAM_HEADER` | se descarta |
| `TS`/`SUBTOTAL` | `SUBTOTAL` | se conserva, NO genera apertura |
| `T`/`TOTAL` | `TOTAL` | se conserva, NO genera apertura |
| (vacío y fila vacía) | `EMPTY` | se descarta |
| resto | `DETAIL` | candidata a apertura |

## 5. Normalización

- **Códigos** (`programa`, `subprograma`, `sisin`, `actividad`, `da`, `ue`):
  SIEMPRE string; ceros iniciales preservados (`'097'`); si la celda vino
  numérica se reconstruye con el formato de celda (`number_format '000'`)
  y se advierte (WARNING "códigos numéricos, ceros posiblemente perdidos").
- **Montos**: `Decimal`, nunca float. Se aceptan `'1.234.567,89'` (coma
  decimal), `'1,234,567.89'`, prefijos `'Bs 1.234'`, `'(123)'` → negativo,
  `''` → 0. Errores de Excel (`#REF!`, `#VALUE!`, `#DIV/0!`, `#N/A`, …) →
  CRITICAL.
- **Texto**: trim + colapso de espacios (INFO si se normalizó).

## 6. Severidades (`SeveridadError`)

| Severidad | Casos |
|---|---|
| `CRITICAL` | error de Excel / monto no numérico; monto negativo; fuente de financiamiento inexistente en catálogos de la gestión; programa/subprograma inexistente en `ProgrammaticCategory` |
| `ERROR` | denominación vacía; fila duplicada (sisin + actividad + denominación) |
| `WARNING` | distrito no encontrado; códigos numéricos (ceros perdidos); campos opcionales faltantes (`unidad`, `da`, `ue`, `programa`) |
| `INFO` | normalizaciones aplicadas (trim/espacios) |

Cada hallazgo es un `ImportError` con `campo`, `valor_original`,
`valor_normalizado`, `accion` sugerida (REEMPLAZAR/NORMALIZAR/ASIGNAR/
IGNORAR) y `resuelto`. Los ERROR/CRITICAL marcan el detalle como `ERROR`;
la importación pasa a VALIDADO solo sin ellos. Los CRITICAL sin resolver
**bloquean la aplicación**.

## 7. Aplicación (`aplicar_importacion`)

- Requisitos: sin CRITICAL sin resolver; no estar ya APLICADO.
- Por cada detalle `DETAIL` + `VALIDO` con denominación: crea `Allocation`
  BORRADOR (con `version` activa de distribución, `distrito` resuelto por
  nombre, `categoria` por código de programa, `codigo_sisin`/`actividad`).
- Montos por fuente: CT/RE/ORE/IDH/TGN → `AllocationSource`; columnas que
  mapean al mismo código de fuente **se suman en una sola fila** (ej. CT e
  IDH → 41). Fuente inexistente en la gestión → 400.
- Resultado: `{aperturas_creadas, total_importado, estado: APLICADO}` +
  auditoría (`crear`).

## 8. API (`BudgetImportViewSet`)

| Ruta | Propósito | Permiso |
|---|---|---|
| `POST /imports/` | upload (máx. 20 MB; XLSX/XLS/CSV) + parseo automático | `sis_poa.budget.import` |
| `GET /imports/?gestion=&estado=&perfil=` | listar | autenticado |
| `GET /imports/{id}/hojas/` | hojas del libro | autenticado |
| `POST /imports/{id}/map/` | configurar hoja + mapeo y re-parsear | `sis_poa.budget.import` |
| `POST /imports/{id}/validate/` | validar (severidades) | `sis_poa.budget.import` |
| `GET /imports/{id}/errors/?severidad=` | hallazgos | autenticado |
| `POST /imports/{id}/apply/` | aplicar (aperturas BORRADOR) | `sis_poa.budget.import` |

Si el archivo no es una planilla válida, la importación pasa a `RECHAZADO`
y la respuesta es 400.

## 9. Casos cubiertos por tests

Planillas GASTOS histórica/actual, headers desplazados, `#REF!`, códigos
con ceros (`097`), SISIN, duplicados, distritos inexistentes y aplicación
con montos sumados por fuente (ver `testing.md`).
