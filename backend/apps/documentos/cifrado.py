"""Cifrado de los documentos que guarda la plataforma.

Se usa AES-256-GCM, que además de cifrar **autentica**: si alguien altera un
byte del documento en la base, el descifrado falla en vez de devolver basura
silenciosamente. Eso importa en un acta firmada.

La clave vive fuera de la base y fuera del repositorio, en la variable de
entorno `DOCUMENTOS_CLAVE` (32 bytes en base64). Si la clave estuviera al lado
del dato, cifrar no protegería de nada: quien se lleva la base se lleva las dos
cosas.
"""
import base64
import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LARGO_NONCE = 12  # 96 bits, lo recomendado para GCM.
LARGO_CLAVE = 32  # AES-256.


class DocumentoAlterado(Exception):
    """El documento no se pudo descifrar: clave equivocada o bytes tocados."""


def clave():
    """La clave de cifrado, validada.

    Se lee solo de `settings`, que ya la toma del entorno. Consultar además
    `os.environ` acá dejaría a la configuración sin la última palabra: la
    variable de entorno ganaría por encima de cualquier override.
    """
    crudo = getattr(settings, 'DOCUMENTOS_CLAVE', '')
    if not crudo:
        raise ImproperlyConfigured(
            'Falta DOCUMENTOS_CLAVE en la configuración. Genérela con: '
            'python -c "import base64,os; '
            'print(base64.b64encode(os.urandom(32)).decode())" '
            'y agréguela al archivo .env.'
        )
    try:
        material = base64.b64decode(crudo, validate=True)
    except Exception as error:
        raise ImproperlyConfigured(
            'DOCUMENTOS_CLAVE debe ser base64 de 32 bytes.') from error
    if len(material) != LARGO_CLAVE:
        raise ImproperlyConfigured(
            f'DOCUMENTOS_CLAVE debe tener {LARGO_CLAVE} bytes, tiene '
            f'{len(material)}.')
    return material


def huella(contenido):
    """SHA-256 del documento en claro: sirve para verificar e identificar."""
    return hashlib.sha256(contenido).hexdigest()


def cifrar(contenido, contexto=b''):
    """Devuelve (nonce, cifrado). `contexto` queda autenticado, no cifrado.

    En `contexto` va el identificador del registro dueño del documento: así un
    documento no se puede mover de un acta a otra sin que el descifrado falle.
    """
    nonce = os.urandom(LARGO_NONCE)
    return nonce, AESGCM(clave()).encrypt(nonce, contenido, contexto)


def descifrar(nonce, cifrado, contexto=b''):
    """Devuelve el documento en claro, o falla si fue alterado."""
    try:
        return AESGCM(clave()).decrypt(bytes(nonce), bytes(cifrado), contexto)
    except InvalidTag as error:
        raise DocumentoAlterado(
            'El documento no se pudo descifrar: la clave no corresponde o el '
            'contenido fue alterado.') from error
