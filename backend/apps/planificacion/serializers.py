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
        hijos = NodoPlanificacion.objects.filter(padre=obj)
        gestion = self.context.get('gestion')
        if gestion:
            hijos = hijos.filter(gestion=gestion)
        hijos = hijos.select_related('plan', 'padre').order_by('orden', 'codigo')
        return NodoArbolSerializer(hijos, many=True, context=self.context).data

    def get_articulaciones(self, obj):
        gestion = self.context.get('gestion')
        arts = ArticulacionPlanificacion.objects.filter(
            nodo_origen=obj
        ).select_related('nodo_destino__plan', 'nodo_destino__padre')
        if gestion:
            arts = arts.filter(gestion=gestion, nodo_destino__gestion=gestion)
        prefix = self.get_codigo_completo(obj)
        result = [
            self._plan_node(a.nodo_destino, prefix=prefix)
            for a in arts.order_by('nodo_destino__orden', 'nodo_destino__codigo')
        ]
        if obj.plan and obj.plan.tipo == 'pdesa' and obj.nivel == 'accion':
            result.extend(self._pad_links(obj))
        return result

    def _plan_node(self, node, *, prefix):
        code = f'{prefix}.{node.codigo}' if prefix else node.codigo
        children = [
            self._plan_node(child, prefix=code)
            for child in node.hijos.filter(
                gestion=self.context.get('gestion'),
            ).select_related('plan').order_by('orden', 'codigo')
        ]
        articulations = self._pad_links(node) if (
            node.plan.tipo == 'pdesa' and node.nivel == 'accion'
        ) else []
        return {
            'id': str(node.pk),
            'tipo': 'articulacion_planificacion',
            'codigo': node.codigo,
            'codigo_completo': code,
            'nombre': node.nombre,
            'nivel': node.nivel,
            'tipo_plan': node.plan.tipo,
            'plan_nombre': node.plan.nombre,
            'hijos': children,
            'articulaciones': articulations,
        }

    def _pad_links(self, node):
        from apps.articulacion.models import ResultadoPAD

        gestion = self.context.get('gestion')
        results = ResultadoPAD.objects.filter(nodo_pdesa=node)
        if gestion:
            results = results.filter(
                vigencia_desde__lte=gestion,
                vigencia_hasta__gte=gestion,
            )
        return [
            self._pad_result(result)
            for result in results.prefetch_related(
                'productos__articulaciones_pei__producto_pei__resultado_pei',
                'productos__articulaciones_pei__producto_pei__acciones_poa__operaciones__actividades__tareas',
            ).order_by('codigo_resultado')
        ]

    @staticmethod
    def _node(instance, *, code, name, level, children=None):
        return {
            'id': str(instance.pk),
            'codigo': code.rsplit('.', 1)[-1],
            'codigo_completo': code,
            'nombre': name,
            'nivel': level,
            'tipo_plan': level.split('_')[-1] if '_' in level else level,
            'hijos': children or [],
            'articulaciones': [],
        }

    def _pad_result(self, result):
        children = [self._pad_product(product) for product in result.productos.all()]
        return self._node(
            result,
            code=result.codigo_completo_articulacion,
            name=result.denominacion,
            level='resultado_pad',
            children=children,
        )

    def _pad_product(self, product):
        objectives = []
        for link in product.articulaciones_pei.all():
            pei_product = link.producto_pei
            pei_result = pei_product.resultado_pei
            prefix = product.codigo_completo_articulacion
            objective_code = '.'.join((
                prefix,
                pei_result.entidad_codificadora.codigo,
                pei_result.cod_oei.zfill(2),
            ))
            result_code = f'{objective_code}.{pei_result.segmento}'
            product_node = self._pei_product(pei_product)
            result_node = self._node(
                pei_result,
                code=result_code,
                name=pei_result.denominacion,
                level='resultado_pei',
                children=[product_node],
            )
            objectives.append({
                'id': f'objective-{pei_result.pk}',
                'codigo': pei_result.cod_oei.zfill(2),
                'codigo_completo': objective_code,
                'nombre': f'Objetivo institucional PEI {pei_result.cod_oei.zfill(2)}',
                'nivel': 'objetivo_pei',
                'tipo_plan': 'pei',
                'hijos': [result_node],
                'articulaciones': [],
            })
        return self._node(
            product,
            code=product.codigo_completo_articulacion,
            name=product.denominacion,
            level='producto_pad',
            children=objectives,
        )

    def _pei_product(self, product):
        actions = [
            self._poa_action(action)
            for action in product.acciones_poa.filter(
                gestion=self.context.get('gestion'),
            ).order_by('codigo_accion')
        ]
        return self._node(
            product,
            code=product.codigo_completo_articulacion,
            name=product.denominacion,
            level='producto_pei',
            children=actions,
        )

    def _poa_action(self, action):
        operations = [
            self._operation(operation)
            for operation in action.operaciones.all().order_by('codigo_operacion')
        ]
        return self._node(
            action,
            code=action.codigo_completo_articulacion,
            name=action.denominacion,
            level='accion_poa',
            children=operations,
        )

    def _operation(self, operation):
        activities = [
            self._activity(activity)
            for activity in operation.actividades.all().order_by('codigo_actividad')
        ]
        return self._node(
            operation,
            code=operation.codigo_completo_articulacion,
            name=operation.denominacion,
            level='operacion_poau',
            children=activities,
        )

    def _activity(self, activity):
        tasks = [
            self._node(
                task,
                code=task.codigo_completo_articulacion,
                name=task.denominacion,
                level='tarea_poau',
            )
            for task in activity.tareas.all().order_by('codigo_tarea')
        ]
        return self._node(
            activity,
            code=activity.codigo_completo_articulacion,
            name=activity.denominacion,
            level='actividad_poau',
            children=tasks,
        )
