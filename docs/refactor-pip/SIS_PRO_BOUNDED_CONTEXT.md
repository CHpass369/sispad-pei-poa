# SIS-PRO — Frontera del bounded context del ciclo de proyectos

- **Fecha:** 2026-08-15
- **Fase:** 6 del refactor SISPOA→PIP (aislar el ciclo de proyectos)
- **Relacionado con:** ADR-002, ADR-010; `DOMAIN_MAP.md` §1, §4; `SCHEMA_MAPPING.md` §6; `SIS_POA_BOUNDED_CONTEXT.md` (FASE 4), `PIP_INTEGRACION_BOUNDED_CONTEXT.md` (FASE 5)

## 1. Propósito

Definir QUÉ pertenece al contexto **SIS-PRO** (ciclo del proyecto: cartera,
preinversión, condiciones previas, costos, cronogramas, vínculo con el POA),
QUÉ NO, el flujo del ciclo de proyectos (plan maestro §25) con los modelos
reales de `apps.inversion`, y el contrato de integración con SIS-POA
(plan maestro §26 y §48) que la FASE 6 materializa en
`services/integracion_poa.py`. Es la frontera de la FASE 6: el código acoplado
NO se mueve, solo se fija la identidad del contexto y el contrato de consumo.

## 2. Frontera del contexto

### 2.1 Qué pertenece a SIS-PRO

| Pieza | Ubicación real (`apps.inversion`) | Rol en SIS-PRO |
|---|---|---|
| Proyecto (cartera V2) | `models_v2.Proyecto` (`proyecto`): fases, estados, tipología RM 115, geometría, presupuestos, `puntaje_madurez`, `habilitado_poa`, `codigos_externos` | Entidad raíz del ciclo; `FasesProyecto` ordena idea → … → evaluación |
| Expediente de preinversión (SISPRE / RM 115) | `models_preinversion`: `ITCP`, `CondicionITCP`, `TDR` + `ActividadTDR`/`ProductoTDR`/`PersonalTDR`/`ItemPresupuestoTDR` | Estados `EstadosExpedientePreinversion` (registrada → … → viable) |
| EDTP y estudios | `models_preinversion`: `EDTP`, `SeccionEDTP`, `EstudioTecnico`, `ItemCostoEDTP`, `FuenteFinanciamientoEDTP`, `ItemCronograma`, `PlanOperacionMantenimiento`, `IndicadorEvaluacionEDTP` | Expediente técnico dinámico por tipología, viabilidad y financiamiento |
| Condiciones previas | `models_v2.CondicionPrevia`, `models_v2.DocumentoTecnico`, `models_v2.CostoProyecto` | Documentos y costos previos a la contratación |
| Vínculo con el POA | `models_v2.VinculoProyectoActividad` (FK real a `poau.Actividad`) | Trazabilidad ascendente Proyecto → POA → PEI → PAD (cadena del plan §14.2) |
| Alternativas y beneficiarios | `models_preinversion`: `AlternativaProyecto`, `ComponenteProyecto`, `GrupoBeneficiario` | Análisis de alternativas y componentes del proyecto |
| Reformulación | `models_preinversion.SolicitudReformulacion` (con `sistema_origen`) | Solicitudes originadas por SIS-POA u otros sistemas |
| Revisión y aprobación | `models_preinversion`: `RevisionPreinversion`, `ObservacionPreinversion`, `AprobacionPreinversion` | Observaciones/severidades y aprobaciones del expediente |
| Documentos del expediente | `models_preinversion`: `DocumentoPreinversion`, `VersionDocumentoPreinversion`, `DocumentoGenerado` | Documentos versionados y generados (plantillas DOCX) |
| Interoperabilidad (a migrar a PIP INTEGRACIÓN) | `models_preinversion`: `ReferenciaExterna`, `EventoOutbox`, `MensajeEntrante` | Vínculos con sistemas externos (SIS-PE, SIS-POA, SIS-PRO, SISFIN) y outbox |
| Servicios de dominio | `services/__init__.py` (legacy `ProyectoInversion`), `services_preinversion.py`, `services/integracion_poa.py` | Lógica de dominio: madurez, clasificación, paquetes, contrato SIS-POA |

### 2.2 Qué NO pertenece a SIS-PRO

