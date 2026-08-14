"""Serializers de la API V2 del ciclo presupuestario SIS-POA (Fase 1)."""
from django.db import IntegrityError
from rest_framework import serializers

from apps.gestion.models import GestionFiscal

from .services import heredar_configuracion


class FiscalYearSerializer(serializers.ModelSerializer):
    """Gestión fiscal del ciclo presupuestario (`apps.gestion.GestionFiscal`)."""

    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    gestion_anterior = serializers.SerializerMethodField()
    heredar_de = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text='Año de la gestión de la cual heredar la configuración '
                  '(ciclos de formulación). Solo al crear.',
    )

    class Meta:
        model = GestionFiscal
        fields = [
            'id', 'anio', 'estado', 'estado_display', 'descripcion',
            'anio_inicio_plurianual', 'anio_fin_plurianual',
            'fecha_apertura', 'fecha_cierre', 'activa',
            'gestion_anterior', 'heredar_de', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = [
            'id', 'estado', 'estado_display', 'fecha_apertura',
            'fecha_cierre', 'gestion_anterior', 'creado_en', 'actualizado_en',
        ]

    def get_gestion_anterior(self, obj):
        anterior = (
            GestionFiscal.objects.filter(anio__lt=obj.anio)
            .order_by('-anio').first()
        )
        return anterior.anio if anterior else None

    def create(self, validated_data):
        heredar_de = validated_data.pop('heredar_de', None)
        origen = None
        if heredar_de is not None:
            origen = GestionFiscal.objects.filter(anio=heredar_de).first()
            if origen is None:
                raise serializers.ValidationError({
                    'heredar_de': f'No existe una gestión para el año {heredar_de}.',
                })

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['creado_por'] = request.user

        gestion = GestionFiscal(**validated_data)
        try:
            gestion.save()
        except IntegrityError:
            raise serializers.ValidationError({
                'anio': f'Ya existe una gestión para el año {validated_data["anio"]}.',
            })

        if origen is not None:
            heredar_configuracion(gestion, origen)
        return gestion
