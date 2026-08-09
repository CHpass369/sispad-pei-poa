# ADR-003 — IAM: identidad externa + autorización por capacidades

- **Estado:** Aprobado (WP-01)
- **Fecha:** 2026-08-09
- **Decisores:** Arquitectura PIP-GAMS

## Contexto

Hoy la autorización depende de roles hard-codeados en el frontend
(`superadmin`, `tecnico_admin`, `planificador`) y de un `IsAuthenticated`
global heterogéneo. Se necesitan permisos por módulo/sistema y menú derivado
de capacidades (principios §3.11 y §3.12 del plan maestro).

## Decisión

**Separación de responsabilidades:**

1. **Identidad y autenticación:** OIDC/Keycloak (fase 12), con usuario local
   vinculado.
2. **Autorización de negocio:** base PIP-GAMS con:

- `Usuario` local (vinculado a identidad OIDC);
- `Rol`;
- `Permiso`/`Capacidad` — código `<sistema>.<dominio>.<accion>`
  (p. ej. `sis_pe.pad.edit`, `sis_poa.budget.manage`, `platform.audit.read`);
- `RolPermiso`;
- `AsignacionUsuarioRol`;
- `AlcanceOrganizacional`, `AlcanceTerritorial`, `AlcanceTemporal`;
- `Delegacion`/`Suplencia`.

**Contrato para el frontend:** `GET /api/v2/me/capabilities` devuelve las
capacidades y alcances del usuario; el menú y las acciones se construyen con
esas capacidades. Los roles no se codifican en componentes.

**Contrato para el backend:** cada endpoint declara las capacidades
requeridas; la política de autorización es uniforme (mixin/permiso base del
núcleo). Todo endpoint `AllowAny` queda inventariado y justificado.

## Consecuencias

- Los permisos dejan de ser responsabilidad del frontend.
- La auditoría registra capacidad/alcance usados en cada decisión.
- La migración de permisos V1 (rol → capacidades) se define en WP-03 con
  tabla de homologación rol→capacidades.

## Alternativas descartadas

- Autorización íntegra en Keycloak: los alcances organizacionales/territoriales
  son de negocio municipal y cambian más rápido que la identidad.
- Roles codificados en UI: prohibido por principio (§3.12).
