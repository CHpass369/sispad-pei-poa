# ADR-002 — API V2 con namespaces por sistema

- **Estado:** Aprobado (WP-01)
- **Fecha:** 2026-08-09
- **Decisores:** Arquitectura PIP-GAMS

## Contexto

La API V1 monta apps en prefijo raíz con rutas inconsistentes (`planificacion`
incluso en dos prefijos). Para los nuevos sistemas se necesita un contrato
estable y agrupado por dominio, sin romper a los consumidores actuales.

## Decisión

**Crear `/api/v2/` manteniendo `/api/v1/` como compatibilidad temporal.**

```
/api/v2/platform/...   → núcleo transversal (IAM, organización, catálogos…)
/api/v2/sis-pe/...     → SIS-PE (instrumentos, versiones, nodos, vínculos…)
/api/v2/sis-poa/...    → SIS-POA (acciones, operaciones, presupuesto…)
/api/v2/sis-pro/...    → SIS-PRO (proyectos, cartera…)
/api/v2/me/...         → identidad/capacidades del usuario actual
```

Reglas por endpoint V2:

- serializers sin lógica compleja;
- servicios para comandos/escritura;
- selectors para lectura compleja;
- validadores de dominio explícitos;
- permisos backend por capacidad/alcance (ver ADR-003);
- OpenAPI obligatorio y contratos de respuesta estables;
- nombres de rutas kebab-case, recursos en plural.

## Consecuencias

- V1 queda congelada funcionalmente (solo fixes críticos).
- Cada SIS evoluciona su namespace V2 de forma independiente.
- El frontend V2 consume únicamente `/api/v2/`.
- El retiro de V1 requiere los gates del plan (estabilidad, reconciliación,
  periodo de observación).

## Alternativas descartadas

- Reorganizar V1 in-place: rompe contratos existentes sin beneficio.
- `api/v2` plano sin namespaces: pierde la agrupación por sistema que
  requiere el menú/capacidades.
