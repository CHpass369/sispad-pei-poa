from rest_framework import permissions

from apps.accounts.permissions import tiene_capacidad


# Roles que formulan instrumentos: son los que pueden escribir en articulación.
#
# `planificador` y `tecnico_admin` se conservan por compatibilidad, pero NO
# existen en el catálogo de Rol: mientras fueron los únicos acompañando a
# `superadmin`, toda la superficie de escritura de articulación quedaba
# reservada de hecho a los superusuarios. Los cuatro perfiles POA/PE son los
# que el sidebar ya usaba para mostrar las herramientas.
#
# ATENCIÓN: esta lista está en minúsculas y solo `jefe_poa`, `tecnico_poa`,
# `jefe_pe` y `tecnico_pe` existen realmente (los siembra accounts.0007). El
# catálogo vigente de roles es el de `seed_roles_permisos` y está en MAYÚSCULAS
# —`JEFE_POA`, `DIRECTOR`, `FORMULADOR_POAU`, `ENCARGADO_UO`,
# `VALIDADOR_POAU`—, así que ninguno de esos perfiles pasa por acá. Por eso la
# lista dejó de ser la única puerta: la autoridad real es la capacidad.
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
    """Lectura para cualquier autenticado; escritura para quien formula.

    «Quien formula» se resuelve por dos vías, y basta con una:

    1. **Capacidad declarada por el viewset** (`capacidad_escritura`), que es la
       autoridad de permisos del proyecto (ADR-003). Es la vía preferente: el
       endpoint dice qué capacidad gobierna su instrumento y el catálogo de
       roles decide quién la tiene, sin que este módulo conozca códigos de rol.
    2. **`ROLES_FORMULADORES`**, la lista histórica, que se conserva para no
       revocarle la escritura a nadie que hoy la tenga por esa vía.

    Un viewset sin `capacidad_escritura` se comporta igual que antes: solo la
    lista. Así el cambio no ensancha la superficie de escritura de PAD/PEI.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.user.roles.filter(codigo__in=ROLES_FORMULADORES).exists():
            return True
        capacidad = getattr(view, 'capacidad_escritura', None)
        return bool(capacidad) and tiene_capacidad(request.user, capacidad)


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
