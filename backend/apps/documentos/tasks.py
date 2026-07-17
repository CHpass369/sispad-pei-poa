import hashlib
import io
import os
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calcular_hash_documento(self, documento_id):
    """Calcula el hash SHA-256 de un documento de forma asíncrona"""
    from apps.documentos.models import DocumentoAdjunto
    try:
        doc = DocumentoAdjunto.objects.get(id=documento_id)
        if doc.hash_sha256:
            return f"Documento {documento_id} ya tiene hash"

        if doc.archivo and default_storage.exists(doc.archivo.name):
            content = default_storage.open(doc.archivo.name).read()
            doc.hash_sha256 = hashlib.sha256(content).hexdigest()
            doc.tamanio_bytes = len(content)
            doc.save(update_fields=['hash_sha256', 'tamanio_bytes'])
            return f"Hash calculado para documento {documento_id}: {doc.hash_sha256[:16]}..."
        return f"Documento {documento_id} sin archivo"
    except DocumentoAdjunto.DoesNotExist:
        return f"Documento {documento_id} no encontrado"


def _es_imagen(nombre_archivo):
    extensiones_imagen = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    _, ext = os.path.splitext(nombre_archivo.lower())
    return ext in extensiones_imagen


def _es_pdf(nombre_archivo):
    _, ext = os.path.splitext(nombre_archivo.lower())
    return ext == '.pdf'


def _crear_thumbnail_imagen(archivo, max_size=(200, 200)):
    """Crea un thumbnail de una imagen usando Pillow."""
    from PIL import Image

    if hasattr(archivo, 'read'):
        content = archivo.read()
        archivo.seek(0)
        img = Image.open(io.BytesIO(content))
    else:
        img = Image.open(archivo)

    img.thumbnail(max_size, Image.LANCZOS)

    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
        img = background

    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    return output


def _extraer_texto_pdf(archivo, max_paginas=1):
    """Extrae texto de las primeras páginas de un PDF."""
    if hasattr(archivo, 'read'):
        content = archivo.read()
        if hasattr(archivo, 'seek'):
            archivo.seek(0)
    else:
        content = archivo.read() if hasattr(archivo, 'read') else open(archivo, 'rb').read()

    try:
        import fitz
        doc = fitz.open(stream=content, filetype='pdf')
        texto_paginas = []
        for i in range(min(max_paginas, len(doc))):
            page = doc[i]
            texto_paginas.append(page.get_text())
        doc.close()
        texto = '\n'.join(texto_paginas).strip()
        return texto[:2000] if texto else '(Sin texto extraíble)'
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        texto_paginas = []
        for i in range(min(max_paginas, len(reader.pages))):
            page = reader.pages[i]
            texto = page.extract_text()
            if texto:
                texto_paginas.append(texto)
        texto = '\n'.join(texto_paginas).strip()
        return texto[:2000] if texto else '(Sin texto extraíble)'
    except ImportError:
        pass

    return '(Extracción de texto no disponible — instalar PyPDF2 o PyMuPDF)'


def _obtener_icono_tipo_archivo(nombre_archivo):
    """Retorna el icono/tipo representativo para archivos que no son imagen ni PDF."""
    _, ext = os.path.splitext(nombre_archivo.lower())
    iconos = {
        '.doc': 'Documento Word',
        '.docx': 'Documento Word',
        '.xls': 'Hoja de calculo',
        '.xlsx': 'Hoja de calculo',
        '.ppt': 'Presentacion',
        '.pptx': 'Presentacion',
        '.txt': 'Texto plano',
        '.csv': 'Datos CSV',
        '.xml': 'XML',
        '.json': 'JSON',
        '.zip': 'Archivo comprimido',
        '.rar': 'Archivo comprimido',
        '.dwg': 'Plano CAD',
        '.dxf': 'Plano CAD',
    }
    return iconos.get(ext, f'Archivo ({ext or "desconocido"})')


@shared_task(bind=True)
def generar_vista_previa(self, documento_id):
    """Genera vista previa de documento: thumbnail para imagenes, texto para PDFs, icono para otros."""
    from apps.documentos.models import DocumentoAdjunto

    try:
        doc = DocumentoAdjunto.objects.get(id=documento_id)

        if not doc.archivo or not default_storage.exists(doc.archivo.name):
            return f"Documento {documento_id} sin archivo asociado"

        nombre = doc.archivo.name
        base_name, _ = os.path.splitext(os.path.basename(nombre))

        if _es_imagen(nombre):
            try:
                archivo = doc.archivo.open('rb')
                thumbnail_io = _crear_thumbnail_imagen(archivo)
                archivo.close()

                thumb_filename = f'previews/thumb_{documento_id}.jpg'
                thumb_content = thumbnail_io.read()
                default_storage.save(thumb_filename, ContentFile(thumb_content))
                logger.info(f"Thumbnail generado para documento {documento_id}: {thumb_filename}")
                return f"Thumbnail generado para documento {documento_id}: {thumb_filename}"
            except Exception as e:
                logger.warning(f"Error creando thumbnail para {documento_id}: {e}")
                return f"Error generando thumbnail: {e}"

        elif _es_pdf(nombre):
            try:
                archivo = doc.archivo.open('rb')
                texto = _extraer_texto_pdf(archivo)
                archivo.close()

                text_filename = f'previews/text_{documento_id}.txt'
                default_storage.save(text_filename, ContentFile(texto.encode('utf-8')))
                logger.info(f"Texto extraido para documento {documento_id}: {len(texto)} caracteres")
                return f"Texto extraido para documento {documento_id}: {len(texto)} caracteres"
            except Exception as e:
                logger.warning(f"Error extrayendo texto de PDF {documento_id}: {e}")
                return f"Error extrayendo texto: {e}"

        else:
            icono = _obtener_icono_tipo_archivo(nombre)
            text_filename = f'previews/icono_{documento_id}.txt'
            default_storage.save(text_filename, ContentFile(icono.encode('utf-8')))
            logger.info(f"Icono generado para documento {documento_id}: {icono}")
            return f"Icono generado para documento {documento_id}: {icono}"

    except DocumentoAdjunto.DoesNotExist:
        return f"Documento {documento_id} no encontrado"
