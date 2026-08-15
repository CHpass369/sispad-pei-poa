"""Mixins reutilizables para serializers DRF de la plataforma PIP."""
from rest_framework import serializers

from apps.core.validators import validar_ejecucion_no_negativa


class EjecucionNoNegativaMixin:
    """Valida que el campo 'ejecutado' nunca sea negativo en create/update."""

    def validate(self, data):
        ejecutado = data.get('ejecutado', getattr(self.instance, 'ejecutado', None))
        resultado = validar_ejecucion_no_negativa(ejecutado)
        if not resultado['valido']:
            raise serializers.ValidationError({'ejecutado': resultado['mensaje']})
        return data
