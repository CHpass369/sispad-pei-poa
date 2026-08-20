"""Saldo disponible por par fuente/organismo.

Lo que una OTB prioriza sale de un techo concreto. El saldo se arma con tres
piezas y el orden importa:

    techo        el Presupuesto General de Recursos, por FF/OF
    asignado     lo que ya está cargado en el Presupuesto General de Gastos
    comprometido lo priorizado en actas que todavía no se validaron

Al validarse, el acta se adjunta al gasto y su monto pasa de `comprometido` a
`asignado`: por eso no se cuenta dos veces.
"""
from django.db.models import Sum

from apps.budget.models import AperturaFuente, RecursoTecho, TechoDirectivo
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador

from .models import EstadosActa, ProyectoPriorizado


def _clave(fuente, organismo):
    return (fuente or '', organismo or '')


def techos_por_par(gestion):
    """El techo vigente de la gestión, agrupado por FF/OF.

    Solo se suman las filas raíz: el árbol de recursos tiene padres e hijos y
    sumar todo contaría la misma plata dos veces.
    """
    techo = TechoDirectivo.objects.filter(gestion__anio=int(gestion)).first()
    if techo is None:
        return {}
    filas = (RecursoTecho.objects
             .filter(version__ceiling=techo,
                     version__numero=techo.version_actual,
                     padre__isnull=True)
             .values('fuente__codigo', 'organismo__codigo',
                     'fuente__denominacion', 'organismo__denominacion')
             .annotate(monto=Sum('monto')))
    resultado = {}
    for f in filas:
        if not (f['fuente__codigo'] and f['organismo__codigo']):
            continue
        clave = _clave(f['fuente__codigo'], f['organismo__codigo'])
        actual = resultado.setdefault(clave, {
            'fuente': f['fuente__codigo'],
            'organismo': f['organismo__codigo'],
            'fuente_denominacion': f['fuente__denominacion'] or '',
            'organismo_denominacion': f['organismo__denominacion'] or '',
            'techo': 0.0,
        })
        actual['techo'] += float(f['monto'] or 0)
    return resultado


def asignado_por_par(gestion):
    """Lo ya cargado en el presupuesto de gastos."""
    filas = (AperturaFuente.objects
             .filter(allocation__gestion__anio=int(gestion))
             .values('fuente__codigo', 'organismo__codigo')
             .annotate(monto=Sum('monto')))
    return {_clave(f['fuente__codigo'], f['organismo__codigo']): float(f['monto'] or 0)
            for f in filas}


def comprometido_por_par(gestion, excluir_acta=None):
    """Lo priorizado en actas que todavía no llegaron a gasto.

    Validada o aprobada, el acta ya está en el presupuesto de gastos y su monto
    se cuenta como `asignado`. `excluir_acta` deja fuera el acta que se está
    editando: si no, su propio monto se descontaría del saldo que se le muestra
    al técnico.
    """
    qs = (ProyectoPriorizado.objects
          .filter(acta__gestion=int(gestion))
          .exclude(acta__estado__in=[EstadosActa.VALIDADO,
                                     EstadosActa.APROBADO]))
    if excluir_acta:
        qs = qs.exclude(acta_id=excluir_acta)
    filas = (qs.values('fuente__codigo', 'organismo__codigo')
               .annotate(monto=Sum('monto')))
    return {_clave(f['fuente__codigo'], f['organismo__codigo']): float(f['monto'] or 0)
            for f in filas
            if f['fuente__codigo'] and f['organismo__codigo']}


def _identificadores():
    """El formulario necesita el id, no el código, para guardar el par."""
    fuentes, organismos = {}, {}
    for f in FuenteFinanciamiento.objects.all():
        fuentes.setdefault(f.codigo, (str(f.id), f.denominacion))
    for o in OrganismoFinanciador.objects.all():
        organismos.setdefault(o.codigo, (str(o.id), o.denominacion))
    return fuentes, organismos


def saldos(gestion, excluir_acta=None):
    """Una fila por par FF/OF con su techo, lo usado y lo que queda."""
    techos = techos_por_par(gestion)
    asignado = asignado_por_par(gestion)
    comprometido = comprometido_por_par(gestion, excluir_acta)

    # Un par puede tener gasto sin techo cargado: se muestra igual, en rojo,
    # porque esconderlo es esconder un sobregiro.
    for clave in set(asignado) | set(comprometido):
        techos.setdefault(clave, {
            'fuente': clave[0], 'organismo': clave[1],
            'fuente_denominacion': '', 'organismo_denominacion': '',
            'techo': 0.0,
        })

    fuentes, organismos = _identificadores()
    filas = []
    for clave, datos in techos.items():
        usado_gasto = asignado.get(clave, 0.0)
        usado_actas = comprometido.get(clave, 0.0)
        id_f, den_f = fuentes.get(datos['fuente'], ('', ''))
        id_o, den_o = organismos.get(datos['organismo'], ('', ''))
        filas.append({
            **datos,
            'fuente_id': id_f,
            'organismo_id': id_o,
            'fuente_denominacion': datos['fuente_denominacion'] or den_f,
            'organismo_denominacion': datos['organismo_denominacion'] or den_o,
            'par': f'{datos["fuente"]}/{datos["organismo"]}',
            'asignado': usado_gasto,
            'comprometido': usado_actas,
            'disponible': datos['techo'] - usado_gasto - usado_actas,
        })
    return sorted(filas, key=lambda f: (f['fuente'], f['organismo']))
