from collections import defaultdict

from django.db.models import Prefetch
from rest_framework import serializers

from apps.articulacion.models import (
    AccionPOA,
    AcuerdoInternacional,
    ArticulacionPADPEI,
    ProductoPAD,
    ResultadoPAD,
)
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

    def to_representation(self, instance):
        builder = self.context.get('matriz_builder')
        if builder is not None:
            return builder.serialize_node(
                instance,
                include_children=not self.context.get('matriz_lazy', False),
                lazy=self.context.get('matriz_lazy', False),
            )
        return super().to_representation(instance)

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
        result = []
        # ArticulacionPlanificacion: PGDESA → PDESA (también incluye sub-árbol PDESA)
        for a in ArticulacionPlanificacion.objects.filter(nodo_origen=obj).select_related('nodo_destino__plan'):
            dest = a.nodo_destino
            entry = {
                'tipo': 'articulacion_planificacion',
                'nodo_id': str(dest.id),
                'codigo_completo': self.get_codigo_completo(dest),
                'nombre': dest.nombre,
                'nivel': dest.nivel,
                'tipo_plan': dest.plan.tipo if dest.plan else None,
                'hijos': NodoArbolSerializer(
                    NodoPlanificacion.objects.filter(padre=dest).order_by('codigo'),
                    many=True, context=self.context
                ).data,
            }
            result.append(entry)

        # Bridge PDESA accion → ResultadoPAD
        if obj.plan and obj.plan.tipo == 'pdesa' and obj.nivel == 'accion':
            from apps.articulacion.models import ResultadoPAD as RP
            for rp in RP.objects.filter(nodo_pdesa=obj).select_related():
                entry = {
                    'tipo': 'bridge_pdesa_pad',
                    'codigo_resultado': rp.codigo_resultado,
                    'denominacion': rp.denominacion,
                    'lineamiento_pad': rp.lineamiento_pad,
                    'sector': rp.sector,
                    'ods': list(rp.acuerdo_ods.values_list('codigo', flat=True)),
                    'hijos': [],
                }
                # Incluir productos PAD como hijos
                for pp in rp.productos.all().order_by('codigo_producto'):
                    entry['hijos'].append({
                        'tipo': 'producto_pad',
                        'codigo_producto': pp.codigo_producto,
                        'denominacion': pp.denominacion,
                    })
                result.append(entry)
        return result


