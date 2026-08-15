# ADR-001 — PIP como plataforma raíz (SIS-PE, SIS-POA, SIS-PRO como subsistemas)

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-002, ADR-003, ADR-010; plan maestro §1, §4; `AUDITORIA_SISPOA.md` §2

## Contexto

El proyecto fue construido y desplegado como "SISPOA Sacaba" (identidad visible en login, título, sidebar, header, Django admin, emails, Swagger, endpoint raíz, logs, Celery, servicios Docker, realm Keycloak, bucket MinIO y dominio). Sin embargo, la plataforma ya contiene los tres subsistemas funcionales SIS-PE, SIS-POA y SIS-PRO: el selector de sistemas existe (`sistemas-seleccion.component.ts`), el namespace `/api/v2/{platform,sis-pe,sis-poa,sis-pro,me}` está separado (`urls_v2.py:139-146`) y el header ya se autodenomina "Plataforma Integral de Planificación". La identidad visible quedó a medio migrar (doble identidad, hallazgo 6 de la auditoría).

SISPOA como nombre colisiona semánticamente con SIS-POA: uno es la plataforma completa y el otro un subsistema, lo que impide distinguir "referencia a toda la plataforma" de "referencia al sistema operativo anual".

## Decisión

1. **PIP es la identidad de la plataforma raíz.** SIS-PE, SIS-POA y SIS-PRO son subsistemas dentro de PIP; PIP CORE (IAM, workflow, documentos, notificaciones, organización) y PIP CATÁLOGOS, PIP INTEGRACIÓN, PIP AUDITORÍA, PIP GEO y REPORTES son los soportes transversales.
2. **El renombrado es semántico y por capa**, nunca un replace global `sispoa → pip`. Cada referencia se clasifica según lo que representa (regla de clasificación de la auditoría §2): plataforma → PIP, operativo anual → SIS-POA (se mantiene), estratégico → SIS-PE, ciclo del proyecto → SIS-PRO, infraestructura compartida → PIP CORE, catálogos → PIP CATÁLOGOS, articulación/transferencias → PIP INTEGRACIÓN.
3. **El orden de ejecución sigue la secuencia de la auditoría §6**: identidad visible primero (UI, admin, emails, Swagger), luego backend (docstrings, config, celery, seeds, tests), luego datos (con backfill), luego integración, documentación e infraestructura (planes dedicados con ventanas de despliegue).

## Consecuencias

Positivas:

- Elimina la ambigüedad SISPOA/SIS-POA: la terminología del código pasa a coincidir con la de la arquitectura y los documentos PIP-GAMS.
- El rename por capa permite ejecutar cambios de bajo riesgo (identidad) antes que los de alto riesgo (BD, DNS, Keycloak) sin bloquearse mutuamente.
- La identidad visible queda alineada con el selector de sistemas y el namespace V2 ya existentes.

Negativas:

- Los valores de datos persistidos no se renombran (`PerfilImportacion.SISPOA_GASTOS_*`, `SolicitudReformulacion.sistema_origen='SISPOA'`): requieren coexistencia o backfill planificado, nunca rename en frío.
- Los renames de infraestructura (BD `gams_sis_poa`, servicios `sispoa-*`, realm Keycloak, bucket, DNS) tienen planes dedicados con ventanas; no se ejecutan como renames de código.
- Los documentos oficiales impresos (consolidación institucional, `workflow/consolidacion.py`) llevan fecha de corte: el histórico no se reescribe.
- El conteo de referencias (865 según el prompt maestro) no es reproducible con un criterio único: queda fijado el criterio de clasificación semántica como fuente de verdad.

## Alternativas consideradas

1. **Replace global `sispoa → pip`**: descartado por riesgo alto: renombraría SIS-POA (correcto) y los valores de datos persistidos, rompiendo histórico, tests e integraciones.
2. **Mantener "SISPOA" como nombre de plataforma**: descartado por la colisión semántica con el subsistema SIS-POA y por el objetivo oficial PIP-GAMS del plan maestro.
3. **Renombrar todo en una sola fase (big-bang)**: descartado: mezcla renames de código con migraciones de infraestructura de distinto riesgo y ventana.
