import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, soft_time_limit=300, time_limit=600)
def generar_reporte_presupuestario_async(self, params: dict):
    """Genera un reporte presupuestario de forma asíncrona"""
    from apps.reportes.services import (
        generar_poa_consolidado_xlsx,
        generar_poa_unidad_xlsx,
    )
    try:
        gestion = params.get('gestion')
        tipo = params.get('tipo', 'consolidado')

        if tipo == 'consolidado':
            output, filename = generar_poa_consolidado_xlsx(gestion)
        elif tipo == 'unidad':
            unidad_id = params.get('unidad_id')
            output, filename = generar_poa_unidad_xlsx(gestion, unidad_id)
        else:
            return {"status": "error", "error": f"Tipo de reporte no soportado: {tipo}"}

        logger.info(f"Reporte {tipo} generado: {filename}")
        return {
            "status": "ok",
            "filename": filename,
            "gestion": gestion,
            "tipo": tipo,
            "tamanio_bytes": output.tell(),
        }
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def exportar_poa_completo_async(self, gestion: int):
    """Exporta el POA completo de una gestión como ZIP"""
    logger.info(f"Exportando POA completo gestión {gestion}")
    # TODO: Implementar exportación completa con zipfile
    return {"status": "ok", "gestion": gestion, "mensaje": "Exportación no implementada aún"}
