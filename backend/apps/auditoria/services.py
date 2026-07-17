from django.db.models import Q

from .models import EventoAuditoria


def registrar_evento(usuario, accion, entidad, entidad_id, **kwargs):
    evento = EventoAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id),
        version=kwargs.get('version'),
        resumen=kwargs.get('resumen', ''),
        datos_previos=kwargs.get('datos_previos'),
        datos_posteriores=kwargs.get('datos_posteriores'),
        direccion_ip=kwargs.get('direccion_ip'),
        gestion=kwargs.get('gestion'),
    )
    return evento


def obtener_historial(entidad, entidad_id, limit=50):
    return EventoAuditoria.objects.filter(
        entidad=entidad, entidad_id=str(entidad_id)
    ).select_related('usuario').order_by('-creado_en')[:limit]


def buscar_por_usuario(usuario_id, gestion=None, accion=None, limit=100):
    qs = EventoAuditoria.objects.filter(usuario_id=usuario_id)
    if gestion:
        qs = qs.filter(gestion=gestion)
    if accion:
        qs = qs.filter(accion=accion)
    return qs.select_related('usuario').order_by('-creado_en')[:limit]


def buscar_por_fecha(fecha_inicio, fecha_fin, entidad=None, accion=None):
    qs = EventoAuditoria.objects.filter(
        creado_en__date__gte=fecha_inicio,
        creado_en__date__lte=fecha_fin,
    )
    if entidad:
        qs = qs.filter(entidad=entidad)
    if accion:
        qs = qs.filter(accion=accion)
    return qs.select_related('usuario').order_by('-creado_en')


def exportar_auditoria(gestion=None, fecha_inicio=None, fecha_fin=None):
    qs = EventoAuditoria.objects.all()
    if gestion:
        qs = qs.filter(gestion=gestion)
    if fecha_inicio:
        qs = qs.filter(creado_en__date__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(creado_en__date__lte=fecha_fin)
    qs = qs.select_related('usuario').order_by('-creado_en')
    registros = []
    for evento in qs:
        registros.append({
            'fecha': str(evento.creado_en),
            'usuario': str(evento.usuario) if evento.usuario else 'Sistema',
            'accion': evento.get_accion_display(),
            'entidad': evento.entidad,
            'entidad_id': evento.entidad_id,
            'resumen': evento.resumen,
            'direccion_ip': str(evento.direccion_ip) if evento.direccion_ip else '',
            'gestion': evento.gestion,
        })
    return registros


def contar_por_entidad(entidad, gestion=None):
    qs = EventoAuditoria.objects.filter(entidad=entidad)
    if gestion:
        qs = qs.filter(gestion=gestion)
    return qs.count()
