"""Tareas asíncronas del dominio de preinversión SIS-PRO."""
from celery import shared_task

from .documentos_preinversion import generar_documento
from .models_preinversion import DocumentoGenerado
from .models_v2 import Proyecto


@shared_task(bind=True)
def generar_documento_preinversion(self, proyecto_id, tipo_documento, usuario_id=None):
    """Genera DOCX/PDF del expediente (ITCP o EDTP) de forma asíncrona."""
    proyecto = Proyecto.objects.get(id=proyecto_id)
    generado = DocumentoGenerado.objects.create(
        proyecto=proyecto, tipo_documento=tipo_documento, created_by_id=usuario_id,
    )
    resultado = generar_documento(proyecto, tipo_documento, generado)
    return {
        'documento_generado_id': str(resultado.id),
        'estado': resultado.estado,
    }
