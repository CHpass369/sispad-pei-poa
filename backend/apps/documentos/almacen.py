"""Guardar y recuperar documentos cifrados.

El identificador del registro dueño viaja como contexto autenticado: un
documento no se puede reasignar de un acta a otra sin que el descifrado falle.
"""
from .cifrado import cifrar, descifrar, huella
from .models import DocumentoAdjunto


def _contexto(entidad, entidad_id):
    return f'{entidad}:{entidad_id}'.encode('utf-8')


def guardar(contenido, *, entidad, entidad_id, nombre, gestion, usuario=None,
            tipo_documento='', content_type='application/pdf',
            descripcion=''):
    """Cifra el documento y lo deja en la base. Devuelve el registro."""
    nonce, cifrado = cifrar(contenido, _contexto(entidad, entidad_id))
    return DocumentoAdjunto.objects.create(
        entidad=entidad, entidad_id=str(entidad_id), nombre=nombre,
        descripcion=descripcion, tipo_documento=tipo_documento,
        contenido_cifrado=cifrado, nonce=nonce, content_type=content_type,
        hash_sha256=huella(contenido), tamanio_bytes=len(contenido),
        subido_por=usuario, gestion=gestion,
    )


def leer(documento):
    """Devuelve el documento en claro. Falla si fue alterado."""
    if not documento.contenido_cifrado:
        raise FileNotFoundError('El documento no tiene contenido cifrado.')
    return descifrar(documento.nonce, documento.contenido_cifrado,
                     _contexto(documento.entidad, documento.entidad_id))
