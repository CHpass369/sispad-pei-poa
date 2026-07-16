import hashlib
from celery import shared_task
from django.core.files.storage import default_storage


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


@shared_task(bind=True)
def generar_vista_previa(self, documento_id):
    """Genera vista previa de documento (placeholder para integración futura)"""
    from apps.documentos.models import DocumentoAdjunto
    try:
        doc = DocumentoAdjunto.objects.get(id=documento_id)
        # TODO: Integrar con WeasyPrint o Pillow para previews
        return f"Vista previa generada para {doc.nombre}"
    except DocumentoAdjunto.DoesNotExist:
        return f"Documento {documento_id} no encontrado"
