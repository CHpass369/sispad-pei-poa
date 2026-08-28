"""Resolución de alcance organizacional (F2a / ADR-003).

`ScopeResolver` traduce los `AlcanceOrganizacional` de un usuario al conjunto
de unidades organizacionales efectivas donde puede operar, aplicando
`scope_type`:

- `SELF`: solo la UO del alcance.
- `DESCENDANTS`: la UO y sus descendientes (BFS sobre
  `UnidadOrganizacional.padre`).
- `GLOBAL`: wildcard, representado por el sentinel `GLOBAL_SCOPE`.

Decisiones documentadas:

- Sin alcances vigentes NO hay GLOBAL implícito: `unidades_efectivas`
  devuelve un set vacío y `puede_operar` deniega.
- Los alcances SIS-PE pueden ser transversales (`fiscal_year` NULL). Un filtro
  explícito por `gestion_id` es SIS-POA y solo admite esa gestión.
- Los superusuarios NO reciben GLOBAL implícito: el scope es siempre
  explícito vía `AlcanceOrganizacional`. Los roles admin que lo requieran
  deben sembrar un alcance GLOBAL (relevante para F2b).
- Sin caché: no hay evidencia medida de problema de performance (regla F2a).
"""
import uuid

from django.db.models import Q

from apps.accounts.models import AlcanceOrganizacional, Capacidad
from apps.organizacion.models import UnidadOrganizacional

GLOBAL_SCOPE = '__GLOBAL__'


def evaluar_acceso_efectivo(
    usuario, asignaciones=None, roles_reemplazables=(),
):
    """Evaluate persisted or hypothetical access without writing assignments."""
    from apps.accounts.permissions import listar_capacidades

    if asignaciones is None:
        codigos = listar_capacidades(usuario)
        alcances = ScopeResolver.alcances_vigentes(usuario)
    else:
        reemplazables = set(roles_reemplazables)
        roles = list(usuario.roles.filter(activo=True).exclude(pk__in=reemplazables))
        roles.extend(item['rol'] for item in asignaciones)
        codigos = listar_capacidades(usuario, roles=roles)
        alcances = list(
            ScopeResolver.alcances_vigentes(usuario).exclude(
                rol_id__in=reemplazables,
            )
        ) + asignaciones

    capacidades = list(
        Capacidad.objects.filter(codigo__in=codigos, activo=True)
        .exclude(Q(codigo__istartswith='sis_pro.') | Q(
            codigo__istartswith='sis-pro.',
        ))
        .order_by('codigo')
    )
    unidades = set()
    for alcance in alcances:
        if isinstance(alcance, dict):
            scope_type = alcance['scope_type']
            unidad = alcance['unidad']
            fiscal_year = alcance['fiscal_year']
        else:
            scope_type = alcance.scope_type
            unidad = alcance.unidad
            fiscal_year = alcance.fiscal_year
        if scope_type == AlcanceOrganizacional.SCOPE_GLOBAL:
            globales = UnidadOrganizacional.objects.filter(activo=True)
            if fiscal_year is not None:
                globales = globales.filter(gestion=fiscal_year)
            unidades.update(globales.values_list('pk', flat=True))
        elif scope_type == AlcanceOrganizacional.SCOPE_DESCENDANTS:
            unidades.update(ScopeResolver._descendants(unidad.pk))
        else:
            unidades.add(unidad.pk)

    unidades = UnidadOrganizacional.objects.filter(pk__in=unidades).order_by(
        'codigo', 'pk',
    )
    modulos = sorted({
        (capacidad.codigo.split('.')[0], capacidad.codigo.split('.')[1])
        for capacidad in capacidades if capacidad.codigo.count('.') >= 2
    })
    return {
        'capabilities': capacidades,
        'effective_uos': unidades,
        'modules': [
            {'sistema': sistema, 'codigo': modulo, 'visible': True}
            for sistema, modulo in modulos
        ],
    }


class ScopeResolver:
    """Resuelve las UOs efectivas donde un usuario puede operar."""

    @staticmethod
    def alcances_vigentes(usuario, gestion_id=None):
        """Alcances activos del usuario.

        Si `gestion_id` se pasa, filtra estrictamente por `fiscal_year_id`.
        La UNION es inherente: todos los alcances del usuario (vengan del rol
        que vengan) se consideran juntos.

        Un usuario inactivo o no autenticado no tiene alcances vigentes.
        """
        if not usuario or not getattr(usuario, 'is_authenticated', False):
            return AlcanceOrganizacional.objects.none()
        if not getattr(usuario, 'activo', False):
            return AlcanceOrganizacional.objects.none()
        qs = AlcanceOrganizacional.objects.filter(usuario=usuario, activo=True)
        if gestion_id is not None:
            qs = qs.filter(fiscal_year_id=gestion_id)
        return qs

    @staticmethod
    def unidades_efectivas(usuario, gestion_id=None):
        """Set de IDs de UO donde el usuario puede operar.

        UNION de todos los alcances vigentes. Un alcance GLOBAL hace
        cortocircuito y devuelve `{GLOBAL_SCOPE}`. Sin alcances vigentes
        devuelve set vacío (nunca GLOBAL implícito).
        """
        efectivas = set()
        for alcance in ScopeResolver.alcances_vigentes(usuario, gestion_id):
            if alcance.scope_type == AlcanceOrganizacional.SCOPE_GLOBAL:
                return {GLOBAL_SCOPE}
            if alcance.scope_type == AlcanceOrganizacional.SCOPE_DESCENDANTS:
                efectivas |= ScopeResolver._descendants(alcance.unidad_id)
            else:  # SELF (default)
                efectivas.add(alcance.unidad_id)
        return efectivas

    @staticmethod
    def puede_operar(usuario, unidad_id, gestion_id=None):
        """True si el usuario puede operar sobre la UO `unidad_id`.

        `unidad_id` puede ser UUID o str (los kwargs de URL llegan como str);
        un valor no parseable deniega (fail-closed).
        """
        if unidad_id is None:
            return False
        if isinstance(unidad_id, str):
            try:
                unidad_id = uuid.UUID(unidad_id)
            except ValueError:
                return False
        efectivas = ScopeResolver.unidades_efectivas(usuario, gestion_id)
        if GLOBAL_SCOPE in efectivas:
            return True
        return unidad_id in efectivas

    @staticmethod
    def _descendants(uo_id):
        """BFS sobre `UnidadOrganizacional.padre`; incluye la UO raíz.

        El set de visitados hace el recorrido inmune a ciclos de datos.
        Sin `lru_cache`: regla F2a, no hay benchmark que lo justifique.
        """
        visitados = {uo_id}
        frontera = [uo_id]
        while frontera:
            hijas = set(
                UnidadOrganizacional.objects.filter(padre_id__in=frontera)
                .values_list('id', flat=True)
            )
            nuevas = hijas - visitados
            if not nuevas:
                break
            visitados |= nuevas
            frontera = list(nuevas)
        return visitados
