from rest_framework import permissions


class ArticulacionPermisos(permissions.BasePermission):
    """Permisos por acción: solo superadmin, planificador y técnico admin pueden modificar."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.roles.filter(
                codigo__in=['superadmin', 'planificador', 'tecnico_admin']
            ).exists()
        )


# ---------------------------------------------------------------------------
# Circuito de revisión de las Matrices PAD
# ---------------------------------------------------------------------------

# Roles que ejercen la jefatura o administración de SIS-PE: aprueban y observan.
# Ajustar aquí si la entidad define un rol propio para esa función.
ROLES_APROBADORES = ('superadmin', 'revisor_planificacion', 'mae')


def es_aprobador(usuario):
    """La jefatura/administración de SIS-PE: aprueba u observa registros."""
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    return usuario.roles.filter(codigo__in=ROLES_APROBADORES).exists()


def es_autor(borrador, usuario):
    """El técnico que creó el registro."""
    if not usuario or not usuario.is_authenticated:
        return False
    return borrador.created_by_id == usuario.id


def permisos_revision_matriz(borrador, usuario):
    """Acciones disponibles para este usuario sobre este registro.

    Reglas:
      - Un registro APROBADO es inmutable: no se edita ni se borra.
      - Valida el técnico autor del registro (o un aprobador).
      - Aprueba y observa solo la jefatura/administración de SIS-PE.
      - Borran el técnico que lo creó y la jefatura, mientras no esté aprobado.
    """
    aprobado = borrador.estado_revision == borrador.REVISION_APROBADO
    autor = es_autor(borrador, usuario)
    aprobador = es_aprobador(usuario)
    validado = borrador.estado_revision == borrador.REVISION_VALIDADO

    return {
        'es_autor': autor,
        'es_aprobador': aprobador,
        'editar': not aprobado and (autor or aprobador),
        'validar': not aprobado and not validado and (autor or aprobador),
        'aprobar': aprobador and validado,
        'observar': aprobador and not aprobado,
        'borrar': (autor or aprobador) and not aprobado,
    }
