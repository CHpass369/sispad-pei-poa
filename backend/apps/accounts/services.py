import re
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.accounts.models import AlcanceOrganizacional, Rol

Usuario = get_user_model()

SISTEMAS_ADMINISTRABLES = {'sis_pe', 'sis_poa'}
SISTEMAS_CAPACIDADES_ASIGNABLES = SISTEMAS_ADMINISTRABLES | {'accounts'}
SISTEMAS_POR_ROL = {
    'JEFE_PE': {'sis_pe'},
    'JEFE_POA': {'sis_poa'},
    'SUPER_ADMIN': SISTEMAS_ADMINISTRABLES,
}
# Roles derivados de la declaración de encargatura hecha en el registro
# público: el encargado aprueba los POAU de su unidad, el resto los valida.
ROL_ENCARGADO_UO = 'ENCARGADO_UO'
ROL_VALIDADOR_POAU = 'VALIDADOR_POAU'

CODIGOS_ROLES_BASE = {
    'SUPER_ADMIN',
    'SECRETARIO_MUNICIPAL',
    'DIRECTOR',
    'JEFE_POA',
    'JEFE_PE',
    'FORMULADOR_POAU',
    ROL_ENCARGADO_UO,
    ROL_VALIDADOR_POAU,
}
SCOPES_FIJOS_ROLES_SISTEMA = {
    'SUPER_ADMIN': AlcanceOrganizacional.SCOPE_GLOBAL,
    'JEFE_PE': AlcanceOrganizacional.SCOPE_GLOBAL,
    'JEFE_POA': AlcanceOrganizacional.SCOPE_GLOBAL,
    'SECRETARIO_MUNICIPAL': AlcanceOrganizacional.SCOPE_DESCENDANTS,
    'DIRECTOR': AlcanceOrganizacional.SCOPE_DESCENDANTS,
    'FORMULADOR_POAU': AlcanceOrganizacional.SCOPE_SELF,
    # Ambos ven y operan solo su propia UO: nunca las dependientes.
    ROL_ENCARGADO_UO: AlcanceOrganizacional.SCOPE_SELF,
    ROL_VALIDADOR_POAU: AlcanceOrganizacional.SCOPE_SELF,
}


def rol_sugerido_por_declaracion(solicita_encargado_unidad):
    """Rol POAU que corresponde a la declaración hecha en el registro.

    Es una sugerencia para la aprobación administrativa, no una concesión: el
    registro público es AllowAny y un administrador sigue confirmando el rol.
    """
    return (
        ROL_ENCARGADO_UO if solicita_encargado_unidad
        else ROL_VALIDADOR_POAU
    )


def unidades_organizacionales_disponibles_registro():
    """UO públicas que pueden solicitarse en un registro nuevo."""
    from apps.organizacion.models import UnidadOrganizacional

    hoy = timezone.localdate()
    return UnidadOrganizacional.objects.filter(
        activo=True,
        fecha_vigencia_desde__lte=hoy,
    ).filter(
        Q(fecha_vigencia_hasta__isnull=True)
        | Q(fecha_vigencia_hasta__gte=hoy)
    )


def crear_usuario(email, password, first_name='', last_name='', **extra_fields):
    usuario = Usuario.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        **extra_fields,
    )
    return usuario


def asignar_roles(usuario, codigos_roles):
    from apps.accounts.models import Rol
    roles = Rol.objects.filter(codigo__in=codigos_roles, activo=True)
    usuario.roles.set(roles)
    return usuario


def validar_contrasena(password):
    errors = []
    if len(password) < 8:
        errors.append('La contraseña debe tener al menos 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        errors.append('La contraseña debe contener al menos una mayúscula.')
    if not re.search(r'[a-z]', password):
        errors.append('La contraseña debe contener al menos una minúscula.')
    if not re.search(r'\d', password):
        errors.append('La contraseña debe contener al menos un número.')
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        errors.append('La contraseña debe contener al menos un carácter especial.')
    return {'valido': len(errors) == 0, 'errores': errors}


def registrar_intento_login(email, exitoso, ip_address=None):
    from apps.auditoria.models import EventoAuditoria
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        usuario = None
    accion = 'login' if exitoso else 'login_fallido'
    EventoAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad='Usuario',
        entidad_id=str(usuario.pk) if usuario else email,
        direccion_ip=ip_address,
        resumen=f'Intento de login {"exitoso" if exitoso else "fallido"} para {email}',
    )


@transaction.atomic
def bloquear_usuario(usuario, motivo='Demasiados intentos fallidos'):
    usuario.is_active = False
    usuario.save(update_fields=['is_active'])
    from apps.auditoria.models import EventoAuditoria
    EventoAuditoria.objects.create(
        usuario=usuario,
        accion='modificar',
        entidad='Usuario',
        entidad_id=str(usuario.pk),
        resumen=f'Usuario bloqueado: {motivo}',
    )


def obtener_usuario_por_email(email):
    try:
        return Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return None


