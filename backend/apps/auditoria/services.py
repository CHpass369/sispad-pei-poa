from django.db.models import Q

from .models import EventoAuditoria
from apps.gestion.models import GestionFiscal


def _resolver_gestion(valor):
    """Normaliza una gestión a instancia de GestionFiscal (PIP-DB-008).

    Acepta instancia (FK), UUID o año entero. Si el año no existe en la
    canónica, devuelve None (el evento queda sin gestión): NO se inventan
    gestiones (invariante de gobernanza).
    """
    if valor is None or isinstance(valor, GestionFiscal):
        return valor
    if isinstance(valor, int):
        return GestionFiscal.objects.filter(anio=valor).first()
    try:
        return GestionFiscal.objects.filter(pk=valor).first()
    except (ValueError, TypeError):
        return None


def _aplicar_filtro_gestion(qs, gestion):
    if gestion is None:
        return qs
    if isinstance(gestion, int):
        return qs.filter(gestion__anio=gestion)
    return qs.filter(gestion=gestion)


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
        gestion=_resolver_gestion(kwargs.get('gestion')),
    )
    return evento


def obtener_historial(entidad, entidad_id, limit=50):
    return EventoAuditoria.objects.filter(
        entidad=entidad, entidad_id=str(entidad_id)
    ).select_related('usuario').order_by('-creado_en')[:limit]


def buscar_por_usuario(usuario_id, gestion=None, accion=None, limit=100):
    qs = EventoAuditoria.objects.filter(usuario_id=usuario_id)
    qs = _aplicar_filtro_gestion(qs, gestion)
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
    qs = _aplicar_filtro_gestion(qs, gestion)
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
            'gestion': evento.gestion.anio if evento.gestion else None,
        })
    return registros


def contar_por_entidad(entidad, gestion=None):
    qs = EventoAuditoria.objects.filter(entidad=entidad)
    qs = _aplicar_filtro_gestion(qs, gestion)
    return qs.count()