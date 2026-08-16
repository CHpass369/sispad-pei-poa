---
name: pip-frontend
description: "Use when: frontend, Angular, Angular Material, componentes, features, servicios HTTP, ApiService, CapabilityGuard, capacidades, routing, lazy loading, formularios, estilos, tokens, Paginado, styles.scss, testing Karma, Jasmine, specs."
---

# PIP — Frontend (Angular 21 + Material)

Frontend en `frontend/sispoa`: Angular 21 + Angular Material, NgModules, 32 features lazy en `src/app/features`, core compartido en `src/app/core`.

## Arquitectura

- **ApiService** (src/app/core): base de API V1 `/api/v1` (legacy, Sunset 2027-01-01). Las rutas de features NO deben repetir el prefijo: PROHIBIDO el doble prefijo `/api/v1/api/v1/...`.
- **Servicios V2 tipados**: para API V2 (`/api/v2/{platform,core,catalogos,geo,integracion,auditoria,sis-pe,sis-poa,budget,sis-pro,me}/`) usar los servicios existentes por dominio, que ya tipan DTOs.
- **CapabilitiesService** (`/api/v2/me/capabilities/`) + **CapabilityGuard** con `data.capacidades` en las rutas para control de acceso por capacidad.
- **TokenInterceptor / ErrorInterceptor** en core: no reinventar manejo de auth/errores.
- Routing: features lazy (`loadChildren`) por dominio, con guardas de capacidad.

## Design system

- Tokens CSS `--pip-*` definidos en `styles.scss`: usarlos para colores, espaciado, tipografía. No colores hardcodeados salvo excepción justificada.
- Reutilizar componentes existentes (búsqueda previa: grep + codegraph) antes de crear.

## Reglas

- NO duplicar `Paginado<T>` (ya duplicado ~5 veces): usar las interfaces de paginación de los servicios V2 existentes.
- Formularios: template-driven por defecto; ReactiveForms solo donde ya es la convención (auth, planificacion).
- No `any` generalizado: tipar contra interfaces de servicios V2 existentes.
- No agrandar archivos grandes existentes sin necesidad (ej: budget.service.ts): extraer o reutilizar.
- SEARCH BEFORE CREATE: componente/servicio/interfaz nueva → buscar equivalente primero.

## Verificación

- Lint y type-check del proyecto.
- Tests: `cd frontend/sispoa; npm test -- --watch=false` (Karma + Jasmine). `make test-frontend` está roto: usar el comando npm directo.
- Escribir specs para features nuevas (describe/it de los componentes y servicios tocados).
