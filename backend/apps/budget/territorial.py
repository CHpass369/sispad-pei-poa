"""Servicios de distribución territorial del ciclo presupuestario SIS-POA
(Fase 6): reparto de una bolsa entre distritos con ajuste de redondeo exacto.

Flujo (patrón de dominio, como `importer.py`):

    1. `calcular_reparto`   — calcula `monto_calculado` por distrito según el
                              método y aplica el AJUSTE DE REDONDEO; escribe
                              `monto_final` y pasa la distribución a CALCULADA.
                              NO crea reservas.
    2. `aplicar_reparto`    — en UNA transacción materializa el reparto como
                              reservas DISTRITALES (una por distrito) sobre la
                              fuente; valida disponibilidad por fuente
                              (BUDGET_EXCEEDED → rollback total) y pasa a
                              APLICADA con auditoría.
    3. `liberar_reparto`    — solo APLICADA: libera las reservas DISTRITALES
                              creadas (`liberar_reserva`) y vuelve a CALCULADA.
    4. `recalcular_reparto` — actualiza poblaciones/porcentajes/montos por
                              distrito (upsert + borra ausentes) y recalcula;
                              solo si NO está APLICADA.

Métodos (`MetodoDistribucion`) y convenciones documentadas:
    - MANUAL / MONTO_FIJO / FORMULA: el monto de cada distrito lo provee el
      usuario (campo `monto` de las asignaciones). MONTO_FIJO comparte el
      manejo de MANUAL (montos fijos por distrito); FORMULA recibe el
      resultado de la fórmula calculado por el cliente. La suma DEBE ser
      exactamente la bolsa total.
    - PORCENTAJE: `porcentaje` en escala 0-100 (50 = 50%); la suma de
      porcentajes debe ser 100.
    - POBLACION: `poblacion` por distrito; monto = bolsa * pob / Σpob.

Ajuste de redondeo (garantiza SUM(monto_final) == bolsa_total EXACTO):
    cada monto se redondea a 2 decimales; la diferencia (en centavos) entre la
    bolsa y la suma se distribuye de a un centavo sobre los distritos con
    mayor residuo fraccional del cálculo crudo (empate → menor id); ese
    centavo queda en `ajuste` (monto_final - monto_calculado). Con
    diferencia negativa se quita el centavo a los distritos con menor residuo.
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento

from .models import (
    EstadoDistribucionTerritorial,
    EstadoReserva,
    MetodoDistribucion,
    Reserva,
    AsignacionTerritorial,
    DistribucionTerritorial,
    TipoReserva,
)
from .services import (
    ErrorDisponibilidad,
    _bloquear_fuentes,
    _disponible_por_fuente,
    liberar_reserva,
    registrar_auditoria,
    techo_distribuible_por_fuente,
    validar_gestion_para_distribucion,
)

_CENTAVO = Decimal('0.01')
_CERO = Decimal('0.00')


def _redondear(valor):
    """Redondea a 2 decimales (HALF_UP), nunca float."""
    return valor.quantize(_CENTAVO, rounding=ROUND_HALF_UP)


def _montos_crudos(distribucion, asignaciones):
    """monto crudo (sin redondear) por distrito según el método.

    Valida los datos de entrada y devuelve {asignacion_id: Decimal crudo}.
    """
    metodo = distribucion.metodo
    bolsa = distribucion.bolsa_total

    if metodo == MetodoDistribucion.POBLACION:
        for a in asignaciones:
            if not a.poblacion or a.poblacion <= 0:
                raise ValidationError(
                    f'El distrito {a.distrito} debe indicar una población '
                    'mayor a 0 (método POBLACION).'
                )
        total_pob = sum(Decimal(a.poblacion) for a in asignaciones)
        if total_pob <= 0:
            raise ValidationError('La población total debe ser mayor a 0.')
        return {
            a.id: bolsa * Decimal(a.poblacion) / total_pob
            for a in asignaciones
        }

    if metodo == MetodoDistribucion.PORCENTAJE:
        for a in asignaciones:
            if a.porcentaje is None or a.porcentaje <= 0:
                raise ValidationError(
                    f'El distrito {a.distrito} debe indicar un porcentaje '
                    'mayor a 0 (método PORCENTAJE, escala 0-100).'
                )
        suma_pct = sum(a.porcentaje for a in asignaciones)
        if suma_pct != Decimal('100'):
            raise ValidationError(
                f'La suma de porcentajes debe ser 100 '
                f'(actual: {suma_pct.quantize(Decimal("0.0001"))}).'
            )
        return {
            a.id: bolsa * a.porcentaje / Decimal('100')
            for a in asignaciones
        }

    # MANUAL / MONTO_FIJO / FORMULA: montos provistos por el usuario.
    for a in asignaciones:
        if a.monto_calculado is None or a.monto_calculado <= 0:
            raise ValidationError(
                f'El distrito {a.distrito} debe indicar un monto mayor a 0 '
                f'(método {distribucion.get_metodo_display()}).'
            )
    suma = sum(a.monto_calculado for a in asignaciones)
    if suma != bolsa:
        raise ValidationError(
            f'La suma de montos debe ser exactamente la bolsa '
            f'({bolsa}); actual: {suma}.'
        )
    return {a.id: a.monto_calculado for a in asignaciones}


def _aplicar_ajuste_redondeo(asignaciones, crudos, bolsa):
    """Resuelve monto_calculado/ajuste/monto_final con SUM == bolsa exacto.

    Los montos crudos se redondean a 2 decimales; la diferencia (en centavos)
    se reparte de a un centavo sobre los distritos con mayor residuo
    fraccional (empate → menor id) y queda en `ajuste`. Con diferencia
    negativa se resta el centavo a los de menor residuo.
    """
    ordenados = sorted(asignaciones, key=lambda a: a.id)
    redondeados = {
        a.id: _redondear(crudos[a.id])
        for a in ordenados
    }
    diferencia = bolsa - sum(redondeados.values())
    centavos = int(abs(diferencia) * 100)
    signo = 1 if diferencia > 0 else -1

    if centavos:
        residuos = sorted(
            ordenados,
            key=lambda a: (
                crudos[a.id] - redondeados[a.id]
                if signo > 0 else redondeados[a.id] - crudos[a.id]
            ),
            reverse=True,
        )
        con_ajuste = {a.id for a in residuos[:centavos]}
    else:
        con_ajuste = set()

    for a in ordenados:
        a.monto_calculado = redondeados[a.id]
        a.ajuste = _CENTAVO * signo if a.id in con_ajuste else _CERO
        a.monto_final = a.monto_calculado + a.ajuste


def calcular_reparto(distribucion, usuario=None):
    """Calcula el reparto de la bolsa por distrito (sin crear reservas).

    Valida los datos según el método, aplica el ajuste de redondeo, persiste
    los montos y pasa la distribución a CALCULADA. Rechaza distribuciones
    APLICADAS. Registra auditoría (modificar) con los montos por distrito
    antes/después (Fase 11).
    """
    if distribucion.estado == EstadoDistribucionTerritorial.APLICADA:
        raise ValidationError(
            'No se puede recalcular una distribución territorial aplicada.'
        )
    asignaciones = list(
        distribucion.asignaciones.select_related('distrito').all()
    )
    if not asignaciones:
        raise ValidationError(
            'Debe cargar al menos un distrito para calcular el reparto.'
        )

    estado_previo = distribucion.estado
    montos_previos = {
        str(a.distrito_id): str(a.monto_final) for a in asignaciones
    }
    crudos = _montos_crudos(distribucion, asignaciones)
    _aplicar_ajuste_redondeo(asignaciones, crudos, distribucion.bolsa_total)

    distribucion.estado = EstadoDistribucionTerritorial.CALCULADA
    distribucion.save(update_fields=['estado', 'updated_at'])
    for a in asignaciones:
        a.save(update_fields=[
            'monto_calculado', 'ajuste', 'monto_final', 'updated_at',
        ])
    registrar_auditoria(
        usuario,
        'UPDATE',
        'DistribucionTerritorial',
        distribucion.id,
        {'estado': estado_previo, 'distritos': montos_previos},
        {
            'estado': distribucion.estado,
            'total': str(distribucion.bolsa_total),
            'distritos': {
                str(a.distrito_id): str(a.monto_final) for a in asignaciones
            },
        },
        gestion=distribucion.gestion.anio,
        motivo=(
            f'Reparto {distribucion.get_metodo_display()} calculado: '
            f'{distribucion.bolsa_total} Bs en {len(asignaciones)} distritos '
            f'(gestión {distribucion.gestion.anio})'
        ),
    )
    return distribucion


@transaction.atomic
def aplicar_reparto(distribucion, usuario):
    """Materializa el reparto como reservas DISTRITALES (una por distrito).

    Valida disponibilidad por fuente contra el techo fijado (misma lógica de
    `crear_reserva`: BUDGET_EXCEEDED con requested/available/difference); si
    algo excede, la transacción revierte TODO (ninguna reserva queda creada).
    Con éxito pasa a APLICADA y registra auditoría.
    """
    if distribucion.estado != EstadoDistribucionTerritorial.CALCULADA:
        raise ValidationError(
            'Solo una distribución territorial CALCULADA puede aplicarse '
            f'(estado actual: {distribucion.get_estado_display()}).'
        )
    if not distribucion.fuente_id:
        raise ValidationError(
            'Debe indicar la fuente de financiamiento de la bolsa.'
        )
    validar_gestion_para_distribucion(distribucion.gestion)
    techo = techo_distribuible_por_fuente(distribucion.gestion)
    if not techo:
        raise ValidationError(
            f'La gestión {distribucion.gestion.anio} no tiene un techo '
            'directivo fijado; la distribución está bloqueada.'
        )

    asignaciones = list(
        distribucion.asignaciones
        .filter(monto_final__gt=0)
        .select_related('distrito')
    )
    if not asignaciones:
        raise ValidationError(
            'No hay asignaciones con monto mayor a 0 para aplicar.'
        )

    _bloquear_fuentes(distribucion.gestion, {distribucion.fuente_id})
    disponible = _disponible_por_fuente(distribucion.gestion)
    saldo = disponible.get(distribucion.fuente_id, _CERO)
    total = sum(a.monto_final for a in asignaciones)
    if total > saldo:
        raise ErrorDisponibilidad(distribucion.fuente_id, total, saldo)

    for a in asignaciones:
        Reserva.objects.create(
            gestion=distribucion.gestion,
            version=distribucion.version,
            fuente_id=distribucion.fuente_id,
            organismo_id=distribucion.organismo_id,
            tipo=TipoReserva.DISTRITAL,
            monto=a.monto_final,
            motivo=f'Distribución territorial: {a.distrito}',
            estado=EstadoReserva.ACTIVA,
            created_by=usuario,
            updated_by=usuario,
        )

    distribucion.estado = EstadoDistribucionTerritorial.APLICADA
    distribucion.updated_by = usuario
    distribucion.save(update_fields=['estado', 'updated_by', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'DistribucionTerritorial',
        distribucion.id,
        resumen=(
            f'Distribución territorial aplicada: {total} Bs en '
            f'{len(asignaciones)} distritos '
            f'(gestión {distribucion.gestion.anio})'
        ),
        datos_posteriores={
            'estado': EstadoDistribucionTerritorial.APLICADA,
            'total': str(total),
            'distritos': [
                {
                    'distrito': str(a.distrito_id),
                    'monto': str(a.monto_final),
                }
                for a in asignaciones
            ],
        },
        gestion=distribucion.gestion.anio,
    )
    return distribucion


@transaction.atomic
def liberar_reparto(distribucion, usuario):
    """Libera las reservas DISTRITALES de la distribución (solo APLICADA).

    Identifica las reservas por (gestion, version, tipo DISTRITAL, estado
    ACTIVA y motivo 'Distribución territorial: <distrito>'); cada una se
    libera con `liberar_reserva` (devuelve el disponible) y la distribución
    vuelve a CALCULADA con auditoría.
    """
    if distribucion.estado != EstadoDistribucionTerritorial.APLICADA:
        raise ValidationError(
            'Solo una distribución territorial APLICADA puede liberarse '
            f'(estado actual: {distribucion.get_estado_display()}).'
        )
    motivos = {
        f'Distribución territorial: {a.distrito}'
        for a in distribucion.asignaciones.select_related('distrito')
    }
    reservas = list(
        Reserva.objects.filter(
            gestion=distribucion.gestion,
            version=distribucion.version,
            tipo=TipoReserva.DISTRITAL,
            estado=EstadoReserva.ACTIVA,
            motivo__in=motivos,
        )
    )
    if not reservas:
        raise ValidationError(
            'No se encontraron reservas DISTRITALES activas de esta '
            'distribución.'
        )
    total = sum(r.monto for r in reservas)
    for reserva in reservas:
        liberar_reserva(reserva, usuario)

    distribucion.estado = EstadoDistribucionTerritorial.CALCULADA
    distribucion.updated_by = usuario
    distribucion.save(update_fields=['estado', 'updated_by', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.MODIFICAR,
        'DistribucionTerritorial',
        distribucion.id,
        resumen=(
            f'Distribución territorial liberada: {total} Bs en '
            f'{len(reservas)} reservas DISTRITALES '
            f'(gestión {distribucion.gestion.anio})'
        ),
        datos_previos={'estado': EstadoDistribucionTerritorial.APLICADA},
        datos_posteriores={
            'estado': EstadoDistribucionTerritorial.CALCULADA,
            'total_liberado': str(total),
        },
        gestion=distribucion.gestion.anio,
    )
    return distribucion


@transaction.atomic
def recalcular_reparto(distribucion, datos_distritos, usuario=None):
    """Actualiza las asignaciones (población/porcentaje/monto) y recalcula.

    Reemplaza el set de distritos: crea/actualiza los indicados y elimina los
    ausentes del payload. Solo si la distribución NO está APLICADA. Los
    montos de MANUAL/MONTO_FIJO/FORMULA se reciben como `monto`.
    """
    if distribucion.estado == EstadoDistribucionTerritorial.APLICADA:
        raise ValidationError(
            'No se puede recalcular una distribución territorial aplicada.'
        )
    if not isinstance(datos_distritos, (list, tuple)) or not datos_distritos:
        raise ValidationError(
            'Debe indicar al menos un distrito ({distrito, poblacion?, '
            'porcentaje?, monto?}).'
        )

    entradas = {}
    for fila in datos_distritos:
        distrito_id = fila.get('distrito')
        if not distrito_id:
            raise ValidationError('Cada fila debe indicar un distrito.')
        try:
            distrito_id = uuid.UUID(str(distrito_id))
        except (ValueError, TypeError):
            raise ValidationError(
                f'Identificador de distrito inválido: {distrito_id}.'
            )
        if distrito_id in entradas:
            raise ValidationError(f'Distrito duplicado: {distrito_id}.')
        entradas[distrito_id] = fila

    from apps.territorio.models import Distrito
    existentes = set(
        Distrito.objects.filter(id__in=entradas)
        .values_list('id', flat=True)
    )
    faltantes = set(entradas) - existentes
    if faltantes:
        raise ValidationError(
            f'Distrito(s) inexistente(s): '
            f'{sorted(str(f) for f in faltantes)}'
        )

    actuales = {
        a.distrito_id: a
        for a in distribucion.asignaciones.all()
    }
    for distrito_id, fila in entradas.items():
        asignacion = actuales.get(distrito_id)
        campos = {}
        if 'poblacion' in fila:
            campos['poblacion'] = fila['poblacion']
        if 'porcentaje' in fila:
            campos['porcentaje'] = fila['porcentaje']
        if 'monto' in fila:
            campos['monto_calculado'] = fila['monto']
        if asignacion is None:
            AsignacionTerritorial.objects.create(
                distribucion=distribucion,
                distrito_id=distrito_id,
                poblacion=fila.get('poblacion'),
                porcentaje=fila.get('porcentaje'),
                monto_calculado=fila.get('monto', _CERO),
                created_by=usuario,
                updated_by=usuario,
            )
        else:
            for campo, valor in campos.items():
                setattr(asignacion, campo, valor)
            asignacion.save()

    for distrito_id, asignacion in actuales.items():
        if distrito_id not in entradas:
            asignacion.delete()

    return calcular_reparto(distribucion, usuario)
