# PIP INTEGRACIÓN — Frontera del bounded context de articulación

- **Fecha:** 2026-08-15
- **Fase:** 5 del refactor SISPOA→PIP (motor de articulación)
- **Relacionado con:** ADR-004, ADR-008, ADR-002; `DOMAIN_MAP.md` §2; `SIS_PE_BOUNDED_CONTEXT.md`; `SIS_POA_BOUNDED_CONTEXT.md`

## 1. Propósito

Definir QUÉ pertenece al contexto **PIP INTEGRACIÓN** (la cadena que une
estratégico y operativo: PAD → PEI → POA → POAU), QUÉ NO, cómo navegarla
(descendente y ascendente) y qué deuda técnica arrastra. Es la frontera del
**Motor de Articulación PIP** que FASE 5 entrega: el servicio de dominio que
hace consultable la trazabilidad estratégica y presupuestaria por FK reales
(plan maestro §28, §83-84; ADR-004).

## 2. Frontera del contexto

### 2.1 Qué pertenece a PIP INTEGRACIÓN

| Pieza | Ubicación actual | Rol en PIP INTEGRACIÓN |
|---|---|---|
| Cadena codificable PAD→PEI→POA→POAU (`ResultadoPAD`, `ProductoPAD`, `ResultadoPEI`, `ProductoPEI`, `AccionPOA`, `OperacionPOAU`, `ActividadPOAU`, `TareaPOAU`) | `apps.articulacion` | **Columna vertebral de la cadena**: los 8 modelos con código oficial segmentado (`CodigoSegmentadoModel`) |
| Articulación PAD↔PEI (`ArticulacionPADPEI`) | `apps.articulacion` | Arco real entre `ProductoPAD` y `ProductoPEI` (FK reales, ADR-004; destino futuro `pip_integracion.articulacion_pad_pei`) |
| `IndicadorCadena` | `apps.articulacion` | Indicadores a lo largo de la cadena (meta 2030, inversiones por gestión) |
| `AcuerdoInternacional`, `Normativa`, `ActividadNormativa`, `TareaNormativa`, `CodigoNivel` | `apps.articulacion` | Marcos normativos y acuerdos que enmarcan la cadena |
| `SeguimientoPresupuesto`, `AsignacionObjetoGasto` | `apps.articulacion` | Trazabilidad presupuestaria de la cadena (SIS-POA funcional; contenedor técnico en `articulacion`) |
| `CodificadorService` (16 segmentos: EE.CC.SS.RS.CGEO.LL.RT.PT.ENTI.OE.RI.PI.ACP.OP.ACT.TAR) | `apps.codificacion/services/codificador.py` | Servicio de codificación oficial que da identidad a cada eslabón; NO se mueve, es el pegamento de la cadena |
| **MotorArticulacion** (NUEVO, FASE 5) | `apps.articulacion/services/motor.py` | Servicio de dominio de navegación: `cadena_descendente`, `cadena_ascendente`, `trazar_instrumento` (V2) |

### 2.2 Qué NO pertenece a PIP INTEGRACIÓN

| Pieza | Destino real |
|---|---|
| Catálogos base EE.CC.SS.RS.CGEO.LL (`EjePGDESA`, `ComponentePDESA`, `SectorEconomico`, `ResultadoSectorial`, `EntidadTerritorialCGEO`, `EntidadCodificadora`, `LineamientoPAD`, `SecuenciaCodigo`, `HomologacionCodigo`, `VersionCatalogoPlan`) | **PIP CATÁLOGOS** (`apps.codificacion`) |
| Kernel V2 de instrumentos (`InstrumentoPlanificacion`, `VersionInstrumento` inmutable, `NodoEstrategico`, `VinculoEstrategico`, `TipoInstrumento`, `VersionMetodologia`, `TipoNodoEstrategico`, `TipoVinculoEstrategico`) | **SIS-PE** (`apps.planificacion/models_v2.py`; ADR-008) |
| PAD legacy (`SectorPAD` → `PoliticaPAD` → `LineamientoEstrategico` → `ResultadoTerritorial` → `ProductoTerritorial` → `ProgramacionAnualPAD`, `ArticulacionSIPEB`) | **SIS-PE** (`apps.pad`; cutover V2 pendiente) |
| Jerarquía V2 canónica (`PoA`, `Accion`, `Operacion`, `Actividad`, `Tarea`, `Programacion`) | **SIS-POA** (`apps.poau`; ADR-002) |
| Presupuesto (`budget.*`, `gestion.*`, `techos.*`, `presupuesto.*`) | **SIS-POA** (ADR-005) |
| Proyectos (`inversion.*`) | **SIS-PRO** |