class MatrizArbolBuilder:
    """Build the complete matrix tree from one management snapshot.

    Main planning nodes, planning articulations, PAD bridges, PAD-PEI
    articulations and POA actions are loaded in batches.  The serializer then
    only traverses those in-memory maps, avoiding a query for every tree row.
    """

    def __init__(self, nodes, gestion, request=None):
        self.gestion = gestion
        self.request = request
        self.nodes = list(nodes)
        self.nodes_by_id = {node.id: node for node in self.nodes}
        self.children_by_parent = defaultdict(list)
        for node in self.nodes:
            self.children_by_parent[node.padre_id].append(node)
        for children in self.children_by_parent.values():
            children.sort(key=lambda node: (node.codigo, node.orden, str(node.id)))

        node_ids = list(self.nodes_by_id)
        self.links_by_origin = defaultdict(list)
        links = ArticulacionPlanificacion.objects.filter(
            gestion=gestion,
            nodo_origen_id__in=node_ids,
            nodo_destino_id__in=node_ids,
        ).select_related('nodo_destino', 'nodo_destino__plan')
        for link in links:
            self.links_by_origin[link.nodo_origen_id].append(link)

        action_ids = [
            node.id for node in self.nodes
            if node.plan and node.plan.tipo == 'pdesa' and node.nivel == 'accion'
        ]
        self.pads_by_node = defaultdict(list)
        pads = list(
            ResultadoPAD.objects.filter(
                nodo_pdesa_id__in=action_ids,
                vigencia_desde__lte=gestion,
                vigencia_hasta__gte=gestion,
            )
            .select_related('nodo_pdesa')
            .prefetch_related(
                Prefetch(
                    'acuerdo_ods',
                    queryset=AcuerdoInternacional.objects.filter(tipo_acuerdo='ODS'),
                    to_attr='matriz_ods',
                )
            )
        )
        for pad in pads:
            self.pads_by_node[pad.nodo_pdesa_id].append(pad)

        pad_ids = [pad.id for pad in pads]
        self.products_by_pad = defaultdict(list)
        products = list(
            ProductoPAD.objects.filter(resultado_pad_id__in=pad_ids)
            .order_by('resultado_pad_id', 'codigo_producto')
        )
        for product in products:
            self.products_by_pad[product.resultado_pad_id].append(product)

        product_ids = [product.id for product in products]
        self.articulations_by_product = defaultdict(list)
        articulations = list(
            ArticulacionPADPEI.objects.filter(
                producto_pad_id__in=product_ids,
                producto_pei__resultado_pei__vigencia_desde__lte=gestion,
                producto_pei__resultado_pei__vigencia_hasta__gte=gestion,
            )
            .select_related('producto_pei', 'producto_pei__resultado_pei')
            .order_by('producto_pad_id', 'producto_pei__codigo_producto')
        )
        for articulation in articulations:
            self.articulations_by_product[articulation.producto_pad_id].append(
                articulation
            )

        pei_ids = [articulation.producto_pei_id for articulation in articulations]
        self.actions_by_pei = defaultdict(list)
        actions = AccionPOA.objects.filter(
            producto_pei_id__in=pei_ids,
            gestion=gestion,
        ).order_by('producto_pei_id', 'codigo_accion')
        for action in actions:
            self.actions_by_pei[action.producto_pei_id].append(action)

        self._complete_code_cache = {}

    def _complete_code(self, node):
        if node.id in self._complete_code_cache:
            return self._complete_code_cache[node.id]

        codes = []
        current = node
        visited = set()
        while current is not None and current.id not in visited:
            visited.add(current.id)
            codes.append(current.codigo)
            current = self.nodes_by_id.get(current.padre_id)
        complete_code = ''
        for code in reversed([code for code in codes if code]):
            if not complete_code:
                complete_code = code
            elif code.startswith(f'{complete_code}.'):
                complete_code = code
            elif code != complete_code:
                complete_code = f'{complete_code}.{code}'
        self._complete_code_cache[node.id] = complete_code
        return complete_code

    def _node_fields(self, node):
        return {
            'id': str(node.id),
            'codigo': node.codigo,
            'codigo_completo': self._complete_code(node),
            'nombre': node.nombre,
            'nivel': node.nivel,
            'tipo_plan': node.plan.tipo if node.plan else None,
            'plan_nombre': node.plan.nombre if node.plan else None,
        }

    def _children_url(self, node):
        if self.request is None:
            return None
        return f'{self.request.path}?gestion={self.gestion}&padre_id={node.id}'

    def serialize_node(self, node, include_children=True, path=(), lazy=False):
        node_data = self._node_fields(node)
        if node.id in path:
            node_data['hijos'] = []
            node_data['articulaciones'] = []
            return node_data

        node_path = path + (node.id,)

        if include_children and node.id not in path:
            node_data['hijos'] = [
                self.serialize_node(child, include_children=True, path=node_path)
                for child in self.children_by_parent.get(node.id, [])
            ]
        else:
            node_data['hijos'] = []

        node_data['articulaciones'] = self._serialize_articulations(node, node_path)
        if lazy:
            node_data['children_url'] = self._children_url(node)
        return node_data

    def _serialize_articulations(self, node, path):
        result = []
        for articulation in self.links_by_origin.get(node.id, []):
            destination = self.nodes_by_id.get(articulation.nodo_destino_id)
            if destination is None:
                continue
            destination_data = self.serialize_node(
                destination,
                include_children=True,
                path=path,
            )
            result.append({
                'tipo': 'articulacion_planificacion',
                'nodo_id': str(destination.id),
                'codigo': destination_data['codigo'],
                'codigo_completo': destination_data['codigo_completo'],
                'nombre': destination_data['nombre'],
                'nivel': destination_data['nivel'],
                'tipo_plan': destination_data['tipo_plan'],
                'plan_nombre': destination_data['plan_nombre'],
                'gestion': articulation.gestion,
                'hijos': destination_data['hijos'],
                'articulaciones': destination_data['articulaciones'],
            })

        if node.plan and node.plan.tipo == 'pdesa' and node.nivel == 'accion':
            for resultado in self.pads_by_node.get(node.id, []):
                result.append(self._serialize_pad_bridge(resultado))
        return result

    def _serialize_pad_bridge(self, resultado):
        return {
            'tipo': 'bridge_pdesa_pad',
            'resultado_pad_id': str(resultado.id),
            'codigo_resultado': resultado.codigo_resultado,
            'denominacion': resultado.denominacion,
            'lineamiento_pad': resultado.lineamiento_pad,
            'sector': resultado.sector,
            'ods': [ods.codigo for ods in getattr(resultado, 'matriz_ods', [])],
            'hijos': [
                self._serialize_producto_pad(product)
                for product in self.products_by_pad.get(resultado.id, [])
            ],
        }

    def _serialize_producto_pad(self, product):
        articulations = self.articulations_by_product.get(product.id, [])
        pei_nodes = [
            self._serialize_producto_pei(articulation.producto_pei)
            for articulation in articulations
        ]
        return {
            'tipo': 'producto_pad',
            'id': str(product.id),
            'producto_pad_id': str(product.id),
            'nivel': 'pad',
            'codigo_producto': product.codigo_producto,
            'denominacion': product.denominacion,
            'nombre': product.denominacion,
            'articulaciones': [
                self._serialize_pad_pei_articulation(articulation)
                for articulation in articulations
            ],
            'hijos': pei_nodes,
        }

    def _serialize_pad_pei_articulation(self, articulation):
        producto_pei = articulation.producto_pei
        resultado_pei = producto_pei.resultado_pei
        return {
            'tipo': 'articulacion_pad_pei',
            'id': str(articulation.id),
            'articulacion_id': str(articulation.id),
            'producto_pad_id': str(articulation.producto_pad_id),
            'producto_pei_id': str(producto_pei.id),
            'codigo_producto_pei': producto_pei.codigo_producto,
            'denominacion_producto_pei': producto_pei.denominacion,
            'resultado_pei_id': str(resultado_pei.id),
            'codigo_resultado_pei': resultado_pei.codigo_resultado,
            'denominacion_resultado_pei': resultado_pei.denominacion,
            'hijos': [],
        }

    def _serialize_producto_pei(self, producto_pei):
        resultado_pei = producto_pei.resultado_pei
        resultado_node = {
            'tipo': 'resultado_pei',
            'id': str(resultado_pei.id),
            'resultado_pei_id': str(resultado_pei.id),
            'nivel': 'resultado_pei',
            'codigo_resultado': resultado_pei.codigo_resultado,
            'denominacion': resultado_pei.denominacion,
            'nombre': resultado_pei.denominacion,
            'hijos': [
                self._serialize_accion_poa(action)
                for action in self.actions_by_pei.get(producto_pei.id, [])
            ],
        }
        return {
            'tipo': 'producto_pei',
            'id': str(producto_pei.id),
            'producto_pei_id': str(producto_pei.id),
            'nivel': 'pei',
            'codigo_producto': producto_pei.codigo_producto,
            'codigo_producto_pei': producto_pei.codigo_producto,
            'denominacion': producto_pei.denominacion,
            'nombre': producto_pei.denominacion,
            'resultado_pei_id': str(resultado_pei.id),
            'hijos': [resultado_node],
        }

    @staticmethod
    def _serialize_accion_poa(action):
        return {
            'tipo': 'accion_poa',
            'id': str(action.id),
            'accion_poa_id': str(action.id),
            'nivel': 'poa',
            'codigo_accion': action.codigo_accion,
            'denominacion': action.denominacion,
            'nombre': action.denominacion,
            'producto_pei_id': str(action.producto_pei_id),
            'gestion': action.gestion,
            'hijos': [],
            'articulaciones': [],
        }
