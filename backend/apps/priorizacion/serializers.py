from rest_framework import serializers
from django.utils import timezone

from .models import (
    ActaPriorizacion, EstadosActa, ProyectoCatalogo, ProyectoPriorizado,
)


class ProyectoCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProyectoCatalogo
        fields = ['id', 'nombre', 'sisin', 'categoria_programatica',
                  'denominacion_categoria', 'origen', 'veces_priorizado']


class ProyectoPriorizadoSerializer(serializers.ModelSerializer):
    par_financiamiento = serializers.CharField(read_only=True)
    fuente_codigo = serializers.CharField(source='fuente.codigo', read_only=True)
    organismo_codigo = serializers.CharField(source='organismo.codigo',
                                             read_only=True)

    class Meta:
        model = ProyectoPriorizado
        fields = ['id', 'orden', 'nombre', 'catalogo', 'sisin',
                  'categoria_programatica', 'denominacion_categoria', 'monto',
                  'fuente', 'organismo', 'fuente_codigo', 'organismo_codigo',
                  'par_financiamiento', 'monto_materializado']
        read_only_fields = ['monto_materializado']


class ActaPriorizacionSerializer(serializers.ModelSerializer):
    proyectos = ProyectoPriorizadoSerializer(many=True, required=False)
    distrito_nombre = serializers.CharField(source='distrito.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    monto_total = serializers.DecimalField(max_digits=18, decimal_places=2,
                                           read_only=True)
    esta_completa = serializers.BooleanField(read_only=True)
    fecha_hora_registro = serializers.DateTimeField(
        source='created_at', read_only=True
    )

    class Meta:
        model = ActaPriorizacion
        fields = ['id', 'gestion', 'numero', 'distrito', 'distrito_nombre', 'otb',
                  'unidad_territorial', 'presidente', 'responsable_registro',
                  'fecha', 'fecha_hora_registro', 'es_pavimento', 'estado',
                  'estado_display', 'observacion',
                  'monto_total', 'esta_completa', 'proyectos']
        read_only_fields = ['fecha', 'estado', 'observacion']

    def create(self, validated_data):
        proyectos = validated_data.pop('proyectos', [])
        # La fecha la fija el servidor con la zona horaria oficial.
        # La hora exacta de registro queda almacenada en created_at.
        acta = ActaPriorizacion.objects.create(
            fecha=timezone.localdate(),
            **validated_data,
        )
        self._guardar_proyectos(acta, proyectos)
        return acta

    def update(self, instance, validated_data):
        from .materializacion import desmaterializar_acta

        proyectos = validated_data.pop('proyectos', None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)

        if proyectos is not None:
            # Lo ya volcado al gasto se libera ANTES de reemplazar la lista.
            # El rastro de cuánto puso cada proyecto vive en su propia fila, y
            # al borrarla se pierde: la plata quedaría en el presupuesto de
            # gastos sin que nada recuerde de dónde vino, y al volver a validar
            # se sumaría de nuevo.
            revertidos = desmaterializar_acta(instance)
            if revertidos and instance.estado == EstadosActa.VALIDADO:
                # Lo validado ya no es lo que dice el acta.
                instance.estado = EstadosActa.BORRADOR

        instance.save()

        if proyectos is not None:
            # El acta se edita como un todo: se reemplaza la lista completa en
            # vez de intentar casar altas, bajas y cambios de orden.
            instance.proyectos.all().delete()
            self._guardar_proyectos(instance, proyectos)
        return instance

    def _guardar_proyectos(self, acta, proyectos):
        for orden, datos in enumerate(proyectos, start=1):
            datos.pop('orden', None)
            ProyectoPriorizado.objects.create(acta=acta, orden=orden, **datos)
