import { AdminAssignmentScope } from './admin-usuarios.service';

export const BASE_ROLE_SCOPES: Readonly<Record<string, AdminAssignmentScope>> = {
  SUPER_ADMIN: 'GLOBAL',
  JEFE_PE: 'GLOBAL',
  JEFE_POA: 'GLOBAL',
  SECRETARIO_MUNICIPAL: 'DESCENDANTS',
  DIRECTOR: 'DESCENDANTS',
  FORMULADOR_POAU: 'SELF',
  VALIDADOR_POAU: 'SELF',
  ENCARGADO_UO: 'SELF',
};

export function fixedScopeForRole(roleCode: string): AdminAssignmentScope | null {
  return BASE_ROLE_SCOPES[roleCode] ?? null;
}
