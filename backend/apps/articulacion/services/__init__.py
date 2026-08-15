from apps.auditoria.models import EventoAuditoria


def registrar_auditoria(usuario, accion, entidad, entidad_id, detalle=None):
    """Registra evento en EventoAuditoria (apps.auditoria)."""
    EventoAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id),
        resumen=detalle or '',
    )


from .materializacion_matriz import (  # noqa: E402
    construir_matriz_a,
    construir_matriz_a_gestion,
    construir_matriz_b,
    construir_matriz_b_gestion,
    materializar_borrador_matriz,
)
