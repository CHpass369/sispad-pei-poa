import re

from django.utils import timezone


def validar_email_institucional(email):
    if not email:
        return {'valido': False, 'mensaje': 'El email es requerido.'}
    patron = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return {'valido': False, 'mensaje': 'El formato del email no es valido.'}
    return {'valido': True, 'mensaje': 'Email valido.'}


def validar_contrasena_forte(password):
    errores = []
    if len(password) < 8:
        errores.append('Minimo 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        errores.append('Al menos una mayuscula.')
    if not re.search(r'[a-z]', password):
        errores.append('Al menos una minuscula.')
    if not re.search(r'\d', password):
        errores.append('Al menos un numero.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errores.append('Al menos un caracter especial.')
    return {'valido': len(errores) == 0, 'errores': errores}


def validar_usuario_activo(usuario):
    if usuario is None:
        return {'valido': False, 'mensaje': 'Usuario no encontrado.'}
    if not usuario.is_active:
        return {'valido': False, 'mensaje': 'La cuenta del usuario esta desactivada.'}
    if usuario.debe_cambiar_password:
        return {'valido': True, 'mensaje': 'Usuario activo pero debe cambiar contrasena.', 'advertencia': True}
    return {'valido': True, 'mensaje': 'Usuario activo.'}
