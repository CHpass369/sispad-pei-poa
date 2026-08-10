# WP-14 — Retiro de legacy: auditoría y roadmap

**Estado: PLAN DE RETIRO PREPARADO** — la ejecución del borrado queda sujeta a
los gates del plan maestro (§21 FASE 14). No se elimina nada en esta fase:
la UI activa sigue consumiendo V1 (compatibilidad temporal, ADR-002).

---

## 1. Condiciones previas (gates obligatorios)

El plan exige ANTES de retirar:

1. V2 estable y en producción como interfaz principal (frontend V2, FASE 9).
2. Reconciliación 100% de registros críticos (conteos, códigos, presupuestos).
3. Cero escritura legacy (ventanas de freeze por módulo, ADR-004).
4. Periodo de observación completado.
5. Respaldo y rollback documentados (WP-00/12: dump verificado, 171/171 tablas).

**Estado actual:** no cumplidos (V1 sigue siendo la UI activa) → **no retirar**.

## 2. Inventario de legacy candidato a retiro

### 2.1 Duplicidades de modelos (ver `domain_map.md`)

| Duplicidad | Dominio | Acción de retiro |
|---|---|---|
| PAD en `pad` + `articulacion` (Lineamiento/Resultado/Producto) | SIS-PE | Fusionar en nodos V2; retirar tras cutover PAD |
| PEI en `articulacion` (ResultadoPEI/ProductoPEI) | SIS-PE | Migrado a kernel; retirar con app legacy `articulacion` |
| Operación/Tarea en `indicadores` + `articulacion` | SIS-POA | Retirar duplicados; jerarquía canónica V2 en `poau` |
| `poau.POAUActividad` vs jerarquía V2 | SIS-POA | Adaptador temporal hasta cutover POAU |
| `AccionCortoPlazo` (planificacion) vs V2 | SIS-POA | Retirar con `planificacion` legacy |

### 2.2 JSONFields deprecados

| Modelo | Campo | Reemplazo |
|---|---|---|
| `pad.ResultadoTerritorial` | `programacion_fisica` / `programacion_financiera` | `ProgramacionAnualPAD` (ya existe) |
| `pad.ProductoTerritorial` | `programacion_fisica` / `programacion_financiera` | `ProgramacionAnualPAD` |
| `articulacion.OperacionPOAU` | `programacion_mensual` | `ProgramacionActividad` V2 |
| `articulacion.ActividadPOAU` | `programacion_mensual` | `ProgramacionActividad` V2 |

Los datos de los JSONFields deben backfillearse a las tablas relacionales
antes de eliminar las columnas (WP-05 reconcilia checksums).

### 2.3 Endpoints V1

- 26 includes de apps en `/api/v1/` (config/urls.py).
- El include duplicado de `planificacion` (raíz + `planificacion/`) se retira
  al hacer el cutover de planificación.
- 14 endpoints V1 sin serializer tipado (warnings de drf-spectacular, WP-00).
- 3 endpoints `AllowAny` (auth pública) se mantienen.

### 2.4 Componentes Angular legacy

- 26 feature modules V1 → se sustituyen por los V2 por sistema.
- `SisPeModule` (V2) ya convive con V1; los módulos legacy se retiran
  módulo a módulo tras su cutover (FASE 9-11).

## 3. Roadmap de retiro por dominio

| Orden | Dominio | Condición de retiro |
|---|---|---|
| 1 | `planificacion` legacy | Cutover SIS-PE (frontend V2 en uso, reconciliación kernel 100%) |
| 2 | `pad` + PAD de `articulacion` | Idem + conciliación de presupuestos/metas |
| 3 | PEI de `articulacion` | Cutover PEI V2 |
| 4 | `articulacion` (resto) | POA/POAU migrados (FASE 10) |
| 5 | `indicadores` (Operacion/Tarea/Producto) | Jerarquía canónica V2 operativa |
| 6 | `poau` legacy | Cutover SIS-POA |
| 7 | `inversion` legacy | Cutover SIS-PRO |
| 8 | V1 API completa | Frontend V2 en producción + periodo de observación |

## 4. Procedimiento de retiro por módulo (ADR-004)

1. Congelar escritura legacy (freeze).
2. Backfill + reconciliación (`legacy_audit --reconciliar --lote <lote>`).
3. Cutover del frontend al namespace V2.
4. Retirar endpoints V1 del módulo (marcar deprecado → 410/redirigir).
5. Eliminar modelos/columnas obsoletos (una versión estable después).
6. Actualizar documentación y CHANGELOG.

## 5. Verificación del plan de retiro

- `legacy_audit --estado` → conteo de registros por estado (pendiente/migrado/
  reconciliado/discrepancia).
- Suite completa (926 tests) debe permanecer verde en cada paso.
- Respaldo restaurable verificado (WP-13: 171/171 tablas idénticas).
