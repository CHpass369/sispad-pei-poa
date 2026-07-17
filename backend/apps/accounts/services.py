import re
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

Usuario = get_user_model()


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
