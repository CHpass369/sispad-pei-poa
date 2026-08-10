# ADR-005 — Preinversión (ITCP/TDR/EDTP) dentro del SIS-PRO V2

- **Fecha:** 2026-08-10
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-002, ADR-004; plan maestro §5.4, §14

## Contexto

La base SISPRE (Sistema de Información de Preinversión) define el ciclo de
preinversión municipal: iniciativas, admisibilidad, ITCP, TDR y presupuesto
referencial del EDTP, EDTP dinámico por tipología RM 115, banco de proyectos
viables y transferencia a SISPOA. PIP-GAMS ya posee SIS-PRO V2 en
`apps/inversion` con el ciclo del proyecto (11 fases) y trazabilidad
ascendente.

Se decidió integrar el dominio SISPRE dentro de SIS-PRO V2 en lugar de crear
un sistema independiente con base de datos propia.

## Decisión

1. **Ubicación:** el dominio de preinversión vive en `apps/inversion`
   (`models_preinversion.py`, `services_preinversion.py`,
   `serializers_preinversion.py`, `views_preinversion.py`,
   `section_catalog.py`, `documentos_preinversion.py`), extendiendo el modelo
   `Proyecto` V2 con tipología RM 115, geometría, presupuestos, puntaje de
   madurez y estado del expediente.
2. **Una sola base:** se mantiene la base PostgreSQL/PostGIS de PIP-GAMS
   (ADR-001). No se crea esquema ni base separada.
3. **API:** todo se expone bajo `/api/v2/sis-pro/` (ADR-002). Los estados del
   expediente y la tipología son `TextChoices` versionados, no catálogos en
   tablas, para no duplicar el catálogo normativo.
4. **Documentos:** generación DOCX con `docxtpl` y plantillas versionadas en
   `backend/templates/docx/`; conversión PDF opcional con LibreOffice
   headless. Los archivos se almacenan con hash SHA-256 y versionado por
   documento.
5. **Permisos:** reutiliza capacidades IAM existentes
   (`sis_pro.project.create/edit`, `sis_pro.preinvestment.validate`).
6. **Integración con SISPOA:** paquete de transferencia JSON + GeoJSON de
   solo lectura y patrón Outbox (`EventoOutbox`) para eventos confiables.

## Consecuencias

- El SIS-PRO V2 se convierte en el sistema de proyectos del ciclo completo,
  incluida la preinversión; no se agrega un sistema externo SISPRE.
- La reformulación solicitada por SISPOA crea `SolicitudReformulacion` y no
  altera el EDTP aprobado.
- `Proyecto` V2 crece en campos; se mantienen las fases del ciclo original y
  se agrega `estado_preinversion` como sub-flujo de la fase de preinversión.
- Pendientes para producción: plantillas institucionales definitivas, firma
  digital y validación jurídica de los flujos.
