from rest_framework import permissions


# Roles que formulan instrumentos: son los que pueden escribir en articulación.
#
# `planificador` y `tecnico_admin` se conservan por compatibilidad, pero NO
# existen en el catálogo de Rol: mientras fueron los únicos acompañando a
# `superadmin`, toda la superficie de escritura de articulación quedaba
# reservada de hecho a los superusuarios. Los cuatro perfiles POA/PE son los
# que el sidebar ya usaba para mostrar las herramientas.
ROLES_FORMULADORES = (
    'superadmin',
    'planificador',
    'tecnico_admin',
    'admin_poa',
    'jefe_poa',
    'tecnico_poa',
    'jefe_pe',
    'tecnico_pe',
)


class ArticulacionPermisos(permissions.BasePermission):
    """Lectura para cualquier autenticado; escritura para quien formula."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.roles.filter(codigo__in=ROLES_FORMULADORES).exists()
        )


# ---------------------------------------------------------------------------
# Circuito de revisión de las Matrices PAD
# ---------------------------------------------------------------------------

# Roles que ejercen la jefatura o administración de SIS-PE: aprueban y observan.
# Ajustar aquí si la entidad define un rol propio para esa función.
ROLES_APROBADORES = (
    'superadmin', 'revisor_planificacion', 'mae', 'jefe_poa', 'jefe_pe',
)


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