### 2.3 Ambigüedad declarada: `AccionPOA` en `articulacion` vs SIS-POA

`AccionPOA` (y sus descendientes POAU y el seguimiento presupuestario) vive
en `apps.articulacion` pero **representa el nivel POA del SIS-POA** (ADR-002).
Es deuda técnica estructural: el contenedor técnico quedó donde nació el
código (la app de articulación) porque la jerarquía canónica V2 del SIS-POA
(`poau`) aún no hace cutover y el código oficial segmentado
(`CodigoSegmentadoModel` + `CodificadorService`) se calcula sobre estos
modelos. **Decisión (FASE 5): se mantienen en `articulacion` hasta el SPLIT
funcional** — moverlos ahora rompería la codificación oficial sin ganancia.
El motor navega el nivel POA del SIS-POA tal como está materializado hoy.

## 3. Cadena maestra PGDESA → PDESA → PAD → PEI → POA → POAU → Proyecto

Fuente: `DOMAIN_MAP.md` §2, verificada contra los modelos (FASE 5).

| Eslabón | Instrumento | Modelos reales |
|---|---|---|
| PGDESA | Marco nacional | `codificacion.EjePGDESA`, `codificacion.ComponentePDESA` |
| PDESA | Marco sectorial | `codificacion.SectorEconomico`, `codificacion.ResultadoSectorial`, `codificacion.EntidadTerritorialCGEO` |
| PAD | Plan Autonómico (SIS-PE) | legacy `pad.SectorPAD → PoliticaPAD → LineamientoEstrategico → ResultadoTerritorial → ProductoTerritorial`; cadena codificable `articulacion.ResultadoPAD → ProductoPAD` (segmentos RT, PT) |
| PEI | Plan Estratégico Institucional (SIS-PE) | kernel V2 `planificacion.InstrumentoPlanificacion + VersionInstrumento + NodoEstrategico/VinculoEstrategico`; cadena codificable `articulacion.ResultadoPEI → ProductoPEI` (RI, PI) + arco `articulacion.ArticulacionPADPEI` + `IndicadorCadena` |
| POA | Plan Operativo Anual (SIS-POA) | V2 `poau.PoA → Accion`; cadena codificable `articulacion.AccionPOA` (ACP; además `planificacion.AccionCortoPlazo` legacy) |
| POAU | Operaciones anuales (SIS-POA) | V2 `poau.Operacion → Actividad → Tarea + Programacion`; cadena codificable `articulacion.OperacionPOAU → ActividadPOAU → TareaPOAU` (OP, ACT, TAR) |
| Proyecto | Inversión (SIS-PRO) | `inversion.Proyecto` + `VinculoProyectoActividad` hacia el SIS-POA (contrato explícito, ADR-004) |

Encadenamiento en la cadena codificable (FK reales, FASE 5):

```
ResultadoPAD ──< ProductoPAD ── ArticulacionPADPEI ──> ProductoPEI ──> ResultadoPEI
                                                              │
                                                              └─< AccionPOA ──< OperacionPOAU ──< ActividadPOAU ──< TareaPOAU
```

## 4. Cómo navegar la cadena

### 4.1 Descendente (trazabilidad estratégica hacia abajo)

`MotorArticulacion.cadena_descendente('ResultadoPAD', <uuid>)` devuelve la
cadena completa en orden canónico (RT → PT → RI → PI → ACP → OP → ACT → TAR):
`ResultadoPAD → ProductoPAD → ResultadoPEI → ProductoPEI → AccionPOA →
OperacionPOAU → ActividadPOAU → TareaPOAU`.

- El tramo PAD→PEI se resuelve por las FK reales de `ArticulacionPADPEI`
  (no por coincidencia de códigos).
- Cuando el PEI se alcanza desde el PAD, solo se emiten los productos PEI
  efectivamente vinculados (columna vertebral); partiendo del propio
  `ResultadoPEI` se emiten todos sus productos.
- Formato de cada eslabón: `{nivel, entidad_tipo, entidad_id, codigo,
  denominacion, gestion}`.

