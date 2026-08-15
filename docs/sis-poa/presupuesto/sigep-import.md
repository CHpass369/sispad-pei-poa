# SIS-POA — Importación SIGEP

## 1. Qué se implementó (fiel al código)

La Fase 2 integró el techo SIGEP con **dos piezas reales** (no hay parser de
PDF en el backend):

1. **Documento de respaldo** (`BudgetDocument` con `tipo=REPORTE_SIGEP`):
   el reporte SIGEP se sube como archivo y queda con su `sha256`.
2. **Recursos por rubro/FF/OF** (`CeilingResource` con `origen=SIGEP`):
   los montos del reporte se registran normalizados por rubro de recurso,
   fuente de financiamiento, organismo financiador y entidad otorgante
   (catálogos corporativos versionados), contra la versión del techo.

La composición del techo suma el origen SIGEP junto a MUNICIPAL/SALDO/OTRO
(ver `directive-ceiling.md` §2-3).

## 2. Estructura del reporte

La planilla/reporte SIGEP **no se importa automáticamente**: el usuario
carga el documento y registra los recursos del techo. El mapeo es manual vía
API (CRUD de `/resources/`), con estas reglas:

- `origen` fijo `SIGEP` para distinguirlo de recursos propios/saldos.
- `monto` NUMERIC(18,2) `>= 0` (CheckConstraint + validación de fijación).
- Rubro/fuente/organismo/entidad: opcionales pero, si se indican, deben
  **pertenecer a la gestión** (`_validar_fuentes_organismos` en la fijación:
  `valor.gestion == gestion.anio` → si no, la fijación falla).
- `documento` opcional: referencia al `BudgetDocument` de respaldo
  (`related_name='recursos'`).

## 3. Documentos de respaldo (sha256)

`POST /api/v2/sis-poa/budget/documents/` (multipart):

| Campo | Detalle |
|---|---|
| `gestion` | gestión fiscal del documento |
| `tipo` | `REPORTE_SIGEP`, `NOTA_MEF`, `RESOLUCION`, `INFORME`, `PROYECCION_RECURSOS_PROPIOS`, `OTRO` |
| `archivo` | máximo 20 MB; mimes: PDF, PNG/JPEG, Excel, Word, CSV, texto |
| `sha256` | calculado en `save()` sobre los chunks del archivo (hex 64) |
| `size` / `mime_type` | autocompletados |
| `storage_path` | ruta en `MEDIA_ROOT/budget/` (read-only) |

El `sha256` garantiza la integridad del respaldo (un reporte reemplazado
tendría otro hash); se expone en el serializer para verificación.

## 4. Recursos por rubro/FF/OF (`CeilingResource`)

`POST/GET /api/v2/sis-poa/budget/resources/?version=` (+ `/{id}/` PATCH/DELETE):

- Campos: `version`, `origen`, `rubro`, `fuente`, `organismo`,
  `entidad_otorgante`, `concepto`, `monto`, `documento`.
- Serializer expone `*_detalle` (`{codigo, denominacion}`) de cada catálogo
  y `documento_nombre`.
- Escritura sobre una versión **fijada** → `409` (inmutable).

## 5. Ciclo del techo con SIGEP

```
1. Gestión HABILITADA
2. POST /directive-ceilings/            → crea techo + v1 BORRADOR
3. POST /documents/  (tipo REPORTE_SIGEP) → respaldo con sha256
4. POST /resources/  (origen SIGEP × N)   → recursos por rubro/FF/OF
5. POST /mandatory-expenses/ (si aplica)  → gastos obligatorios
6. POST /directive-ceilings/{id}/submit/ → EN_REVISION
7. POST /directive-ceilings/{id}/approve/→ APROBADO
8. POST /directive-ceilings/{id}/freeze/ → FIJADO (valida §24: montos ≥ 0,
   obligatorios ≤ bruto, catálogos de la gestión, checksum SHA-256)
9. Distribución: techo_distribuible_por_fuente() = Σ recursos[f] −
   Σ obligatorios[f] (recursos sin fuente NO distribuibles en esta fase)
```

## 6. Notas y límites (documentados)

- No existe importación automática del PDF SIGEP (ni OCR ni parsing de
  tablas): el plan original la preveía, la implementación optó por carga
  de respaldo + registro normalizado manual (decisión de la Fase 2).
- Sin techo FIJADO, `techo_distribuible_por_fuente()` devuelve `{}` y
  **toda operación de distribución queda bloqueada**.
- Los gastos obligatorios atribuidos a una fuente se restan del techo de
  esa fuente; los que no tienen fuente se restan del total general
  (regla §22).
