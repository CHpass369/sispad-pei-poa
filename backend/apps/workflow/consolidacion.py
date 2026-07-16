"""
Servicio de consolidación institucional del POA — SISPOA Sacaba.

Funciones de alto nivel para consolidar, verificar consistencia y generar
actas de cierre de la formulación presupuestaria anual. Usa exclusivamente
Django ORM y Decimal para cálculos monetarios.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db.models import (
    Count,
    F,
    Q,
    Sum,
    Value,
    DecimalField,
)
from django.db.models.functions import Coalesce

from apps.indicadores.models import Operacion, Producto
from apps.inversion.models import ProyectoInversion
from apps.organizacion.models import UnidadOrganizacional
from apps.planificacion.models import AccionCortoPlazo
from apps.presupuesto.models import (
    LineaPresupuestaria,
    ProgramaPresupuestario,
)
from apps.techos.models import DistribucionTecho, TechoPresupuestario
from apps.workflow.models import Aprobacion, EnvioFormulacion, Observacion

# ---------------------------------------------------------------------------
# Configuración de asignaciones obligatorias (ajustable por municipio)
# ---------------------------------------------------------------------------
# Estas reglas son mandatorias para municipios en Bolivia. Los valores
# porcentuales y las claves de búsqueda deben verificarse contra la
# codificación programática vigente del Gobierno Autónomo Municipal de Sacaba.
#
# `clave_nombre`: texto buscado en el nombre del programa (icontains) para
#   identificar a qué categoría pertenece.
# `codigos_programa`: lista explícita de códigos de programa (alternativa
#   exacta a la búsqueda por nombre).
# `codigos_objeto_gasto`: lista de códigos de objeto del gasto asociados.

ASIGNACIONES_OBLIGATORIAS: dict[str, dict[str, Any]] = {
    "sus": {
        "nombre": "Seguro Universal de Salud (SUS)",
        "clave_nombre": "salud",
        "codigos_programa": [],
        "codigos_objeto_gasto": [],
        "porcentaje_minimo": Decimal("0.10"),  # 10 % del presupuesto total
    },
    "renta_dignidad": {
        "nombre": "Renta Dignidad",
        "clave_nombre": "renta dignidad",
        "codigos_programa": [],
        "codigos_objeto_gasto": [],
        "porcentaje_minimo": Decimal("0.0075"),  # 0,75 % del presupuesto total
    },
    "seguridad_ciudadana": {
        "nombre": "Seguridad Ciudadana",
        "clave_nombre": "seguridad",
        "codigos_programa": [],
        "codigos_objeto_gasto": [],
        "porcentaje_minimo": Decimal("0.10"),  # 10 % del presupuesto total
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _monto(valor: Any) -> Decimal:
    """Retorna Decimal, o 0 si el valor es None."""
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor))


def _qs_activos(gestion: int):
    """QuerySet base de líneas activas para una gestión."""
    return LineaPresupuestaria.objects.filter(gestion=gestion, activo=True)


def _total_formulado(gestion: int) -> Decimal:
    """Suma de importes de todas las líneas activas en la gestión."""
    return _monto(
        _qs_activos(gestion).aggregate(
            total=Coalesce(Sum("importe", output_field=DecimalField()), Value(Decimal("0.00")))
        )["total"]
    )


def _total_techo(gestion: int) -> Decimal:
    """Suma de todos los techos presupuestarios activos de la gestión."""
    return _monto(
        TechoPresupuestario.objects.filter(gestion=gestion, activo=True).aggregate(
            total=Coalesce(Sum("monto_total", output_field=DecimalField()), Value(Decimal("0.00")))
        )["total"]
    )


def _total_distribuido(gestion: int) -> Decimal:
    """Suma de todas las distribuciones de techo activas de la gestión."""
    return _monto(
        DistribucionTecho.objects.filter(
            techo__gestion=gestion, activo=True
        ).aggregate(
            total=Coalesce(
                Sum("monto_asignado", output_field=DecimalField()), Value(Decimal("0.00"))
            )
        )["total"]
    )


# ---------------------------------------------------------------------------
# 1. Consolidación institucional
# ---------------------------------------------------------------------------

def consolidar_poa_institucional(gestion: int) -> dict[str, Any]:
    """
    Consolidación institucional del POA para una gestión.

    1. Suma líneas presupuestarias por programa, fuente, organismo y objeto del gasto.
    2. Compara totales: techo vs formulado vs (aprobado si existe).
    3. Identifica unidades organizacionales que no formularon.
    4. Identifica acciones sin presupuesto y presupuesto sin acción.
    5. Detecta productos y operaciones duplicados.
    6. Calcula brechas de asignaciones obligatorias (SUS, Renta Dignidad, Seguridad Ciudadana).

    Args:
        gestion: Año de gestión (ej. 2025).

    Returns:
        Dict con estructura:
        - gestion
        - fecha_consolidacion
        - totales (techo, formulado, aprobado, diferencia)
        - resultados_por_programa (list[dict])
        - alertas (list[dict])
        - asignaciones_obligatorias (list[dict])
        - estado (str)
    """
    lineas = _qs_activos(gestion)

    # ── Totales generales ──────────────────────────────────────────────
    total_form = _total_formulado(gestion)
    total_tech = _total_techo(gestion)
    total_dist = _total_distribuido(gestion)

    # Aprobado: si existe una aprobación de consolidación aprobada se usa
    # el formulado de la versión correspondiente; si no, None.
    aprobacion = (
        Aprobacion.objects.filter(
            gestion=gestion, tipo="consolidacion", estado="aprobado"
        )
        .order_by("-version")
        .first()
    )
    total_aprobado: Decimal | None = (
        total_form if aprobacion else None
    )

    totales = {
        "techo": total_tech,
        "techo_distribuido": total_dist,
        "saldo_por_distribuir": total_tech - total_dist,
        "formulado": total_form,
        "aprobado": total_aprobado,
        "diferencia_techo_vs_formulado": total_tech - total_form,
        "diferencia_techo_vs_distribuido": total_tech - total_dist,
        "porcentaje_formulado_vs_techo": (
            round(float((total_form / total_tech) * 100), 2)
            if total_tech > 0
            else 0.0
        ),
    }

    # ── Resultados por programa ─────────────────────────────────────────
    programas_qs = ProgramaPresupuestario.objects.filter(
        gestion=gestion, activo=True
    ).select_related("ue_responsable")

    resultados_por_programa = []
    for prog in programas_qs:
        prog_lineas = lineas.filter(programa=prog)
        total_prog = _monto(
            prog_lineas.aggregate(
                total=Coalesce(Sum("importe", output_field=DecimalField()), Value(Decimal("0.00")))
            )["total"]
        )

        # Detalle por fuente / organismo / objeto del gasto
        detalle = list(
            prog_lineas.values(
                fuente_codigo=F("fuente__codigo"),
                fuente_nombre=F("fuente__denominacion"),
                organismo_codigo=F("organismo__codigo"),
                organismo_nombre=F("organismo__denominacion"),
                objeto_codigo=F("objeto_gasto__codigo"),
                objeto_nombre=F("objeto_gasto__denominacion"),
            )
            .annotate(
                total_linea=Coalesce(
                    Sum("importe", output_field=DecimalField()), Value(Decimal("0.00"))
                ),
                cantidad=Count("id"),
            )
            .order_by("-total_linea")
        )

        # Techo asociado al programa (distribuciones)
        techo_prog = _monto(
            DistribucionTecho.objects.filter(
                techo__gestion=gestion, programa=prog, activo=True
            ).aggregate(
                total=Coalesce(
                    Sum("monto_asignado", output_field=DecimalField()),
                    Value(Decimal("0.00")),
                )
            )["total"]
        )

        ue_resp = prog.ue_responsable
        resultados_por_programa.append(
            {
                "programa_codigo": prog.codigo,
                "programa_nombre": prog.nombre,
                "ue_responsable_codigo": ue_resp.codigo if ue_resp else None,
                "ue_responsable_nombre": ue_resp.nombre if ue_resp else None,
                "total_formulado": total_prog,
                "total_techo_asignado": techo_prog,
                "diferencia": techo_prog - total_prog,
                "cantidad_lineas": prog_lineas.count(),
                "detalle_fuente_organismo_objeto": detalle,
            }
        )

    # ── Unidades sin formular ───────────────────────────────────────────
    # Se considera "unidad debe formular" a toda UO activa que:
    #   (a) tenga al menos una UE asociada, y
    #   (b) no haya registrado un envío de formulación para la gestión.
    uos_con_envio = set(
        EnvioFormulacion.objects.filter(gestion=gestion, activo=True).values_list(
            "unidad_id", flat=True
        )
    )
    uos_con_ues = UnidadOrganizacional.objects.filter(
        gestion=gestion, activo=True, ues_asociadas__isnull=False
    ).distinct()

    unidades_sin_formular = []
    for uo in uos_con_ues:
        if uo.id not in uos_con_envio:
            unidades_sin_formular.append(
                {
                    "unidad_codigo": uo.codigo,
                    "unidad_nombre": uo.nombre,
                    "unidad_sigla": uo.sigla,
                }
            )

    # ── Inconsistencias ─────────────────────────────────────────────────
    # Acciones de corto plazo sin ninguna línea presupuestaria vinculada
    acp_con_ppto_ids = set(
        lineas.exclude(operacion__isnull=True)
        .values_list("operacion__accion_corto_plazo_id", flat=True)
        .distinct()
    )
    acciones_sin_presupuesto = list(
        AccionCortoPlazo.objects.filter(gestion=gestion, activo=True)
        .exclude(id__in=acp_con_ppto_ids)
        .values("codigo", "nombre", unidad_responsable_nombre=F("unidad_responsable__nombre"))
    )

    # Líneas presupuestarias sin operación vinculada
    lineas_sin_operacion = list(
        lineas.filter(operacion__isnull=True).values(
            "id",
            "programa__codigo",
            "objeto_gasto__denominacion",
            "importe",
        )[:100]  # limitar a 100 para no explotar la respuesta
    )

    # ── Duplicidades ────────────────────────────────────────────────────
    # Productos con el mismo código dentro de la misma gestión
    duplicados_productos = list(
        Producto.objects.filter(
            accion_corto_plazo__gestion=gestion, activo=True
        )
        .values("codigo", "nombre")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )

    # Operaciones con el mismo código dentro de la misma gestión
    duplicados_operaciones = list(
        Operacion.objects.filter(
            accion_corto_plazo__gestion=gestion, activo=True
        )
        .values("codigo", "nombre")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )

    # ── Alertas ─────────────────────────────────────────────────────────
    alertas: list[dict[str, Any]] = []

    for u in unidades_sin_formular:
        alertas.append(
            {
                "tipo": "unidad_sin_formular",
                "severidad": "grave",
                "mensaje": (
                    f"La unidad {u['unidad_nombre']} ({u['unidad_codigo']}) "
                    "no ha realizado ningún envío de formulación."
                ),
                "detalle": u,
            }
        )

    for acp in acciones_sin_presupuesto:
        alertas.append(
            {
                "tipo": "accion_sin_presupuesto",
                "severidad": "moderada",
                "mensaje": (
                    f"La acción de corto plazo {acp['codigo']} — "
                    f"{acp['nombre'][:80]} no tiene líneas presupuestarias."
                ),
                "detalle": acp,
            }
        )

    if lineas_sin_operacion:
        alertas.append(
            {
                "tipo": "presupuesto_sin_accion",
                "severidad": "moderada",
                "mensaje": (
                    f"Existen {len(lineas_sin_operacion)} líneas presupuestarias "
                    "sin operación vinculada (presupuesto sin acción)."
                ),
                "detalle": {"cantidad": len(lineas_sin_operacion), "muestra": lineas_sin_operacion[:10]},
            }
        )

    for dup in duplicados_productos:
        alertas.append(
            {
                "tipo": "producto_duplicado",
                "severidad": "leve",
                "mensaje": (
                    f"El producto '{dup['codigo']} — {dup['nombre'][:80]}' "
                    f"aparece {dup['total']} veces en la gestión."
                ),
                "detalle": dup,
            }
        )

    for dup in duplicados_operaciones:
        alertas.append(
            {
                "tipo": "operacion_duplicada",
                "severidad": "leve",
                "mensaje": (
                    f"La operación '{dup['codigo']} — {dup['nombre'][:80]}' "
                    f"aparece {dup['total']} veces en la gestión."
                ),
                "detalle": dup,
            }
        )

    # ── Asignaciones obligatorias ───────────────────────────────────────
    resultado_asignaciones = _calcular_asignaciones_obligatorias(gestion, total_form)
    for asig in resultado_asignaciones:
        if not asig["cumple"]:
            alertas.append(
                {
                    "tipo": f"brecha_{asig['codigo']}",
                    "severidad": "grave",
                    "mensaje": asig["mensaje"],
                    "detalle": {
                        "asignado": asig["asignado"],
                        "minimo_requerido": asig["minimo_requerido"],
                        "diferencia": asig["diferencia"],
                    },
                }
            )

    # ── Estado final ────────────────────────────────────────────────────
    estado = _determinar_estado(alertas)

    return {
        "gestion": gestion,
        "fecha_consolidacion": date.today().isoformat(),
        "totales": totales,
        "resultados_por_programa": resultados_por_programa,
        "alertas": alertas,
        "asignaciones_obligatorias": resultado_asignaciones,
        "unidades_sin_formular": unidades_sin_formular,
        "estado": estado,
    }


# ---------------------------------------------------------------------------
# 2. Verificación de consistencia presupuestaria
# ---------------------------------------------------------------------------

def verificar_consistencia_presupuestaria(gestion: int) -> dict[str, Any]:
    """
    Verifica la consistencia de las líneas presupuestarias y techos.

    Comprueba:
    1. Líneas con llave presupuestaria incompleta (proyecto, actividad u organismo nulos).
    2. Programas sin UE responsable.
    3. Importes inconsistentes anual / plurianual (plurianual < anual).
    4. Proyectos de inversión sin código SISIN-WEB.
    5. Techos sin distribución o con saldo remanente.

    Args:
        gestion: Año de gestión.

    Returns:
        Dict con listas de hallazgos por categoría y un resumen.
    """
    hallazgos: list[dict[str, Any]] = []
    lineas = _qs_activos(gestion)

    # ── 1. Llave presupuestaria incompleta ──────────────────────────────
    lineas_incompletas = lineas.filter(
        Q(proyecto__isnull=True) | Q(actividad__isnull=True) | Q(organismo__isnull=True)
    )
    total_incompletas = lineas_incompletas.count()
    if total_incompletas:
        muestra = list(
            lineas_incompletas.values(
                "id",
                "programa__codigo",
                "objeto_gasto__denominacion",
                "importe",
            )[:20]
        )
        hallazgos.append(
            {
                "categoria": "llave_incompleta",
                "severidad": "grave",
                "mensaje": (
                    f"{total_incompletas} líneas presupuestarias tienen llave incompleta "
                    "(proyecto, actividad u organismo sin especificar)."
                ),
                "cantidad": total_incompletas,
                "muestra": muestra,
            }
        )

    # ── 2. Programas sin UE responsable ─────────────────────────────────
    programas_sin_ue = ProgramaPresupuestario.objects.filter(
        gestion=gestion, activo=True, ue_responsable__isnull=True
    )
    total_sin_ue = programas_sin_ue.count()
    if total_sin_ue:
        hallazgos.append(
            {
                "categoria": "programa_sin_ue",
                "severidad": "grave",
                "mensaje": (
                    f"{total_sin_ue} programas presupuestarios no tienen "
                    "unidad ejecutora responsable asignada."
                ),
                "cantidad": total_sin_ue,
                "programas": list(programas_sin_ue.values("codigo", "nombre")),
            }
        )

    # ── 3. Importes inconsistentes anual / plurianual ───────────────────
    # Casos: plurianual < anual (inconsistencia grave),
    #        plurianual nulo pero importe_plurianual en otras líneas del mismo proyecto.
    inconsistentes_pluri = lineas.filter(
        Q(importe_plurianual__isnull=False)
        & Q(importe_plurianual__lt=F("importe"))
    )
    total_inconsistentes = inconsistentes_pluri.count()
    if total_inconsistentes:
        muestra = list(
            inconsistentes_pluri.values(
                "id",
                "programa__codigo",
                "importe",
                "importe_plurianual",
            )[:20]
        )
        hallazgos.append(
            {
                "categoria": "inconsistencia_anual_plurianual",
                "severidad": "moderada",
                "mensaje": (
                    f"{total_inconsistentes} líneas tienen importe plurianual "
                    "menor al importe anual."
                ),
                "cantidad": total_inconsistentes,
                "muestra": muestra,
            }
        )

    # ── 4. Proyectos de inversión sin código SISIN ──────────────────────
    proyectos_sin_sisin = ProyectoInversion.objects.filter(
        Q(gestion_inicio__lte=gestion) | Q(programacion_fisica_financiera__gestion=gestion),
        activo=True,
    ).filter(Q(codigo_sisin="") | Q(codigo_sisin__isnull=True)).distinct()
    total_sin_sisin = proyectos_sin_sisin.count()
    if total_sin_sisin:
        hallazgos.append(
            {
                "categoria": "proyecto_sin_sisin",
                "severidad": "grave",
                "mensaje": (
                    f"{total_sin_sisin} proyectos de inversión no tienen "
                    "código SISIN-WEB registrado."
                ),
                "cantidad": total_sin_sisin,
                "proyectos": list(
                    proyectos_sin_sisin.values(
                        "codigo_interno",
                        "nombre",
                        programa_codigo=F("programa__codigo"),
                    )
                ),
            }
        )

    # ── 5. Techos sin distribuir o con saldo ────────────────────────────
    techos = TechoPresupuestario.objects.filter(gestion=gestion, activo=True)
    for techo in techos:
        distribuciones = techo.distribuciones.filter(activo=True)
        total_asignado = _monto(
            distribuciones.aggregate(
                total=Coalesce(
                    Sum("monto_asignado", output_field=DecimalField()),
                    Value(Decimal("0.00")),
                )
            )["total"]
        )
        total_reserva = _monto(
            distribuciones.aggregate(
                total=Coalesce(
                    Sum("monto_reserva", output_field=DecimalField()),
                    Value(Decimal("0.00")),
                )
            )["total"]
        )
        saldo = techo.monto_total - total_asignado - total_reserva

        if not distribuciones.exists():
            hallazgos.append(
                {
                    "categoria": "techo_sin_distribuir",
                    "severidad": "grave",
                    "mensaje": (
                        f"El techo de Bs {techo.monto_total} de la fuente "
                        f"{techo.fuente.denominacion} no tiene ninguna distribución."
                    ),
                    "techo_id": str(techo.id),
                    "fuente": techo.fuente.denominacion,
                    "monto_total": techo.monto_total,
                }
            )
        elif saldo > 0:
            hallazgos.append(
                {
                    "categoria": "techo_con_saldo",
                    "severidad": "moderada",
                    "mensaje": (
                        f"El techo de Bs {techo.monto_total} de la fuente "
                        f"{techo.fuente.denominacion} tiene un saldo de Bs {saldo} "
                        "sin distribuir."
                    ),
                    "techo_id": str(techo.id),
                    "fuente": techo.fuente.denominacion,
                    "monto_total": techo.monto_total,
                    "total_asignado": total_asignado,
                    "total_reserva": total_reserva,
                    "saldo": saldo,
                }
            )

    # ── Resumen ─────────────────────────────────────────────────────────
    resumen = {
        "total_hallazgos": len(hallazgos),
        "hallazgos_graves": sum(1 for h in hallazgos if h.get("severidad") == "grave"),
        "hallazgos_moderados": sum(1 for h in hallazgos if h.get("severidad") == "moderada"),
        "hallazgos_leves": sum(1 for h in hallazgos if h.get("severidad") == "leve"),
        "consistente": len(hallazgos) == 0,
    }

    return {
        "gestion": gestion,
        "fecha_verificacion": date.today().isoformat(),
        "resumen": resumen,
        "hallazgos": hallazgos,
    }


# ---------------------------------------------------------------------------
# 3. Acta de consolidación
# ---------------------------------------------------------------------------

def generar_acta_consolidacion(
    gestion: int,
    responsable: str | None = None,
) -> dict[str, Any]:
    """
    Genera el acta de consolidación institucional del POA.

    Args:
        gestion: Año de gestión.
        responsable: Nombre del responsable de la consolidación (opcional).

    Returns:
        Dict con los metadatos del acta más el texto completo.
    """
    # Datos base
    consolidacion = consolidar_poa_institucional(gestion)
    verificacion = verificar_consistencia_presupuestaria(gestion)
    fecha_hoy = date.today()

    # Observaciones abiertas / cerradas
    observaciones = Observacion.objects.filter(gestion=gestion)
    total_obs = observaciones.count()
    abiertas = observaciones.filter(estado__in=["abierta", "respondida", "aceptada", "rechazada"])
    cerradas = observaciones.filter(estado="cerrada")
    resueltas = observaciones.filter(estado="cerrada")
    pendientes = observaciones.filter(
        estado__in=["abierta", "respondida", "aceptada", "rechazada"]
    )

    # Composición del acta
    totales = consolidacion["totales"]
    estado = consolidacion["estado"]
    alertas = consolidacion["alertas"]
    programas = consolidacion["resultados_por_programa"]

    # ── Generar texto del acta ─────────────────────────────────────────
    lineas_texto: list[str] = []
    lineas_texto.append("=" * 72)
    lineas_texto.append("ACTA DE CONSOLIDACIÓN INSTITUCIONAL DEL POA")
    lineas_texto.append(f"SISTEMA DE PLANIFICACIÓN OPERATIVA ANUAL — SISPOA SACABA")
    lineas_texto.append("=" * 72)
    lineas_texto.append("")
    lineas_texto.append(f"Gestión:                     {gestion}")
    lineas_texto.append(f"Fecha de consolidación:      {fecha_hoy.strftime('%d/%m/%Y')}")
    lineas_texto.append(f"Responsable:                 {responsable or '—'}")
    lineas_texto.append(f"Estado:                      {estado.upper()}")
    lineas_texto.append("")

    # ── Totales generales ───────────────────────────────────────────────
    lineas_texto.append("-" * 72)
    lineas_texto.append("1. TOTALES GENERALES")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    lineas_texto.append(f"  Techo presupuestario:            Bs {totales['techo']:>14,.2f}")
    lineas_texto.append(f"  Techo distribuido:               Bs {totales['techo_distribuido']:>14,.2f}")
    lineas_texto.append(f"  Saldo por distribuir:            Bs {totales['saldo_por_distribuir']:>14,.2f}")
    lineas_texto.append(f"  Monto formulado:                 Bs {totales['formulado']:>14,.2f}")
    if totales["aprobado"] is not None:
        lineas_texto.append(f"  Monto aprobado:                  Bs {totales['aprobado']:>14,.2f}")
    lineas_texto.append(f"  Diferencia techo vs formulado:   Bs {totales['diferencia_techo_vs_formulado']:>14,.2f}")
    lineas_texto.append(f"  Ejecución presupuestaria:         {totales['porcentaje_formulado_vs_techo']:>13.2f} %")
    lineas_texto.append("")

    # ── Resultados por programa ─────────────────────────────────────────
    lineas_texto.append("-" * 72)
    lineas_texto.append("2. RESULTADOS POR PROGRAMA PRESUPUESTARIO")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    lineas_texto.append(
        f"  {'Código':<10} {'Programa':<40} {'Formulado':>16} {'Techo':>16} {'Diferencia':>16}"
    )
    lineas_texto.append("  " + "-" * 100)
    for p in programas:
        lineas_texto.append(
            f"  {p['programa_codigo']:<10} {p['programa_nombre'][:40]:<40} "
            f"Bs {p['total_formulado']:>11,.2f} "
            f"Bs {p['total_techo_asignado']:>11,.2f} "
            f"Bs {p['diferencia']:>11,.2f}"
        )
    lineas_texto.append("")

    # ── Asignaciones obligatorias ───────────────────────────────────────
    lineas_texto.append("-" * 72)
    lineas_texto.append("3. ASIGNACIONES OBLIGATORIAS")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    for asig in consolidacion["asignaciones_obligatorias"]:
        estado_asig = "✓ CUMPLE" if asig["cumple"] else "✗ INCUMPLE"
        lineas_texto.append(
            f"  {asig['nombre']:<45} {estado_asig}"
        )
        lineas_texto.append(
            f"  {' ':<45} Asignado: Bs {asig['asignado']:>14,.2f}"
        )
        lineas_texto.append(
            f"  {' ':<45} Mínimo:   Bs {asig['minimo_requerido']:>14,.2f}"
        )
        if asig["diferencia"]:
            lineas_texto.append(
                f"  {' ':<45} Brecha:   Bs {asig['diferencia']:>14,.2f}"
            )
        lineas_texto.append("")

    # ── Resumen de observaciones ────────────────────────────────────────
    lineas_texto.append("-" * 72)
    lineas_texto.append("4. OBSERVACIONES DE REVISIÓN")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    lineas_texto.append(f"  Total observaciones:            {total_obs}")
    lineas_texto.append(f"  Resueltas (cerradas):           {resueltas.count()}")
    lineas_texto.append(f"  Pendientes:                     {pendientes.count()}")
    lineas_texto.append("")

    if pendientes.exists():
        lineas_texto.append("  Observaciones pendientes:")
        for obs in pendientes.select_related("revision")[:20]:
            tipo = obs.get_tipo_display()
            sev = obs.get_severidad_display()
            lineas_texto.append(
                f"    • [{obs.codigo}] {tipo} ({sev}): "
                f"{obs.texto[:120]}"
            )
        lineas_texto.append("")

    # ── Alertas de consolidación ────────────────────────────────────────
    graves = [a for a in alertas if a["severidad"] == "grave"]
    moderadas = [a for a in alertas if a["severidad"] == "moderada"]
    leves = [a for a in alertas if a["severidad"] == "leve"]

    lineas_texto.append("-" * 72)
    lineas_texto.append("5. ALERTAS DE CONSOLIDACIÓN")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    lineas_texto.append(f"  Graves:     {len(graves)}")
    lineas_texto.append(f"  Moderadas:  {len(moderadas)}")
    lineas_texto.append(f"  Leves:      {len(leves)}")
    lineas_texto.append("")

    if graves:
        lineas_texto.append("  Alertas graves:")
        for a in graves:
            lineas_texto.append(f"    ! {a['mensaje']}")
        lineas_texto.append("")
    if moderadas:
        lineas_texto.append("  Alertas moderadas:")
        for a in moderadas:
            lineas_texto.append(f"    ? {a['mensaje']}")
        lineas_texto.append("")

    # ── Consistencia presupuestaria ─────────────────────────────────────
    lineas_texto.append("-" * 72)
    lineas_texto.append("6. VERIFICACIÓN DE CONSISTENCIA PRESUPUESTARIA")
    lineas_texto.append("-" * 72)
    lineas_texto.append("")
    resumen_verif = verificacion["resumen"]
    lineas_texto.append(
        f"  Estado: {'CONSISTENTE' if resumen_verif['consistente'] else 'CON INCONSISTENCIAS'}"
    )
    lineas_texto.append(f"  Total de hallazgos:          {resumen_verif['total_hallazgos']}")
    lineas_texto.append(f"  Graves:                      {resumen_verif['hallazgos_graves']}")
    lineas_texto.append(f"  Moderados:                   {resumen_verif['hallazgos_moderados']}")
    lineas_texto.append("")

    for h in verificacion["hallazgos"]:
        lineas_texto.append(f"  [{h['severidad'].upper()}] {h['mensaje']}")
    lineas_texto.append("")

    # ── Cierre ──────────────────────────────────────────────────────────
    lineas_texto.append("=" * 72)
    lineas_texto.append(
        f"ACTA GENERADA EL {fecha_hoy.strftime('%d/%m/%Y')} A LAS "
        f"{datetime.now().strftime('%H:%M')}"
    )
    lineas_texto.append(f"ESTADO FINAL: {estado.upper()}")
    lineas_texto.append("=" * 72)

    texto_acta = "\n".join(lineas_texto)

    # ── Unidades sin formular ───────────────────────────────────────────
    resumen_unidades = consolidacion.get("unidades_sin_formular", [])

    return {
        "gestion": gestion,
        "fecha_emision": fecha_hoy.isoformat(),
        "responsable": responsable or "",
        "estado": estado,
        "texto": texto_acta,
        "resumen": {
            "totales": totales,
            "total_programas": len(programas),
            "unidades_sin_formular": len(resumen_unidades),
            "alertas_graves": len(graves),
            "alertas_moderadas": len(moderadas),
            "alertas_leves": len(leves),
            "observaciones_abiertas": abiertas.count(),
            "observaciones_cerradas": cerradas.count(),
            "hallazgos_consistencia": resumen_verif["total_hallazgos"],
            "consistente": resumen_verif["consistente"],
        },
    }


# ---------------------------------------------------------------------------
# Funciones internas
# ---------------------------------------------------------------------------

def _calcular_asignaciones_obligatorias(
    gestion: int, total_presupuesto: Decimal
) -> list[dict[str, Any]]:
    """
    Calcula la asignación efectiva a cada categoría obligatoria y la compara
    con el mínimo legal.

    Para cada categoría, busca líneas cuyo programa coincida por:
    1. Códigos exactos de programa (``codigos_programa``), o
    2. Nombre del programa contenga la ``clave_nombre`` (icontains).
    """
    resultados: list[dict[str, Any]] = []
    lineas = _qs_activos(gestion)

    for codigo, config in ASIGNACIONES_OBLIGATORIAS.items():
        filtro = Q()

        # Filtro por códigos exactos de programa
        if config.get("codigos_programa"):
            filtro |= Q(programa__codigo__in=config["codigos_programa"])

        # Filtro por nombre (icontains)
        if config.get("clave_nombre"):
            filtro |= Q(programa__nombre__icontains=config["clave_nombre"])

        # Filtro por códigos de objeto del gasto
        if config.get("codigos_objeto_gasto"):
            filtro |= Q(objeto_gasto__codigo__in=config["codigos_objeto_gasto"])

        if not filtro:
            # Sin filtro configurado: no se puede determinar
            resultados.append(
                {
                    "codigo": codigo,
                    "nombre": config["nombre"],
                    "asignado": Decimal("0.00"),
                    "minimo_requerido": Decimal("0.00"),
                    "diferencia": Decimal("0.00"),
                    "cumple": None,
                    "mensaje": (
                        f"No se pudo determinar la asignación a "
                        f"{config['nombre']}: no hay filtros configurados "
                        "(códigos de programa o clave de nombre)."
                    ),
                }
            )
            continue

        asignado = _monto(
            lineas.filter(filtro).aggregate(
                total=Coalesce(
                    Sum("importe", output_field=DecimalField()), Value(Decimal("0.00"))
                )
            )["total"]
        )

        porcentaje = config["porcentaje_minimo"]
        minimo_requerido = (total_presupuesto * porcentaje).quantize(Decimal("0.01"))
        diferencia = asignado - minimo_requerido

        cumple = asignado >= minimo_requerido if minimo_requerido > 0 else None

        if cumple is False:
            mensaje = (
                f"Asignación a {config['nombre']}: Bs {asignado:,.2f} < "
                f"mínimo requerido Bs {minimo_requerido:,.2f} "
                f"({float(porcentaje * 100):.2f} % del total). "
                f"Brecha: Bs {abs(diferencia):,.2f}."
            )
        elif cumple is True:
            mensaje = (
                f"Asignación a {config['nombre']}: Bs {asignado:,.2f} ≥ "
                f"mínimo requerido Bs {minimo_requerido:,.2f} "
                f"({float(porcentaje * 100):.2f} % del total)."
            )
        else:
            mensaje = f"Asignación a {config['nombre']} no pudo ser evaluada."

        resultados.append(
            {
                "codigo": codigo,
                "nombre": config["nombre"],
                "asignado": asignado,
                "minimo_requerido": minimo_requerido,
                "diferencia": diferencia,
                "cumple": cumple,
                "mensaje": mensaje,
            }
        )

    return resultados


def _determinar_estado(alertas: list[dict[str, Any]]) -> str:
    """Determina el estado de la consolidación según la severidad de las alertas."""
    graves = any(a["severidad"] == "grave" for a in alertas)
    moderadas = any(a["severidad"] == "moderada" for a in alertas)

    if graves:
        return "incompleto"
    if moderadas:
        return "con_observaciones"
    return "completado"
