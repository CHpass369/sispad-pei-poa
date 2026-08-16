# Reporte de Funcionamiento de la Plataforma PIP-GAMS Sacaba

**Fecha:** 16 de agosto de 2026
**Alcance:** Estado real y funcionamiento de toda la plataforma (backend, frontend, datos, infraestructura, API en vivo)
**Método:** Evidencia ejecutada, no documental: suites de tests completas, `manage.py check`, inventario de BD, pruebas HTTP en vivo contra el servidor en ejecución, validación de compose.

---

## 1. Resumen ejecutivo

| Área | Estado | Evidencia |
|---|---|---|
| Backend (Django/DRF) | ✅ **OPERATIVO** | 1251/1252 tests OK · `check` sin issues · 117 migraciones aplicadas |
| API (V1 + V2) | ✅ **OPERATIVA** | 1959 endpoints · V2 protegida (401 sin token) · health 200 |
| Frontend (Angular 21) | ✅ **OPERATIVO** | 252/252 tests OK · build producción OK |
| Base de datos (PostGIS) | ✅ **MIGRADA** | 9 esquemas PIP (222 tablas) + 54 tablas legacy en `public` |
| Infraestructura | ✅ **VÁLIDA** | `docker compose config` OK · PG/Redis/Django/ng serve activos |
| Login | ⚠️ **CON RIESGO** | Endpoint OK, pero credenciales del seed no validan y ningún usuario tiene roles |
| Calidad | ⚠️ **DEUDA** | 1 test fallido (datos demo) · 391 warnings · suite lenta (16m42s) |

**Veredicto:** la plataforma está funcional de punta a punta. Los problemas detectados son de datos/calidad, no de arquitectura. Un test fallido y el riesgo de login son los únicos bloqueos reales.

---

## 2. Backend — Django / DRF

### 2.1 Verificaciones

- `python manage.py check` → **0 issues**.
- Migraciones: **117 aplicadas, 0 pendientes**.
- **Suites de tests completas: 1251 passed, 1 failed, 239 subtests** (16m42s).
- Endpoints registrados: **1959** (API V1 + API V2 + admin + SPA).

### 2.2 Test fallido (único)

```
apps/planificacion/tests/test_demo_matrix.py::DemoMatrizCompletaTests
::test_matrix_2027_returns_same_operational_chain_as_m3
AssertionError: 0 != 19   (nodos nivel actividad_poau esperados: 19, obtenidos: 0)
```

**Causa:** el endpoint `GET /api/v1/planificacion/matriz-completa/?gestion=2027` no devuelve la cadena operacional (actividades/tareas POAU) porque **la data demo de la gestión 2027 no incluye esa cadena** en el entorno de test. No es un fallo de código de producción: el endpoint funciona; es un problema de seed/datos demo. Afecta al reporte de la matriz completa para 2027.

### 2.3 Warnings (391 totales)

El patrón dominante es `UnorderedObjectListWarning` de DRF: varios querysets paginados **no tienen `ordering` definido** (catalogos, InstrumentoPlanificacion, AccionCorrectiva, Evaluacion, Notificacion, etc.). Riesgo real: **paginación inconsistente** (elementos que se repiten o se saltan entre páginas).

---

## 3. Base de datos — PostgreSQL 17 + PostGIS

### 3.1 Esquemas (222 tablas de dominio migradas)

| Esquema | Tablas | Contenido |
|---|---|---|
| `sis_poa` | 39 | Operativo: POAU, budget, seguimiento, modificaciones |
| `sis_pe` | 35 | Estratégico: PAD, PEI, kernel de instrumentos |
| `sis_pro` | 34 | Ciclo de proyecto: preinversión, costos |
| `pip_core` | 29 | Núcleo transversal |
| `pip_catalogo` | 21 | Catálogos versionados |
| `pip_integracion` | 4 | Articulación |
| `pip_geo` | 4 | Territorio/PostGIS |
| `pip_auditoria` | 1 | Auditoría |
| `reportes` | 1 | Reportes |
| `public` | 54 | Legacy V1 (presupuesto, techos, flujo v1, articulacion legacy) |

### 3.2 Inventario de datos por dominio (contado en BD real)

**Núcleo / IAM**
- 4 usuarios (`admin@gamsacaba.gob.bo`, `smoke@pip.local`, `smoke2@pip.local`, `docx-test@x.gob.bo`) — **ninguno con roles asignados**.
- 31 capacidades, 12 roles, 8 unidades organizacionales, 11 unidades ejecutoras, 5 direcciones administrativas.

**SIS-PE — Planificación Estratégica**
- Kernel V2: 3 instrumentos, 604 nodos de planificación, 61 articulaciones, 8 versiones de instrumento, 4 versiones de metodología.
- Catálogos marco 2026-2035 **completos**: 170 lineamientos PAD, 49 componentes PDESA, 25 sectores económicos, 21 ejes PGDESA, 57 acuerdos internacionales (ODS/NDT/30×30), 6 versiones de catálogo.
- Matrices PAD: **4 borradores** (flujo borrador → materialización operativo).
- PAD legacy (V1): 1 cadena SIPEB (PoliticaPAD → Lineamiento → ResultadoTerritorial → ProductoTerritorial).
- **Vacíos:** `ArticulacionPADPEI` (0 filas — puente PAD→PEI) e `IndicadorCadena` (0 filas).

**SIS-POA — Planificación Operativa**
- Budget V2: 1 techo directivo (con versión), 5 recursos de techo, 3 gastos obligatorios.
- POAU 2027: 2 POA institucionales, 3 programaciones de actividad.
- Cadena operativa V1: 1 AccionPOA → OperacionPOAU → ActividadPOAU → TareaPOAU.
- Legacy vacío: `TechoPresupuestario` (0 filas).

