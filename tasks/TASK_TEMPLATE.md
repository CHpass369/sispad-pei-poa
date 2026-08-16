# Task Template

Copia este archivo como `{ID}-{slug-descriptivo}.md` en `tasks/backlog/`, completa TODAS las secciones y muévelo a `tasks/active/` al iniciar el trabajo.

# TASK {TASK ID}: {TITLE}

## DOMINIO

`core` | `sis-pe` | `sis-poa` | `sis-pro` | `core/infra` | otro

## OBJECTIVE

Qué se logra con esta tarea, en una o dos oraciones verificables.

## CONTEXT

Estado actual del dominio y del código relevante: dónde vive la falla o el hueco, qué artefactos existen, qué antecedentes aplican. Referencias a documentación (`docs/architecture/`, `docs/refactor-pip/`) y a código con rutas reales.

## CURRENT BEHAVIOR

Qué hace hoy el sistema, con evidencia (rutas de archivo, líneas, datos).

## EXPECTED BEHAVIOR

Qué debe hacer después de la tarea, en términos verificables.

## IN SCOPE

- [ ] ítem 1
- [ ] ítem 2

## OUT OF SCOPE

- ítem 1
- ítem 2

## INVARIANTS

Propiedades que la tarea NO puede romper (contratos, esquemas, tests existentes).

## DATABASE IMPACT

`ninguno` o: tablas/columnas afectadas, tipo de cambio (migración nueva, data migration), estrategia de datos.

## API IMPACT

`ninguno` o: endpoints afectados (V1/V2), cambios de contrato, headers de deprecación.

## FRONTEND IMPACT

`ninguno` o: features/componentes afectados, rutas, contrato de llamadas.

## FILES EXPECTED

- `ruta/archivo` — qué se hace (crear/modificar/eliminar)

## DEPENDENCIES

Tareas o prerrequisitos previos; `ninguna` si no aplica.

## ACCEPTANCE CRITERIA

- [ ] criterio 1 (verificable, sin ambigüedad)
- [ ] criterio 2

## TESTS

Comandos reales de verificación:

```bash
cd backend; python -m pytest <ruta_o_kw>
cd frontend/sispoa; npm test -- --watch=false
```

## RISKS

Riesgos, impacto en otros módulos y mitigaciones.

## ROLLBACK

Pasos concretos para revertir si la tarea falla (revert de commit, migración de reversa, restore).

## FINAL REPORT

Completar al cerrar con `/task-close`: archivos modificados, creados, migraciones, endpoints, tests ejecutados, riesgos, deuda detectada, trabajo pendiente.

---

## Instrucciones de uso

### Nomenclatura

| Prefijo | Alcance |
|---|---|
| `PIP-CORE-###` | Núcleo transversal (core, organizacion, territorio, workflow, documentos, auditoría) |
| `PIP-PE-###` | SIS-PE (planificación estratégica, PAD, PEI, articulación) |
| `PIP-POA-###` | SIS-POA (POA/POAU, presupuesto, techos, seguimiento) |
| `PIP-PRO-###` | SIS-PRO (cartera, preinversión, ejecución) |
| `PIP-DB-###` | Cambios de base de datos (esquemas, migraciones, datos) |
| `PIP-UI-###` | Frontend (features, componentes, estilos) |
| `PIP-ARCH-###` | Arquitectura e infraestructura (docs, CI/CD, tooling) |

### Ciclo de vida

1. Crear la tarea en `tasks/backlog/` con el template completo.
2. Al iniciar el trabajo, moverla a `tasks/active/`.
3. Al terminar, cerrarla solo vía `/task-close`, que verifica: acceptance criteria, tests, build, review, scope y documentación. Recién entonces se mueve a `tasks/completed/` con el FINAL REPORT completo.