| Pieza | Destino real |
|---|---|
| POA/POAU y jerarquía operativa (`poau.*`: PoA → Acción → Operación → Actividad → Tarea, programación físico-financiera) | **SIS-POA** (FASE 4, ADR-002); SIS-PRO solo las LEE por contrato |
| Ciclo presupuestario (`gestion`, `techos`, `presupuesto`, `budget`, `modificaciones`, `seguimiento`, `recursos`) | **SIS-POA** (FASE 4) |
| Articulación PAD-PEI-POA-POAU y motor de cadena (`articulacion.*`, `MotorArticulacion`) | **PIP INTEGRACIÓN** (FASE 5) |
| Planificación estratégica, PAD/PEI, kernel V2 (`planificacion.*`, `pad.*`) | **SIS-PE** (FASE 3) |
| Catálogos maestros y normativa (`catalogos.*`, `normativa.*`) | **PIP CATÁLOGOS** (ADR-005) |
| Codificación oficial (`codificacion.CodigoSegmentadoModel` + `CodificadorService`) | **Infraestructura compartida PIP** — NO se mueve |
| Evaluación de proyectos (`evaluacion.Evaluacion`, …) | Compartido **SIS-PE / SIS-PRO** (decisión; hoy en namespace `sis-pe`) |

## 3. Flujo del ciclo de proyectos (plan maestro §25)

Secuencia con los modelos reales de `apps.inversion` (fases `FasesProyecto`
= idea → condiciones_previas → preinversion → formulacion → costos →
revision → contratacion → ejecucion → supervision → cierre → evaluacion):

| # | Etapa | Modelos reales de SIS-PRO | Notas |
|---|---|---|---|
| 1 | Identificación | `Proyecto` (fase `idea`), `ProyectoTerritorio`, `codigos_externos`/`etiquetas` | Demanda/idea capturada; territorio y etiquetas |
| 2 | Registro | `Proyecto` (gestion, ue, responsable, `tipologia_rm115`), `clasificar_tipologia` | Alta del expediente; `estado_preinversion = registrada` |
| 3 | Vinculación POA | `VinculoProyectoActividad` (FK real a `poau.Actividad`), `IntegracionPoaContract` (§4), `calcular_madurez` → `habilitado_poa` | SIS-PRO lee actividades del SIS-POA por contrato y vincula su proyecto |
| 4 | Condiciones previas | `CondicionPrevia`, `DocumentoTecnico`, `CostoProyecto` | Fase `condiciones_previas` |
| 5 | ITCP | `ITCP`, `CondicionITCP` (9 condiciones RM 115), `inicializar_itcp` | Estados `itcp_*`; admisibilidad previa (`en_admisibilidad`/`admitida`) |
| 6 | Preinversión | `TDR` + `ActividadTDR`/`ProductoTDR`/`PersonalTDR`/`ItemPresupuestoTDR`, `AlternativaProyecto`, `ComponenteProyecto`, `GrupoBeneficiario` | TDR y presupuesto referencial del EDTP |
| 7 | EDTP | `EDTP`, `SeccionEDTP`, `EstudioTecnico`, `ItemCostoEDTP`, `FuenteFinanciamientoEDTP`, `ItemCronograma`, `PlanOperacionMantenimiento`, `IndicadorEvaluacionEDTP` | Estados `edtp_*` → `viable`; `validar_edtp_para_aprobacion` |
| 8 | Contratación | `DocumentoPreinversion`, `VersionDocumentoPreinversion`, `DocumentoGenerado`, `AprobacionPreinversion` | Fase `contratacion`; documentos versionados del expediente |
| 9 | Ejecución | Fase `ejecucion` + `CostoProyecto`, `DocumentoTecnico` | Seguimiento físico-financiero del proyecto |
| 10 | Seguimiento | Fase `supervision` + `RevisionPreinversion`, `ObservacionPreinversion`, `AprobacionPreinversion` | Revisión técnico-financiera-legal; observaciones con severidad |
| 11 | Cierre | Fase `cierre` | Recepción/cierre del proyecto |
| 12 | Evaluación | Fase `evaluacion` + `evaluacion.Evaluacion` (compartido) | Evaluación de resultados del proyecto |

## 4. Contrato de integración SIS-PRO ↔ SIS-POA (plan maestro §26, §48)

`backend/apps/inversion/services/integracion_poa.py` — `IntegracionPoaContract`:

| Método | Qué hace | Dirección |
|---|---|---|
| `actividades_poa_disponibles(gestion)` | Lee actividades del SIS-POA de la gestión (id, codigo, denominacion, unidad) vía `poau.Actividad` (jerarquía canónica PoA → Acción → Operación → Actividad, ADR-002) | Lectura de poau |
| `vincular_proyecto_a_actividad(proyecto, actividad_id, usuario)` | Valida la actividad (ValidationError si no existe), crea `VinculoProyectoActividad` (modelo propio de inversion); idempotente | Escritura en inversion |
| `proyectos_de_actividad(actividad_id)` | Vínculos con proyecto de una actividad (lectura pura) | Lectura de inversion |
| `paquete_transferencia_poa(proyecto)` | Paquete de solo lectura hacia SIS-POA (JSON + GeoJSON + documentos); delega en `construir_paquete_transferencia` de `services_preinversion` | Exportación |