**SIS-PRO — Ciclo del Proyecto**
- 3 proyectos, 3 condiciones previas, 2 documentos técnicos, 2 costos de proyecto, 1 vínculo proyecto-actividad.

**Transversal**
- Workflow V2: 1 definición, 2 instancias, 8 tareas, 4 transiciones, 2 aprobaciones.
- Catálogos: 23 fuentes de financiamiento, 13 unidades de medida, 11 organismos financiadores, 6 tipos de producto, 5 tipos de proyecto.
- Normativa: 5 versiones. Gestión fiscal: 2. Territorio: 12 distritos. Auditoría: 1 evento.
- `LegacyMigrationMap`: **348 registros** de reconciliación legacy.

---

## 4. API — prueba en vivo contra el servidor en ejecución

| Prueba | Resultado |
|---|---|
| `GET /health/` | **200** `{"status":"ok","sistema":"PIP-GAMS","version":"1.0.0","base_datos":"ok"}` |
| `GET /api/v2/` sin token | **401** (protección correcta) |
| `GET /api/v2/me/capabilities/` sin token | **401** |
| `POST /api/v1/auth/login/` (sin CSRF) | Procesa la petición (**400** validación: exige `email`) → el login funciona, **no hay fricción CSRF** |
| `POST /api/v1/auth/login/` con `admin@gamsacaba.gob.bo` / `admin2026` | **401** credenciales no válidas en la BD actual |

**Hallazgo crítico de acceso:** el usuario `admin` existe y está activo, pero la contraseña del seed (`admin2026`) no valida en esta BD y **ninguno de los 4 usuarios tiene roles** (el menú por capacidades quedará vacío para sesiones nuevas). Las sesiones existentes (token en `localStorage`) siguen funcionando; un alta nueva o un logout dejarían a alguien sin acceso.

---

## 5. Frontend — Angular 21

- **Suite completa de tests: 252/252 SUCCESS** (Karma + ChromeHeadless).
- **Build de producción: OK** (35s, sin errores de compilación).
- ⚠️ **Warning de budget:** bundle inicial **461.79 kB** vs presupuesto máximo de aviso 300 kB (excede en 161 kB). No bloquea, pero degrada el primer paint.
- Hallazgo menor: `angular.json` tiene el target `test` **definido dos veces** (claves duplicadas; el CLI usa la última).

---

## 6. Infraestructura y servicios

- `docker compose config --quiet` → **válido** (compose dev y prod).
- Servicios activos en la máquina:
  - PostgreSQL **5432** (BD `gams_pip`) ✅
  - Redis **6379** ✅
  - Django `runserver 127.0.0.1:8000` — ⚠️ **arrancado el 15/08 21:43 con `--noreload`**: sirve código de ayer; **requiere reinicio** para tomar cambios de hoy.
  - Angular `ng serve` **4200** ✅
- Nota: nombres de contenedores renombrados a `pip-*` (commit 7a690fd); los volúmenes persisten.

---

## 7. Deuda técnica y riesgos priorizados

| # | Prioridad | Hallazgo | Impacto |
|---|---|---|---|
| 1 | **ALTA** | Login: credenciales del seed no válidas + usuarios sin roles | Sin sesión, no se puede operar |
| 2 | **ALTA** | Test fallido: matriz completa 2027 sin cadena operacional | Reportes POAU 2027 incompletos |
| 3 | **MEDIA** | `UnorderedObjectListWarning` (paginación sin `ordering`) | Resultados de paginación inconsistentes |
| 4 | **MEDIA** | Bundle inicial 461 kB > 300 kB | Rendimiento del primer paint |
| 5 | **MEDIA** | Suite backend 16m42s | Fricción en CI/desarrollo |
| 6 | **BAJA** | `angular.json` target `test` duplicado | Higiene de configuración |
| 7 | **BAJA** | `ArticulacionPADPEI` e `IndicadorCadena` vacíos | Cadena PAD→PEI sin poblar (fuente XLSX externa) |
| 8 | **INFO** | Deuda funcional del plan maestro (§11 FINAL_REPORT): wizards PEI/POA/POAU, motor visual PAD→PEI, dashboards/BI | Roadmap de producto |

---

## 8. Refactor pendiente recomendado (en orden)

1. **Consolidar paginación ordenada** (DRF `OrderingFilter` + `ordering` en querysets clave) — elimina los 391 warnings y el riesgo de paginación. Bajo riesgo, alto valor.
2. **Arreglar el seed/demo de la matriz 2027** — desbloquea el test fallido y los reportes POAU.
3. **Sanear configuración frontend** (target `test` duplicado, budgets realistas o bundle splitting por features).
4. **Revisar el flujo de alta de usuarios/roles** (¿por qué los 4 usuarios están sin roles? ¿el seed no corrió completo?).
5. **Acelerar la suite** (pytest-xdist, marcas de integración, DB compartida).
6. **Avanzar el cutover V1→V2** con la palanca `LEGACY_MENU_VISIBLE` por dominio (el plan maestro ya define el orden).

No se detectó necesidad de refactor estructural: la migración a 9 esquemas PIP está ejecutada y los bounded contexts (SIS-PE/SIS-POA/SIS-PRO/núcleo) están delimitados y documentados.

---

*Reporte generado con evidencia ejecutada el 2026-08-16. Fuentes: suites pytest (1252), karma (252), inventario de esquemas/datos en `gams_pip`, pruebas HTTP en vivo, `manage.py check`, `docker compose config`.*
