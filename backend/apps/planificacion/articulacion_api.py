"""
API optimizada para la herramienta de articulación PDES → PTDI → PEI → POA.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch
from .models import NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo


class ArticulacionViewSet(viewsets.ViewSet):
    """Herramienta de articulación PDES → PTDI → PEI → POA."""

    @action(detail=False, methods=['get'])
    def pep(self, request):
        """
        Cadena de articulación PDES → PEI → POA con datos precargados.
        """
        # 1. Todas las acciones PDES
        acciones_pdes = NodoPlanificacion.objects.filter(nivel='accion_pdes')
        pdes_map = {}
        for ap in acciones_pdes:
            pdes_map[str(ap.id)] = {
                'id': str(ap.id),
                'codigo': ap.codigo,
                'nombre': ap.nombre,
                'pei': [],
            }

        # 2. TODAS las AMPs con su nodo_planificacion_id
        amps = AccionMedianoPlazo.objects.all().values(
            'id', 'codigo', 'nombre', 'nodo_planificacion_id'
        )
        amp_map = {}
        for amp in amps:
            nid = str(amp['nodo_planificacion_id']) if amp['nodo_planificacion_id'] else None
            amp_item = {
                'id': str(amp['id']),
                'codigo': amp['codigo'],
                'nombre': amp['nombre'],
                'poa': [],
            }
            amp_map[str(amp['id'])] = amp_item
            if nid and nid in pdes_map:
                pdes_map[nid]['pei'].append(amp_item)

        # 3. TODAS las ACPs por AMP
        acps = AccionCortoPlazo.objects.all().values(
            'id', 'codigo', 'nombre', 'gestion', 'accion_mediano_plazo_id'
        )
        for acp in acps:
            amp_id = str(acp['accion_mediano_plazo_id']) if acp['accion_mediano_plazo_id'] else None
            if amp_id and amp_id in amp_map:
                amp_map[amp_id]['poa'].append({
                    'id': str(acp['id']),
                    'codigo': acp['codigo'],
                    'nombre': acp['nombre'],
                    'gestion': acp['gestion'],
                })

        resultado = list(pdes_map.values())

        stats = {
            'acciones_pdes': len(resultado),
            'acciones_pei': sum(len(r['pei']) for r in resultado),
            'acciones_poa': sum(len(pei['poa']) for r in resultado for pei in r['pei']),
        }

        return Response({'total': len(resultado), 'data': resultado, 'stats': stats})

    @action(detail=False, methods=['post'])
    def vincular(self, request):
        """Vincula una Acción PEI (AMP) a un nodo PDES."""
        nodo_id = request.data.get('nodo_id')
        amp_id = request.data.get('amp_id')
        if not nodo_id or not amp_id:
            return Response({'error': 'nodo_id y amp_id requeridos'}, status=400)
        try:
            nodo = NodoPlanificacion.objects.get(id=nodo_id)
            amp = AccionMedianoPlazo.objects.get(id=amp_id)
            amp.nodo_planificacion = nodo
            amp.save()
            return Response({'status': 'vinculado'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
