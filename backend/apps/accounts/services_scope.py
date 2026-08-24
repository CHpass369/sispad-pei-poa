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
- Un alcance con `fiscal_year` NULL aplica a toda gestión: al filtrar por
  `gestion_id` se incluyen los alcances de esa gestión y los sin gestión.
  Mantiene operativos los alcances pre-F1.5 (que no tenían gestión).
- Los superusuarios NO reciben GLOBAL implícito: el scope es siempre
  explícito vía `AlcanceOrganizacional`. Los roles admin que lo requieran
  deben sembrar un alcance GLOBAL (relevante para F2b).
- Sin caché: no hay evidencia medida de problema de performance (regla F2a).
"""
import uuid

from django.db.models import Q

from apps.accounts.models import AlcanceOrganizacional
from apps.organizacion.models import UnidadOrganizacional

GLOBAL_SCOPE = '__GLOBAL__'


class ScopeResolver:
    """Resuelve las UOs efectivas donde un usuario puede operar."""

    @staticmethod
    def alcances_vigentes(usuario, gestion_id=None):
        """Alcances activos del usuario.

        Si `gestion_id` se pasa, filtra por `fiscal_year_id`; los alcances
        sin gestión (`fiscal_year` NULL) aplican a toda gestión y se
        incluyen. La UNION es inherente: todos los alcances del usuario
        (vengan del rol que vengan) se consideran juntos.

        Un usuario inactivo o no autenticado no tiene alcances vigentes.
        """
        if not usuario or not getattr(usuario, 'is_authenticated', False):
            return AlcanceOrganizacional.objects.none()
        if not getattr(usuario, 'activo', False):
            return AlcanceOrganizacional.objects.none()
        qs = AlcanceOrganizacional.objects.filter(usuario=usuario, activo=True)
        if gestion_id is not None:
            qs = qs.filter(
                Q(fiscal_year_id=gestion_id) | Q(fiscal_year__isnull=True)
            )
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
