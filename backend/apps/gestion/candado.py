"""Candado de gestión fiscal de SIS-POA (ADR-007 §2-§3).

Una sola gestión está habilitada a la vez —`GestionFiscal.activa`, respaldado
por el índice único parcial `unica_gestion_habilitada`— y todos los módulos de
SIS-POA operan sobre ella. Ningún módulo elige el año: lo absorbe de acá.

El candado es DURO: fuera de la gestión habilitada no se lee ni se escribe.

**No aplica fuera de SIS-POA.** El SIS-PE (PAD, PEI) es quinquenal (2026-2030)
y sus años son horizontes de plan, no gestiones fiscales operativas; la
excepción plurianual está documentada en `docs/architecture/GESTION_FISCAL_AUDIT.md` §6.
Por eso los mixins de este módulo se aplican viewset por viewset y nunca de
forma global.

La resolución es por dato (la gestión que alguien habilitó explícitamente),
nunca por reloj: ADR-007 §3 prohíbe inferir la gestión de `now()`.
"""
from django.core.exceptions import ValidationError

from .models import GestionFiscal

# Códigos de error estables que el frontend distingue (el interceptor los
# propaga tal cual para poder mostrar el mensaje correcto).
CODIGO_SIN_GESTION = 'gestion_no_habilitada'
CODIGO_FUERA_DE_GESTION = 'fuera_de_gestion_habilitada'

# Estados que cuentan como "habilitada". Conviven los dos vocabularios del
# mismo campo: el del ciclo presupuestario y el legacy (`models.py:25-32`).
ESTADOS_HABILITADOS = ('HABILITADA', GestionFiscal.Estado.ABIERTA)


class FueraDeGestionHabilitada(ValidationError):
    """Se intentó operar sobre una gestión que no es la habilitada."""

    def __init__(self, mensaje, codigo=CODIGO_FUERA_DE_GESTION):
        super().__init__(mensaje, code=codigo)
        self.codigo = codigo


def esta_habilitada(gestion):
    """¿El *estado* de esta gestión es de habilitación?

    Mira el estado, no el candado. `apps.budget.services.gestion_habilitada`
    delega acá y sus tests dependen de esta semántica.
    """
    return gestion.estado in ESTADOS_HABILITADOS


def gestion_habilitada():
    """La gestión que tiene el candado, o ``None`` si no hay ninguna."""
    return GestionFiscal.objects.filter(activa=True).first()


def anio_habilitado():
    """El año de la gestión habilitada, o ``None``."""
    gestion = gestion_habilitada()
    return gestion.anio if gestion else None


def exigir_gestion_habilitada():
    """La gestión habilitada; lanza si no hay ninguna."""
    gestion = gestion_habilitada()
    if gestion is None:
        raise FueraDeGestionHabilitada(
            'No hay ninguna gestión fiscal habilitada. Habilite una gestión '
            'antes de planificar o programar en SIS-POA.',
            codigo=CODIGO_SIN_GESTION,
        )
    return gestion


def _anio_de(gestion_o_anio):
    """Normaliza gestión, año (int/texto) o UUID de gestión a un entero.

    Los tres formatos conviven de verdad: la campaña FK PIP-DB-005/006/007
    sigue abierta, así que unas tablas guardan la FK (y el cliente manda el
    UUID) y otras el año suelto. `apps/budget/views.py:1913` ya tenía que
    distinguirlos a mano.
    """
    if isinstance(gestion_o_anio, GestionFiscal):
        return gestion_o_anio.anio
    if gestion_o_anio in (None, ''):
        return None
    texto = str(gestion_o_anio)
    if texto.isdigit():
        return int(texto)
    try:
        anio = (
            GestionFiscal.objects
            .filter(pk=texto)
            .values_list('anio', flat=True)
            .first()
        )
    except (ValueError, ValidationError):
        # Ni año ni UUID: el pk es UUIDField y rechaza cualquier otra cosa.
        anio = None
    if anio is None:
        raise FueraDeGestionHabilitada(
            f'«{texto}» no identifica ninguna gestión fiscal.'
        )
    return anio


def validar_gestion(gestion_o_anio):
    """Exige que el objetivo sea la gestión habilitada. Devuelve la gestión.

    ``None`` significa "la habilitada" y pasa: es el caso de un cliente que no
    manda `?gestion=` y absorbe la del candado.
    """
    habilitada = exigir_gestion_habilitada()
    anio = _anio_de(gestion_o_anio)
    if anio is not None and anio != habilitada.anio:
        raise FueraDeGestionHabilitada(
            f'La gestión {anio} no es la gestión habilitada '
            f'({habilitada.anio}); SIS-POA solo opera sobre la habilitada.'
        )
    return habilitada


def resolver_gestion(request):
    """La gestión sobre la que responde un request de SIS-POA.

    Si el request trae `?gestion=`, tiene que coincidir con la habilitada; si
    no la trae, se absorbe la habilitada. Nunca devuelve "todas las gestiones":
    ese era justamente el agujero del `if gestion:` disperso por los viewsets.
    """
    return validar_gestion(request.query_params.get('gestion'))
