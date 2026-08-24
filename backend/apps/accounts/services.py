import re
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.accounts.models import AlcanceOrganizacional, Rol

Usuario = get_user_model()

SISTEMAS_ADMINISTRABLES = {'sis_pe', 'sis_poa'}
SISTEMAS_POR_ROL = {
    'JEFE_PE': {'sis_pe'},
    'JEFE_POA': {'sis_poa'},
    'SUPER_ADMIN': SISTEMAS_ADMINISTRABLES,
}


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
