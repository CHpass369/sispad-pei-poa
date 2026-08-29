from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from .models import (
    ActaPriorizacion,
    EstadosActa,
    ProyectoCatalogo,
    ProyectoPriorizado,
)


class ProyectoCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoCatalogo
        fields = [
            'id',
            'nombre',
            'sisin',
            'categoria_programatica',
            'denominacion_categoria',
            'origen',
            'veces_priorizado',
        ]


class ProyectoPriorizadoSerializer(serializers.ModelSerializer):
    par_financiamiento = serializers.CharField(read_only=True)

    fuente_codigo = serializers.CharField(
        source='fuente.codigo',
        read_only=True,
    )

    organismo_codigo = serializers.CharField(
        source='organismo.codigo',
        read_only=True,
    )

    class Meta:
        model = ProyectoPriorizado
        fields = [
            'id',
            'orden',
            'nombre',
            'catalogo',
            'sisin',
            'categoria_programatica',
            'denominacion_categoria',
            'monto',
            'fuente',
            'organismo',
            'fuente_codigo',
            'organismo_codigo',
            'par_financiamiento',
            'monto_materializado',
        ]

        read_only_fields = [
            'monto_materializado',
        ]


class ActaPriorizacionSerializer(serializers.ModelSerializer):
    proyectos = ProyectoPriorizadoSerializer(
        many=True,
        required=False,
    )

    distrito_nombre = serializers.CharField(
        source='distrito.nombre',
        read_only=True,
    )

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True,
    )

    monto_total = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )

    esta_completa = serializers.BooleanField(
        read_only=True,
    )

    fecha_hora_registro = serializers.DateTimeField(
        source='created_at',
        read_only=True,
    )

    class Meta:
        model = ActaPriorizacion

        fields = [
            'id',
            'gestion',
            'numero',
            'distrito',
            'distrito_nombre',
            'otb',
            'unidad_territorial',
            'presidente',
            'responsable_registro',
            'fecha',
            'fecha_hora_registro',
            'es_pavimento',
            'estado',
            'estado_display',
            'observacion',
            'monto_total',
            'esta_completa',
            'proyectos',
        ]

        read_only_fields = [
            'fecha',
            'estado',
            'observacion',
        ]

    def create(self, validated_data):
        proyectos = validated_data.pop(
            'proyectos',
            [],
        )

        # La fecha la fija el servidor.
        acta = ActaPriorizacion.objects.create(
            fecha=timezone.localdate(),
            **validated_data,
        )

        self._guardar_proyectos(
            acta,
            proyectos,
        )

        acta_id = acta.id

        # Solo se sincroniza con Google si PostgreSQL
        # terminó correctamente la transacción.
        transaction.on_commit(
            lambda acta_id=acta_id:
            self._sincronizar_google(acta_id)
        )

        return acta

    def update(self, instance, validated_data):
        from .materializacion import desmaterializar_acta

        proyectos = validated_data.pop(
            'proyectos',
            None,
        )

        # Actualizar campos del acta.
        for campo, valor in validated_data.items():
            setattr(
                instance,
                campo,
                valor,
            )

        if proyectos is not None:
            # Si el acta ya estaba materializada en presupuesto,
            # primero se revierte.
            revertidos = desmaterializar_acta(
                instance
            )

            if (
                revertidos
                and instance.estado
                == EstadosActa.VALIDADO
            ):
                instance.estado = (
                    EstadosActa.BORRADOR
                )

        instance.save()

        if proyectos is not None:
            # El formulario reemplaza la lista completa.
            instance.proyectos.all().delete()

            self._guardar_proyectos(
                instance,
                proyectos,
            )

        acta_id = instance.id

        # Sincronizar Google después del commit.
        transaction.on_commit(
            lambda acta_id=acta_id:
            self._sincronizar_google(acta_id)
        )

        return instance

    def _sincronizar_google(self, acta_id):
        """
        Envía los proyectos del acta a:

        PROYECTOS 2027
        -> BASE DE DATOS FICHAS 2026

        Si Google falla, el error se registra,
        pero el guardado del PIP no se pierde.
        """
        from .services.google_sheets import (
            sincronizar_acta_google,
        )

        sincronizar_acta_google(
            acta_id
        )

    def _guardar_proyectos(
        self,
        acta,
        proyectos,
    ):
        for orden, datos in enumerate(
            proyectos,
            start=1,
        ):
            # El orden siempre lo controla el servidor.
            datos.pop(
                'orden',
                None,
            )

            ProyectoPriorizado.objects.create(
                acta=acta,
                orden=orden,
                **datos,
            )
