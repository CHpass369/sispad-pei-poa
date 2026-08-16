---
name: sis-poa
description: "Use when: SIS-POA, POA, POAU, plan operativo anual, gestión fiscal, GestionFiscal, techos presupuestarios, distribuciones, asignaciones, clasificadores, presupuesto, categoría programática, reformas, modificaciones, seguimiento, recursos, budget."
---

# SIS-POA — Planificación Operativa

## Propósito

Planificación operativa anual: POA/POAU, presupuesto, techos, distribuciones, asignaciones, programación y seguimiento. Techos, distribuciones y asignaciones son funcionalidades de SIS-POA, no sistemas independientes.

## ESTADO ACTUAL

### Apps y canonicidad

| App | Estado | Contenido |
|---|---|---|
| gestion | V1+V2 | GestionFiscal: fuente canónica del periodo fiscal. Usar FK, nunca PositiveIntegerField suelto de año. |
| budget | V2 CANÓNICO | DirectiveCeiling, ProgrammaticCategory, Allocation, Reform (tablas presupuesto_*, modelos en inglés). Nuevos desarrollos de presupuesto van AQUÍ. |
| poau | V1+V2 | POA/POAU operativo. |
| techos | V1 LEGACY | TechoPresupuestario (techos_*). No extender; migrar a budget. |
| presupuesto | V1 LEGACY | ProgramaPresupuestario, CategoriaProgramatica (presupuesto_* V1). No extender; migrar a budget. |
| modificaciones | V1 | Modificaciones presupuestarias (legacy). |
| seguimiento | V1 | Seguimiento operativo. |
| recursos | V1 | Recursos (legacy). |

## Reglas

- Nuevos desarrollos de techos, distribuciones, asignaciones, clasificadores y reformas → app budget V2 (inglés, db_table presupuesto_*), NO techos/presupuesto legacy.
- Categoría programática duplicada: V1 (CategoriaProgramatica) vs V2 (ProgrammaticCategory). Usar V2.
- Techo duplicado: techos_* (V1) vs presupuesto_techo_* (V2). No crear referencias nuevas a V1.
- Reforma V2 vs modificaciones V1: conceptos solapados; consultar DUPLICATION_ANALYSIS.md antes de modelar.
- Los clasificadores de programación se apoyan en catálogos de `catalogos` (catalogo_*) y codificación oficial de `codificacion`.

## ARQUITECTURA OBJETIVO

- budget V2 como único dueño del ciclo presupuestario (techos → distribuciones → asignaciones → reformas).
- GestionFiscal como raíz canónica del periodo; todo elemento presupuestario se ata a ella por FK.
- Depende de CORE (organización, territorio, normativa, workflow) y de SIS-PE vía articulación (motor articulacion), por contratos.
- Retiro de techos/presupuesto/modificaciones V1 por tarea aprobada; V1 queda legacy con Sunset 2027-01-01.

## Riesgos

- Duplicar TechoPresupuestario al crear entidades de budget sin consultar DUPLICATION_ANALYSIS.md.
- Atar elementos a un año suelto en lugar de FK a GestionFiscal.
- Mezclar nomenclatura en inglés (budget V2) con la legacy en español sin señalar la deuda.
