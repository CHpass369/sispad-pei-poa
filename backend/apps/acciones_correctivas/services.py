from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q

from .models import AccionCorrectiva, CompromisoAccionCorrectiva


def crear_accion_correctiva(
    alerta_id, description, cause, responsible_id, due_date,
    start_date=None, expected_result='', responsible_unit_id=None,
    entry_id=None, gestion=None,
):
    now = timezone.now()
    if gestion is None:
        gestion = now.year
    if start_date is None:
        start_date = now.date()

    accion = AccionCorrectiva.objects.create(
        alerta_id=alerta_id,
        entry_id=entry_id,
        description=description,
        cause=cause,
        responsible_id=responsible_id,
        responsible_unit_id=responsible_unit_id,
        start_date=start_date,
        due_date=due_date,
        expected_result=expected_result,
        status=AccionCorrectiva.Estado.PENDIENTE,
        gestion=gestion,
    )
    return accion


def verificar_cumplimiento(accion_id):
    accion = AccionCorrectiva.objects.get(id=accion_id)
    compromisos = accion.compromisos.all()

    if not compromisos.exists():
        return {
            'accion_id': str(accion.id),
            'total_compromisos': 0,
            'cumplidos': 0,
            'pendientes': 0,
            'incumplidos': 0,
            'todos_cumplidos': False,
        }

    total = compromisos.count()
    cumplidos = compromisos.filter(status='cumplido').count()
    pendientes = compromisos.filter(status='pendiente').count()
    incumplidos = compromisos.filter(status='incumplido').count()

    todos_cumplidos = total > 0 and cumplidos == total

    return {
        'accion_id': str(accion.id),
        'total_compromisos': total,
        'cumplidos': cumplidos,
        'pendientes': pendientes,
        'incumplidos': incumplidos,
        'todos_cumplidos': todos_cumplidos,
    }


def verificar_vencimiento():
    hoy = timezone.now().date()
    acciones_vencidas = AccionCorrectiva.objects.filter(
        status__in=[
            AccionCorrectiva.Estado.PENDIENTE,
            AccionCorrectiva.Estado.EN_EJECUCION,
        ],
        due_date__lt=hoy,
    ).select_related('responsible', 'responsible_unit')

    resultados = []
    for accion in acciones_vencidas:
        dias_vencida = (hoy - accion.due_date).days
        resultados.append({
            'accion_id': str(accion.id),
            'description': accion.description,
            'responsible_email': accion.responsible.email,
            'due_date': accion.due_date,
            'dias_vencida': dias_vencida,
            'status': accion.status,
            'gestion': accion.gestion,
        })

    return resultados


def obtener_acciones_por_cumplir(dias=7):
    hoy = timezone.now().date()
    fecha_limite = hoy + timedelta(days=dias)

    acciones = AccionCorrectiva.objects.filter(
        status__in=[
            AccionCorrectiva.Estado.PENDIENTE,
            AccionCorrectiva.Estado.EN_EJECUCION,
        ],
        due_date__gte=hoy,
        due_date__lte=fecha_limite,
    ).select_related('responsible', 'responsible_unit')

    resultados = []
    for accion in acciones:
        dias_restantes = (accion.due_date - hoy).days
        total_compromisos = accion.compromisos.count()
        cumplidos = accion.compromisos.filter(status='cumplido').count()

        resultados.append({
            'accion_id': str(accion.id),
            'description': accion.description,
            'responsible_email': accion.responsible.email,
            'due_date': accion.due_date,
            'dias_restantes': dias_restantes,
            'status': accion.status,
            'total_compromisos': total_compromisos,
            'compromisos_cumplidos': cumplidos,
            'gestion': accion.gestion,
        })

    return resultados


def actualizar_estado_automatico():
    acciones_actualizadas = []

    acciones = AccionCorrectiva.objects.filter(
        status__in=[
            AccionCorrectiva.Estado.PENDIENTE,
            AccionCorrectiva.Estado.EN_EJECUCION,
        ],
    ).prefetch_related('compromisos')

    for accion in acciones:
        compromisos = accion.compromisos.all()
        if not compromisos.exists():
            continue

        total = compromisos.count()
        cumplidos = compromisos.filter(status='cumplido').count()
        incumplidos = compromisos.filter(status='incumplido').count()

        nuevo_estado = None

        if cumplidos == total:
            nuevo_estado = AccionCorrectiva.Estado.CUMPLIDA
        elif incumplidos == total:
            nuevo_estado = AccionCorrectiva.Estado.INCUMPLIDA
        elif accion.status == AccionCorrectiva.Estado.PENDIENTE and cumplidos > 0:
            nuevo_estado = AccionCorrectiva.Estado.EN_EJECUCION

        if nuevo_estado and nuevo_estado != accion.status:
            accion.status = nuevo_estado
            accion.save(update_fields=['status', 'updated_at'])
            acciones_actualizadas.append({
                'accion_id': str(accion.id),
                'estado_anterior': accion.status,
                'estado_nuevo': nuevo_estado,
            })

    return acciones_actualizadas
