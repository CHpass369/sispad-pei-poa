import hashlib
from django.db import transaction

from .models import DocumentoAdjunto

ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'application/zip',
]

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


@transaction.atomic
def subir_documento(archivo, nombre, entidad, entidad_id, gestion, **kwargs):
    doc = DocumentoAdjunto(
        archivo=archivo,
        nombre=nombre,
        entidad=entidad,
        entidad_id=str(entidad_id),
        gestion=gestion,
        descripcion=kwargs.get('descripcion', ''),
        tipo_documento=kwargs.get('tipo_documento', ''),
        subido_por=kwargs.get('subido_por'),
    )
    doc.save()
    return doc


def validar_tipo_archivo(archivo):
    if hasattr(archivo, 'content_type'):
        mime = archivo.content_type
    else:
        mime = 'application/octet-stream'
    if mime not in ALLOWED_MIME_TYPES:
        return {
            'valido': False,
            'mensaje': 'Tipo de archivo no permitido: ' + mime + '. Tipos aceptados: ' + ', '.join(ALLOWED_MIME_TYPES),
        }
    return {'valido': True, 'mensaje': 'Tipo de archivo valido.'}


def validar_tamanio_archivo(archivo):
    if hasattr(archivo, 'size'):
        size = archivo.size
    elif hasattr(archivo, 'read'):
        content = archivo.read()
        size = len(content)
        archivo.seek(0)
    else:
        return {'valido': True, 'mensaje': 'No se pudo determinar el tamanio.'}
    if size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        size_mb = size // (1024 * 1024)
        return {
            'valido': False,
            'mensaje': 'El archivo (' + str(size_mb) + ' MB) excede el limite de ' + str(max_mb) + ' MB.',
        }
    return {'valido': True, 'mensaje': 'Tamanio valido.'}


def generar_vista_previa_real(documento_id):
    try:
        doc = DocumentoAdjunto.objects.get(id=documento_id)
    except DocumentoAdjunto.DoesNotExist:
        return None
    if not doc.archivo:
        return None
    return {
        'id': str(doc.id),
        'nombre': doc.nombre,
        'tipo_documento': doc.tipo_documento,
        'hash_sha256': doc.hash_sha256,
        'tamanio_bytes': doc.tamanio_bytes,
        'url': doc.archivo.url if doc.archivo else None,
    }


@transaction.atomic
def eliminar_documento(documento_id, usuario=None):
    try:
        doc = DocumentoAdjunto.objects.get(id=documento_id)
    except DocumentoAdjunto.DoesNotExist:
        return {'exito': False, 'mensaje': 'Documento no encontrado.'}
    doc.activo = False
    doc.save(update_fields=['activo', 'updated_at'])
    return {'exito': True, 'mensaje': 'Documento eliminado (desactivado).'}


def obtener_documentos_por_entidad(entidad, entidad_id, gestion=None):
    qs = DocumentoAdjunto.objects.filter(
        entidad=entidad, entidad_id=str(entidad_id), activo=True
    )
    if gestion:
        qs = qs.filter(gestion=gestion)
    return qs.select_related('subido_por').order_by('-created_at')