Reglas del contrato:

- **SIS-PRO nunca escribe en tablas internas de `poau` / `articulacion` / `budget`**: las escrituras del contrato ocurren solo en modelos de `apps.inversion`.
- La relación POA/POAU → Proyecto es vía `VinculoProyectoActividad` (FK real a `poau.Actividad`, `models_v2.py:296-299`), nunca por acceso directo a otras tablas operativas.
- El paquete de transferencia y el outbox (`EventoOutbox`, `MensajeEntrante`) son contratos: su deprecación requiere que AMBOS lados migren (`LEGACY_DEPRECATION.md` §3), nunca unilateralmente.
- `usuario` en `vincular_proyecto_a_actividad` queda reservado para la auditoría de PIP INTEGRACIÓN (fase futura); el vínculo no persiste al autor.

## 5. Legacy: `sistema_origen='SISPOA'`

`SolicitudReformulacion.sistema_origen` (`models_preinversion.py:194`) tenía
`default='SISPOA'`; la FASE 6 cambia el default a `'SIS-POA'` (el sistema
operativo POA = SIS-POA). **Las filas existentes con `'SISPOA'` NO se tocan**:
son datos históricos (valor KEEP según `LEGACY_DEPRECATION.md` #15), el
mapeo a la identidad nueva se resuelve en la fase de datos
(`DATA_MIGRATION_PLAN.md`) y las etiquetas de display pasan a "SIS-POA".
El cambio de default no genera migración de esquema (CharField), verificado
con `makemigrations --check`.

## 6. Identidad del contexto (FASE 6)

- `apps/inversion/apps.py` → `InversionConfig`: `name='apps.inversion'`,
  `default_auto_field='django.db.models.BigAutoField'`,
  `verbose_name='SIS-PRO - Ciclo de Proyectos'`.
- `config/settings.py` → `'apps.inversion.apps.InversionConfig'` (label intacto
  `inversion`: preserva contenttypes y permisos). `settings_test_sqlite.py`
  NO aplica: `inversion` es una app geo (requiere PostgreSQL/PostGIS) y no
  integra la lista de apps no-geo.
- Correcciones semánticas SISPOA → SIS-POA (solo docstrings/etiquetas/default;
  valores persistidos intactos): `models_preinversion.py` (7, 188, 194, 792),
  `models_v2.py:91` (etiqueta de choice; el valor `enviado_poa` no cambia),
  `services_preinversion.py` (4, 182, 237).
- `services.py` (módulo) → `services/__init__.py` (paquete, `git mv`):
  habilita `services/integracion_poa.py` sin romper imports.

## 7. Deuda técnica registrada

1. **Artefactos de integración en SIS-PRO**: `EventoOutbox`, `MensajeEntrante`,
   `ReferenciaExterna` y el outbox de preinversión deberían vivir en PIP
   INTEGRACIÓN (`DOMAIN_MAP.md` §4, `DATA_MIGRATION_PLAN.md` grupo G); se
   migran en la fase de datos, nunca por renombrado ad-hoc.
2. **Legacy `ProyectoInversion` (V1)**: `apps/inversion/models.py` + `services/__init__.py`
   (crear_proyecto, cambiar_estado, validar_tecnico, programaciones) conviven
   con el V2; DEPRECATE tras cutover del dominio (`cutover.config.ts`, orden de
   retiro: inversion).
3. **Datos persistidos**: `sistema_origen='SISPOA'` en filas viejas de
   `SolicitudReformulacion` y perfiles `SISPOA_GASTOS_*` de `Importacion` son
   datos, no código: renombrar requiere backfill con plan
   (`AUDITORIA_SISPOA.md` §3.3, `LEGACY_DEPRECATION.md` #15).
4. **Cadena PAD→PEI sin poblar**: `ArticulacionPADPEI` = 0 filas en BD real
   (deuda de FASE 5); la trazabilidad ascendente Proyecto → POA → PEI → PAD
   queda incompleta hasta que el wizard de articulación la alimente.
5. **`usuario` en el contrato**: `vincular_proyecto_a_actividad` recibe el
   autor pero aún no registra auditoría; se conecta a PIP INTEGRACIÓN cuando
   exista el servicio de auditoría de contratos.
