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
