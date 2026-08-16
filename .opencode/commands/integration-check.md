---
description: Revisar contratos e integración frontend↔backend y entre dominios: mismatch de rutas, DTOs, esquemas, breaking changes y dependencias cross-domain. Uso: integration-check [dominio o par opcional].
agent: integration-reviewer
---

Revisa los contratos e integración indicados SIN MODIFICAR NINGÚN ARCHIVO. $ARGUMENTS

Pasos:

1. Acota el alcance: dominio (core, sis-pe, sis-poa, sis-pro), par frontend/backend (feature ↔ apps) o flujo (PAD→PEI→POA, proyecto↔actividad).
2. Traza y verifica los contratos (codegraph/grep, citando ruta:línea):
   - Frontend ↔ API: rutas, métodos, params, payloads y DTOs (ApiService /api/v1 legacy + servicios V2 tipados; sin doble prefijo).
   - API ↔ Application ↔ Domain ↔ Persistence: viewsets/serializers/services → modelos → migraciones.
   - Entre dominios: articulacion (SIS-PE↔SIS-POA), vinculoproyectoactividad → poau_actividad (SIS-POA↔SIS-PRO), dependencias de SIS-* sobre CORE sin inversión.
   - Convivencia V1/V2: namespaces correctos, rutas V2 no registradas en v1 y viceversa.
3. Busca breaking changes: consultas/queries a tablas renombradas (15-08-2026) en backend, frontend y scripts/; cambios de DTOs sin actualizar el consumidor.
4. Clasifica hallazgos: BLOCKER (contrato roto, dependencia indebida), HIGH, MEDIUM, LOW, INFO.

NO MODIFICAR. Salida: informe con hallazgos clasificados, contratos verificados y recomendaciones.