def cambiar_contrasena(usuario, nueva_password):
    result = validar_contrasena(nueva_password)
    if not result['valido']:
        return result
    usuario.set_password(nueva_password)
    usuario.debe_cambiar_password = False
    usuario.save(update_fields=['password', 'debe_cambiar_password'])
    return {'valido': True, 'errores': []}


def obtener_usuarios_por_rol(codigo_rol, gestion=None):
    qs = Usuario.objects.filter(
        roles__codigo=codigo_rol, roles__activo=True, is_active=True
    ).distinct()
    return qs


def sistemas_de_rol(rol):
    """Sistemas de negocio efectivos de un rol activo."""
    if not rol or not rol.activo:
        return set()
    if rol.codigo in SISTEMAS_POR_ROL:
        return set(SISTEMAS_POR_ROL[rol.codigo])

    capacidades = getattr(rol, 'capacidades_activas', None)
    if capacidades is None:
        codigos = rol.capacidades.filter(activo=True).values_list(
            'codigo', flat=True,
        )
    else:
        codigos = [capacidad.codigo for capacidad in capacidades]
    return {
        sistema
        for sistema in SISTEMAS_ADMINISTRABLES
        if any(codigo.startswith(f'{sistema}.') for codigo in codigos)
    }


def sistema_efectivo_capacidad(capacidad_o_codigo):
    """Deriva el sistema desde el código; el campo legacy no es autoridad."""
    codigo = getattr(capacidad_o_codigo, 'codigo', capacidad_o_codigo)
    prefijo, separador, _ = str(codigo).partition('.')
    if not separador:
        return ''
    return prefijo.lower().replace('-', '_')


def sistemas_efectivos_de_rol(rol):
    """Namespaces efectivos de las capacidades activas de un rol."""
    capacidades = getattr(rol, 'capacidades_admin', None)
    if capacidades is None:
        capacidades = rol.capacidades.filter(activo=True)
    sistemas = {
        sistema_efectivo_capacidad(capacidad)
        for capacidad in capacidades
        if capacidad.activo
    }
    sistemas.discard('')
    sistemas.update(sistemas_de_rol(rol))
    return sistemas


def sistemas_administrables(usuario):
    """Límite explícito de SUPER_ADMIN y jefaturas PE/POA."""
    if usuario.is_superuser:
        return set(SISTEMAS_ADMINISTRABLES)
    codigos = set(
        usuario.roles.filter(activo=True).values_list('codigo', flat=True)
    )
    if 'SUPER_ADMIN' in codigos:
        return set(SISTEMAS_ADMINISTRABLES)
    sistemas = set()
    for codigo in codigos & SISTEMAS_POR_ROL.keys():
        sistemas.update(SISTEMAS_POR_ROL[codigo])
    # Conserva compatibilidad con roles administrativos personalizados: las
    # capacidades autorizan y solo las jefaturas conocidas limitan sistema.
    return sistemas or set(SISTEMAS_ADMINISTRABLES)


def puede_administrar_sistema(usuario, sistema):
    return sistema in sistemas_administrables(usuario)


def es_super_admin(usuario):
    """Reconoce superusuario Django o el rol base SUPER_ADMIN activo."""
    if usuario.is_superuser:
        return True
    return usuario.roles.filter(activo=True, codigo='SUPER_ADMIN').exists()


def sistemas_asignaciones_administrables(usuario):
    """Sistemas que el actor puede reemplazar en F3b2b.

    A diferencia del fallback histórico de ``sistemas_administrables``, este
    contrato es deliberadamente cerrado: solo SUPER_ADMIN y las dos jefaturas
    base administran asignaciones de usuarios.
    """
    if es_super_admin(usuario):
        return set(SISTEMAS_ADMINISTRABLES)
    codigos = set(
        usuario.roles.filter(activo=True).values_list('codigo', flat=True)
    )
    sistemas = set()
    for codigo in codigos & {'JEFE_PE', 'JEFE_POA'}:
        sistemas.update(SISTEMAS_POR_ROL[codigo])
    return sistemas


def puede_administrar_asignacion_rol(administrador, rol):
    """Indica si F3b2b puede reemplazar asignaciones del rol indicado."""
    sistemas = sistemas_efectivos_de_rol(rol)
    if not sistemas or not sistemas <= SISTEMAS_CAPACIDADES_ASIGNABLES:
        return False
    if es_super_admin(administrador):
        return True
    if not rol.activo or rol.deprecated:
        return False

    sistemas_negocio = sistemas & SISTEMAS_ADMINISTRABLES
    administrables = sistemas_asignaciones_administrables(administrador)
    if not sistemas_negocio or not sistemas_negocio <= administrables:
        return False

    capacidades_accounts = {
        capacidad.codigo
        for capacidad in (
            getattr(rol, 'capacidades_admin', None)
            or rol.capacidades.filter(activo=True)
        )
        if capacidad.activo and capacidad.codigo.startswith('accounts.')
    }
    capacidades_actor = set(
        administrador.roles.filter(
            activo=True,
            capacidades__activo=True,
            capacidades__codigo__startswith='accounts.',
        ).values_list('capacidades__codigo', flat=True)
    )
    return capacidades_accounts <= capacidades_actor


