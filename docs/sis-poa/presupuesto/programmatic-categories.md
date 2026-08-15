# SIS-POA — Categorías Programáticas (`programmatic-categories`)

## 1. Concepto

`budget.ProgrammaticCategory` es el catálogo **propio del ciclo presupuestario**
(por gestión): base programática de las aperturas. Es jerárquico con 4
niveles y se duplica entre gestiones. No reemplaza a
`presupuesto.CategoriaProgramatica` (legacy), que se documenta como
coexistente.

## 2. Jerarquía y niveles (`NivelCategoria`)

```
PROGRAMA ──> SUBPROGRAMA ──> PROYECTO ──> ACTIVIDAD
```

- Los niveles **no son obligatorios** en todas las categorías: un PROGRAMA
  puede tener hijos PROYECTO sin pasar por SUBPROGRAMA, etc.
- `parent` = FK self (CASCADE); el árbol se recorre con `hijos`.

## 3. Códigos con ceros

- `codigo` es **VARCHAR(20)**: los ceros iniciales se preservan (`'097'`
  no es `97`).
- **Constraint**: `UNIQUE (gestion, codigo)` →
  `budget_categoria_gestion_codigo_uniq` (el código compuesto es único por
  gestión, no global).
- `codigo_compuesto` (serializer): ruta jerárquica `prog[.sub[.proy[.act]]]`
  preservando ceros — p. ej. `01.02.001`.

## 4. Reglas de validación (`clean()`)

1. El padre debe pertenecer a la **misma gestión**.
2. El padre no puede tener el **mismo nivel** que la categoría.
3. El nivel debe ser **más profundo** que el del padre (índice de nivel
   estrictamente mayor en PROGRAMA < SUBPROGRAMA < PROYECTO < ACTIVIDAD).

`save()` ejecuta `full_clean()`; el serializer traduce los errores a
`ValidationError` de DRF (400).

## 5. Otros campos

`denominacion`, `estado` (ACTIVA/INACTIVA), `vigencia_desde/hasta`,
`origen` (texto, p. ej. `'duplicado'`), `normativa`, `observaciones`.

## 6. Árbol — `GET /programmatic-categories/tree/?gestion=` (obligatorio)

Devuelve la estructura anidada desde raíces (`parent__isnull=True`),
ordenadas por `nivel, codigo`:

```json
[{ "id", "codigo", "denominacion", "nivel", "estado", "hijos": [...] }]
```

## 7. Duplicar a gestión — `POST /programmatic-categories/{id}/duplicar_a_gestion/`

Body: `{"gestion_destino": "<id>"}`. Copia la categoría **y su subárbol**
(recorre `origen.hijos` en orden `nivel, codigo`), re-apuntando `parent` a la
copia (mapeo por id original):

- Respeta `vigencia`, `estado`, `normativa`; `origen` se marca `'duplicado'`
  si la categoría no trae uno propio.
- Errores: `gestion_destino` faltante o inexistente → 400.
- Respuesta 201: `{detail: 'Categoría y N hijos duplicados.'}`.

## 8. CRUD y catálogos

- `GET/POST /programmatic-categories/` (filtros `?gestion=` y `?nivel=`),
  `PATCH/DELETE /{id}/`.
- **No se pueden crear categorías para una gestión no habilitada** (400).
- `GET /budget/catalogs/` expone los catálogos corporativos para los
  formularios del ciclo: `fuentes`, `organismos`, `rubros`,
  `objetos_gasto`, `entidades_transferencia`, `distritos`, `direcciones`,
  `unidades_ejecutoras`, `unidades_organizacionales` (limitados a 500
  opciones cada uno).

## 9. Integración con el ciclo

- Las aperturas referencian `categoria` (FK PROTECT): no se puede borrar
  una categoría en uso.
- El importador Excel valida que `programa`/`subprograma` de cada fila
  existan como código de categoría de la gestión (CRITICAL si no — ver
  `excel-importer.md`).
- La categoría alimenta el `codigo_compuesto` de las aperturas en la UI.
