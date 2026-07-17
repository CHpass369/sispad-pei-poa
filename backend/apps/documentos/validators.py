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


def validar_tipo_mime(archivo):
    if hasattr(archivo, 'content_type'):
        mime = archivo.content_type
    else:
        mime = 'application/octet-stream'
    if mime not in ALLOWED_MIME_TYPES:
        return {
            'valido': False,
            'mensaje': (
                'Tipo MIME no permitido: ' + mime
                + '. Tipos aceptados: ' + ', '.join(ALLOWED_MIME_TYPES)
            ),
        }
    return {'valido': True, 'mensaje': 'Tipo MIME valido.'}


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
            'mensaje': (
                'El archivo (' + str(size_mb) + ' MB) excede el limite de '
                + str(max_mb) + ' MB.'
            ),
        }
    return {'valido': True, 'mensaje': 'Tamanio valido.'}


def validar_nombre_archivo(nombre):
    if not nombre or not nombre.strip():
        return {'valido': False, 'mensaje': 'El nombre del archivo es requerido.'}
    caracteres_prohibidos = '<>:"/\\|?*'
    for char in nombre:
        if char in caracteres_prohibidos:
            return {
                'valido': False,
                'mensaje': 'El nombre contiene caracteres no permitidos: "' + char + '".',
            }
    if len(nombre) > 255:
        return {'valido': False, 'mensaje': 'El nombre del archivo excede 255 caracteres.'}
    return {'valido': True, 'mensaje': 'Nombre de archivo valido.'}