def roles_con_sistema(queryset, sistema):
    """Filtra roles por sistema efectivo, incluyendo los roles base."""
    codigos_especiales = [
        codigo
        for codigo, sistemas in SISTEMAS_POR_ROL.items()
        if sistema in sistemas
    ]
    return queryset.filter(
        Q(codigo__in=codigos_especiales)
        | Q(
            capacidades__activo=True,
            capacidades__codigo__startswith=f'{sistema}.',
        ),
    ).distinct()


def limitar_roles_administrables(queryset, administrador):
    """Oculta a las jefaturas los roles con capacidades del otro sistema."""
    sistemas = sistemas_administrables(administrador)
    if sistemas == SISTEMAS_ADMINISTRABLES:
        return queryset

    sistemas_prohibidos = SISTEMAS_ADMINISTRABLES - sistemas
    codigos_prohibidos = [
        codigo
        for codigo, sistemas_rol in SISTEMAS_POR_ROL.items()
        if sistemas_rol & sistemas_prohibidos
    ]
    restriccion = Q(codigo__in=codigos_prohibidos)
    for sistema in sistemas_prohibidos:
        restriccion |= Q(
            capacidades__activo=True,
            capacidades__codigo__startswith=f'{sistema}.',
        )
    return queryset.exclude(restriccion)


def _roles_objetivo_con_sistema(sistema):
    codigos_especiales = [
        codigo
        for codigo, sistemas in SISTEMAS_POR_ROL.items()
        if sistema in sistemas
    ]
    return Rol.objects.filter(
        Q(codigo__in=codigos_especiales)
        | Q(
            capacidades__activo=True,
            capacidades__codigo__startswith=f'{sistema}.',
        ),
        activo=True,
    )


def usuarios_con_sistema(queryset, sistema):
    """Filtra usuarios vinculados al sistema por roles o alcances activos."""
    roles_sistema = _roles_objetivo_con_sistema(sistema)
    roles_directos = Usuario.roles.through.objects.filter(
        usuario_id=OuterRef('pk'),
        rol_id__in=roles_sistema.values('pk'),
    )
    roles_alcance = AlcanceOrganizacional.objects.filter(
        usuario_id=OuterRef('pk'),
        activo=True,
        rol_id__in=roles_sistema.values('pk'),
    )
    alias = f'_tiene_{sistema}'
    return queryset.annotate(
        **{
            alias: Exists(roles_directos) | Exists(roles_alcance),
        },
    ).filter(**{alias: True})


def limitar_usuarios_administrables(queryset, administrador):
    """Aplica visibilidad por sistema y oculta SUPER_ADMIN a jefaturas."""
    sistemas = sistemas_administrables(administrador)
    if sistemas == SISTEMAS_ADMINISTRABLES:
        return queryset

    sistema = next(iter(sistemas))
    otro = next(iter(SISTEMAS_ADMINISTRABLES - sistemas))
    queryset = usuarios_con_sistema(queryset, sistema)

    roles_otro = _roles_objetivo_con_sistema(otro)
    directo_otro = Usuario.roles.through.objects.filter(
        usuario_id=OuterRef('pk'),
        rol_id__in=roles_otro.values('pk'),
    )
    alcance_otro = AlcanceOrganizacional.objects.filter(
        usuario_id=OuterRef('pk'),
        activo=True,
        rol_id__in=roles_otro.values('pk'),
    )
    return queryset.annotate(
        _tiene_otro_sistema=Exists(directo_otro) | Exists(alcance_otro),
    ).filter(_tiene_otro_sistema=False)


def limitar_objetivos_asignaciones(queryset, administrador):
    """Visibilidad F3b2b: pertenece al sistema propio, aunque también a otro."""
    if es_super_admin(administrador):
        return queryset

    sistemas = sistemas_asignaciones_administrables(administrador)
    if not sistemas:
        return queryset.none()

    condicion = Q()
    for sistema in sistemas:
        roles_sistema = _roles_objetivo_con_sistema(sistema)
        directo = Usuario.roles.through.objects.filter(
            usuario_id=OuterRef('pk'),
            rol_id__in=roles_sistema.values('pk'),
        )
        alcance = AlcanceOrganizacional.objects.filter(
            usuario_id=OuterRef('pk'),
            activo=True,
            rol_id__in=roles_sistema.values('pk'),
        )
        alias = f'_asignable_{sistema}'
        queryset = queryset.annotate(**{alias: Exists(directo) | Exists(alcance)})
        condicion |= Q(**{alias: True})

    super_admin_directo = Usuario.roles.through.objects.filter(
        usuario_id=OuterRef('pk'),
        rol__codigo='SUPER_ADMIN',
        rol__activo=True,
    )
    super_admin_alcance = AlcanceOrganizacional.objects.filter(
        usuario_id=OuterRef('pk'),
        activo=True,
        rol__codigo='SUPER_ADMIN',
        rol__activo=True,
    )
    return queryset.annotate(
        _objetivo_super_admin=(
            Exists(super_admin_directo) | Exists(super_admin_alcance)
        ),
    ).filter(
        condicion,
        is_superuser=False,
        _objetivo_super_admin=False,
    )