### 4.2 Ascendente (trazabilidad presupuestaria hacia arriba)

`MotorArticulacion.cadena_ascendente('TareaPOAU', <uuid>)` devuelve el
camino inverso: `TareaPOAU → ActividadPOAU → OperacionPOAU → AccionPOA →
ProductoPEI → ResultadoPEI → ProductoPAD → ResultadoPAD`, reutilizando el
contexto canónico de `CodificadorService._contexto` (la navegación por FK
que ya usa el codificador, sin duplicarla). Si la articulación PAD-PEI es
ambigua, la cadena asciende hasta PEI y se corta: el motor no inventa un
padre (ADR-004).

### 4.3 Kernel V2 (SIS-PE)

`MotorArticulacion.trazar_instrumento(instancia)` acepta objetos del kernel
V2 (`NodoEstrategico` / `VinculoEstrategico`) y devuelve instrumento,
versión (estado/inmutabilidad) y vínculos entrantes/salientes — los arcos
pueden cruzar instrumentos (ADR-008).

### 4.4 Robustez

Tipo fuera de la cadena, entidad inexistente o instancia ajena al kernel V2
→ la salida es `[]` (decisión FASE 5: el motor nunca lanza por datos
ausentes; las excepciones quedan reservadas a la validación del
`CodificadorService`).

## 5. ADR-004: por qué NO polimorfismo genérico

La cadena usa **tablas de articulación específicas con FK reales**
(`ArticulacionPADPEI`, `vinculo_estrategico` V2, `VinculoProyectoActividad`)
en lugar de `source_type` + `source_id`: la base rechaza vínculos huérfanos o
inválidos y la trazabilidad es consultable por FK (plan maestro §14.2). El
patrón `tipo + id` genérico queda reservado a usos transversales no críticos
(workflow, auditoría) con validación explícita en el servicio — y el
`MotorArticulacion` resuelve tipos contra el catálogo de la cadena y verifica
existencia antes de navegar.

## 6. Deuda técnica

1. **Enlace semántico por código + gestión en `cadena_completa` de `pad`
   (frágil)** — `pad/views.py:98` resuelve PAD→PEI buscando `NodoPlanificacion`
   con `codigo__icontains=resultado.codigo`. No usa FK: es la fuente legada
   para PAD (la doc FASE 5 no la toca), pero el motor ya no depende de ella.
2. **`AccionPOA` en `articulacion` vs SIS-POA** — ver §2.3; se mantiene por
   `CodigoSegmentadoModel` hasta el SPLIT funcional.
3. **0 filas de `ArticulacionPADPEI` en la BD actual** — la cadena PAD→PEI
   no está poblada: los eslabones PAD y PEI existen por separado, pero el
   arco que el motor atraviesa (y que `CodificadorService` exige para el
   tramo PEI→PAD) no tiene datos. El `MotorArticulacion` navega el tramo que
   hay y se corta donde no hay arco (no inventa nada).
4. **`ArticulacionPADPEI` hereda el estado del código** — la inmutabilidad
   oficial hace que los vínculos PAD-PEI no sean modificables una vez
   codificada la cadena (consecuencia del ADR-004 + inmutabilidad FASE T3):
   el flujo de re-articulación aún no tiene estrategia definida.

## 7. Verificación FASE 5

Ejecutada el 2026-08-15:

- **Identidad**: `apps.articulacion` registrada con su AppConfig
  (`apps.articulacion.apps.ArticulacionConfig`) en `config/settings.py` y
  `config/settings_test_sqlite.py`; `verbose_name` = "PIP INTEGRACIÓN -
  Articulación" (label intacto). Nota: el mojibake reportado
  (`ArticulaciA3n`) no estaba en disco al inicio de la fase; se aplicó
  igualmente el rename de identidad.
- **Motor**: `MotorArticulacion` nuevo en
  `apps/articulacion/services/motor.py` (`services.py` se convirtió en
  paquete `services/` preservando `registrar_auditoria`); 10 tests en
  `apps/articulacion/tests/test_motor_articulacion.py` (cadena completa
  descendente/ascendente, casos vacíos, smoke de datos reales con skip
  cuando la BD no está sembrada, trazado V2).
- **Suite**: `pytest apps/articulacion/ apps/codificacion/
  --ds=config.settings` en PostgreSQL local — sin regresiones;
  `manage.py check` sin issues; `ng build --configuration development`
  del frontend OK.
