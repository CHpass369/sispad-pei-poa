# ADR-002 — SIS-POA como bounded context de planificación operativa anual

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-005, ADR-006, ADR-007; plan maestro §13; `DOMAIN_MAP.md` §1, §3

## Contexto

El SIS-POA actual es el corazón operativo del sistema, pero sus modelos están dispersos en varias apps con fronteras difusas: `gestion` (gestión fiscal legacy), `techos` (legacy), `presupuesto` (legacy), `budget` (V2), `recursos`, `poau` (legacy + jerarquía canónica V2), `articulacion` (contenidos POA/POAU legacy), `seguimiento`, `modificaciones`, `planificacion` (AccionCortoPlazo) e `indicadores` (jerarquía operativa duplicada). A la vez, `articulacion` mezcla contenido estratégico (PAD/PEI) con operativo, y `catalogos`/`normativa` mezclan catálogos maestros con lógica de negocio.

Sin una frontera clara, los catálogos maestros, la estrategia y lo operativo conviven en las mismas apps y tablas, dificultando el cutover V2 y la trazabilidad PEI → POA.

## Decisión

1. **SIS-POA es SOLO planificación operativa anual.** Su alcance funcional comprende:
   - gestión fiscal y habilitación de la gestión (`budget.FiscalYear`; legacy `gestion.GestionFiscal`, MERGE pendiente);
   - techos (`budget.DirectiveCeiling`; legacy `techos.*` se DEPRECATE);
   - distribución (`DistribucionVersion`, `DistribucionTerritorial`, `AsignacionTerritorial`);
   - asignación (`Apertura`, `AperturaFuente`, categoría programática y objeto de gasto);
   - POA y POAU (`poau` V2: PoA → Accion → Operacion → Actividad → Tarea + `Programacion`);
   - programación físico-financiera con validación de techo;
   - consolidación institucional;
   - modificaciones (`modificaciones.SolicitudModificacion` + `budget.Reforma`);
   - seguimiento operativo (`seguimiento.*`).
2. **SIS-POA NO contiene**: catálogos maestros (viven en PIP CATÁLOGOS, ADR-005), estrategia (SIS-PE), ni proyectos (SIS-PRO).
3. **El contenedor físico es el esquema `sis_poa`** (ADR-003), con las tablas de `budget`, `gestion`, `recursos`, `poau`, `seguimiento`, `modificaciones` y los contenidos operativos de `articulacion` (SPLIT) según `SCHEMA_MAPPING.md` §5.
4. **Los legacy `presupuesto` y `techos` se DEPRECATE** a favor de `budget` V2: permanecen técnicamente separados bajo el mismo dominio funcional (plan maestro §13.3), nunca se crea un SIS-PRESUPUESTO (ADR-005).
5. **Jerarquía canónica única**: `operacion → actividad → tarea` de `poau` V2 es la fuente de verdad; los duplicados legacy (`indicadores_operacion/tarea/producto`, `articulacion_*POAU`, `poau_poauactividad`) se retiran tras cutover y reconciliación (REMOVE_LATER / MERGE).

## Consecuencias

Positivas:

- La frontera PEI (estratégico) → POA (operativo) queda explícita: SIS-POA lee versiones aprobadas e inmutables del SIS-PE (ADR-008), nunca tablas de borrador.
- Facilita el cutover V2 por dominio: cada pieza operativa se retira de legacy cuando su equivalente V2 está estable y reconciliado.
- El namespace `/api/v2/sis-poa/` (incluido `sis-poa/budget/`) ya existente se convierte en la única puerta de entrada del contexto.

Negativas:

- El SPLIT de `articulacion` (estratégico → SIS-PE, operativo → SIS-POA, cadena → PIP INTEGRACIÓN) es el cambio más delicado del refactor: requiere mover tablas y reconciliar duplicados con `LegacyMigrationMap` antes de retirar cualquier tabla.
- La duplicación temporal legacy/V2 (fase Expand) convive durante el refactor: exige disciplina para no crear una tercera representación.
- `seguimiento` y `modificaciones` tienen reglas compartidas con SIS-PRO; su contrato de compartición (IDs + versiones) debe definirse antes de mover tablas (notas de decisión de `DOMAIN_MAP.md` §4).

## Alternativas consideradas

1. **SIS-PRESUPUESTO como contexto separado**: descartado por ADR-005: el presupuesto operativo es inseparable del POA (techos, distribución, asignación, programación forman un solo flujo transaccional).
2. **Dejar `articulacion` sin dividir**: descartado: rompe el principio de una sola fuente de verdad y bloquea el cutover V2.
3. **Mantener la jerarquía operativa duplicada en `indicadores`**: descartado: contradice la jerarquía canónica única del plan maestro §13.2.
