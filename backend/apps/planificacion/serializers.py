from rest_framework import serializers
from .models import (
    Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo,
    ArticulacionPlanificacion, PlanVersion
)


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'


class NodoPlanificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodoPlanificacion
        fields = '__all__'


class AccionMedianoPlazoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionMedianoPlazo
        fields = '__all__'


class AccionCortoPlazoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionCortoPlazo
        fields = '__all__'


class ArticulacionPlanificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulacionPlanificacion
        fields = '__all__'


class PlanVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanVersion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NodoArbolSerializer(serializers.ModelSerializer):
    codigo_completo = serializers.SerializerMethodField()
    tipo_plan = serializers.SerializerMethodField()
    plan_nombre = serializers.CharField(source='plan.nombre')
    hijos = serializers.SerializerMethodField()
    articulaciones = serializers.SerializerMethodField()

    class Meta:
        model = NodoPlanificacion
        fields = ['id', 'codigo', 'codigo_completo', 'nombre', 'nivel',
                  'tipo_plan', 'plan_nombre', 'hijos', 'articulaciones']

    def get_codigo_completo(self, obj):
        codes = []
        node = obj
        while node:
            codes.append(node.codigo)
            node = node.padre
        return '.'.join(reversed(codes))

    def get_tipo_plan(self, obj):
        return obj.plan.tipo if obj.plan else None

    def get_hijos(self, obj):
        hijos = NodoPlanificacion.objects.filter(padre=obj).order_by('codigo')
        return NodoArbolSerializer(hijos, many=True, context=self.context).data

    def get_articulaciones(self, obj):
        gestion = self.context.get('gestion')
        arts = ArticulacionPlanificacion.objects.filter(
            nodo_origen=obj
        ).select_related('nodo_destino')
        result = []
        for a in arts:
            result.append({
                'tipo': 'articulacion_planificacion',
                'nodo_id': str(a.nodo_destino.id),
                'codigo_completo': self.get_codigo_completo(a.nodo_destino),
                'nombre': a.nodo_destino.nombre,
                'nivel': a.nodo_destino.nivel,
                'tipo_plan': a.nodo_destino.plan.tipo if a.nodo_destino.plan else None,
            })
        if obj.plan and obj.plan.tipo == 'pdesa' and obj.nivel == 'accion':
            from apps.articulacion.models import ResultadoPAD
            for rp in ResultadoPAD.objects.filter(nodo_pdesa=obj).select_related('lineamiento_pad'):
                result.append({
                    'tipo': 'bridge_pdesa_pad',
                    'resultado_pad_id': str(rp.id),
                    'codigo_resultado': rp.codigo_resultado,
                    'denominacion': rp.denominacion,
                })
        return result
