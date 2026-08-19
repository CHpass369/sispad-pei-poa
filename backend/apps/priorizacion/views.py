"""API del módulo Priorización POA."""
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.articulacion.permissions import es_aprobador

from .models import (
    ActaPriorizacion, EstadosActa, PlantillaActa, ProyectoCatalogo, normalizar,
)
from .pdf import generar_acta_pdf, hash_acta
from .serializers import ActaPriorizacionSerializer, ProyectoCatalogoSerializer

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

UNIDADES = ['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete',
            'ocho', 'nueve', 'diez', 'once', 'doce', 'trece', 'catorce',
            'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve',
            'veinte', 'veintiuno', 'veintidós', 'veintitrés', 'veinticuatro',
            'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho',
            'veintinueve', 'treinta', 'treinta y uno']


def anio_en_letras(anio):
    """El acta escribe el año con palabras: "del año dos mil veinticinco"."""
    if not 2000 <= anio <= 2099:
        return str(anio)
    resto = anio - 2000
    if resto == 0:
        return 'dos mil'
    decenas = {30: 'treinta', 40: 'cuarenta', 50: 'cincuenta', 60: 'sesenta',
               70: 'setenta', 80: 'ochenta', 90: 'noventa'}
    if resto <= 31:
        return f'dos mil {UNIDADES[resto]}'
    decena, unidad = divmod(resto, 10)
    texto = decenas[decena * 10]
    return f'dos mil {texto}' + (f' y {UNIDADES[unidad]}' if unidad else '')


class ProyectoCatalogoViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo maestro que alimenta el buscador del nombre de proyecto.

    La búsqueda funciona como un buscador web: cada palabra escrita acota más el
    resultado. Se comparan contra el nombre normalizado, así que ni las tildes
    ni la puntuación cambian el resultado.
    """
    serializer_class = ProyectoCatalogoSerializer
    permission_classes = [IsAuthenticated]
    queryset = ProyectoCatalogo.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        consulta = normalizar(self.request.query_params.get('q', ''))
        for palabra in consulta.split():
            qs = qs.filter(nombre_busqueda__contains=palabra)
        if self.request.query_params.get('con_sisin') == '1':
            qs = qs.exclude(sisin='')
        # Lo más priorizado primero: es lo que el técnico va a elegir seguido.
        return qs.order_by('-veces_priorizado', 'nombre')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        limite = min(int(request.query_params.get('limite', 20)), 100)
        return Response({
            'total': qs.count(),
            'resultados': self.get_serializer(qs[:limite], many=True).data,
        })


class ActaPriorizacionViewSet(viewsets.ModelViewSet):
    """Actas de priorización, con su circuito de revisión."""
    serializer_class = ActaPriorizacionSerializer
    permission_classes = [IsAuthenticated]
    queryset = (ActaPriorizacion.objects
                .select_related('distrito')
                .prefetch_related('proyectos')
                .all())

    def get_queryset(self):
        qs = super().get_queryset()
        for campo in ('gestion', 'distrito', 'estado'):
            valor = self.request.query_params.get(campo)
            if valor:
                qs = qs.filter(**{campo: valor})
        buscar = self.request.query_params.get('q')
        if buscar:
            qs = qs.filter(Q(otb__icontains=buscar) |
                           Q(presidente__icontains=buscar))
        return qs

    # --- Circuito de revisión ----------------------------------------------

    def _transicion(self, acta, estado, observacion=''):
        acta.estado = estado
        acta.observacion = observacion
        acta.save(update_fields=['estado', 'observacion'])
        return Response({'estado': acta.estado, 'observacion': acta.observacion})

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        acta = self.get_object()
        if acta.estado == EstadosActa.APROBADO:
            return Response({'error': 'Un acta aprobada ya no admite cambios.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not acta.esta_completa:
            return Response(
                {'error': 'El acta necesita fecha y al menos un proyecto '
                          'priorizado para validarse.'},
                status=status.HTTP_400_BAD_REQUEST)
        return self._transicion(acta, EstadosActa.VALIDADO)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        if not es_aprobador(request.user):
            return Response({'error': 'Solo la jefatura puede aprobar actas.'},
                            status=status.HTTP_403_FORBIDDEN)
        acta = self.get_object()
        if acta.estado != EstadosActa.VALIDADO:
            return Response({'error': 'Solo se aprueba un acta validada.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._transicion(acta, EstadosActa.APROBADO)

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        if not es_aprobador(request.user):
            return Response({'error': 'Solo la jefatura puede observar actas.'},
                            status=status.HTTP_403_FORBIDDEN)
        comentario = str(request.data.get('comentario', '')).strip()
        if not comentario:
            return Response({'error': 'Se requiere un comentario para observar.'},
                            status=status.HTTP_400_BAD_REQUEST)
        acta = self.get_object()
        if acta.estado == EstadosActa.APROBADO:
            return Response({'error': 'Un acta aprobada ya no admite cambios.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._transicion(acta, EstadosActa.OBSERVADO, comentario)

    def destroy(self, request, *args, **kwargs):
        acta = self.get_object()
        if acta.estado == EstadosActa.APROBADO:
            return Response({'error': 'Un acta aprobada no se puede eliminar.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    # --- Acta oficial -------------------------------------------------------

    def _datos_acta(self, acta):
        """Los datos del acta ya resueltos, o un Response con el motivo."""
        if not acta.fecha:
            return Response(
                {'error': 'El acta no tiene fecha: no se puede emitir.'},
                status=status.HTTP_400_BAD_REQUEST)
        if not acta.proyectos.exists():
            return Response(
                {'error': 'El acta no tiene proyectos priorizados.'},
                status=status.HTTP_400_BAD_REQUEST)

        plantilla = (PlantillaActa.objects
                     .filter(activa=True)
                     .filter(Q(gestion=acta.gestion) | Q(gestion__isnull=True))
                     # La específica de la gestión gana sobre la general.
                     # `-gestion` a secas no sirve: en PostgreSQL los NULL van
                     # primero al ordenar descendente, y la general ganaría.
                     .order_by(F('gestion').desc(nulls_last=True))
                     .first())
        if plantilla is None:
            return Response(
                {'error': 'No hay plantilla de acta cargada. Ejecute '
                          'sembrar_plantilla_acta.'},
                status=status.HTTP_400_BAD_REQUEST)

        fecha = acta.fecha
        proyectos = list(acta.proyectos.all())
        total = sum((p.monto or 0) for p in proyectos)
        textos = plantilla.render({
            'presidente': acta.presidente, 'otb': acta.otb,
            'distrito': acta.distrito.nombre, 'dia': f'{fecha.day:02d}',
            'mes': MESES[fecha.month - 1],
            'anio_letras': anio_en_letras(fecha.year),
            'gestion': acta.gestion, 'total': f'{total:,.0f}',
        })
        valores = {'presidente': acta.presidente,
                   'responsable': acta.responsable_registro}
        return {
            **textos,
            'acta_id': str(acta.id),
            'gestion': acta.gestion,
            'distrito': acta.distrito.nombre,
            'otb': acta.otb,
            'presidente': acta.presidente,
            'fecha': acta.fecha.isoformat(),
            'proyectos': [{
                'nro': p.orden, 'descripcion': p.nombre,
                'monto': float(p.monto or 0),
                'sisin': p.sisin,
                'categoria_programatica': p.categoria_programatica,
            } for p in proyectos],
            'total': float(total),
            'firmas': [{'rol': f.get('rol', ''),
                        'nombre': valores.get(f.get('campo', ''), '')}
                       for f in (plantilla.firmas or [])],
        }

    @action(detail=True, methods=['get'], url_path='acta-oficial')
    def acta_oficial(self, request, pk=None):
        """El acta lista para emitir, con los textos de la plantilla."""
        datos = self._datos_acta(self.get_object())
        if isinstance(datos, Response):
            return datos
        return Response({**datos, 'huella': hash_acta(datos)})

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        """El acta en PDF tamaño oficio, armada en el servidor.

        No se delega en la impresión del navegador: el diálogo nativo usa el
        tamaño de papel que tenga configurado el usuario y escala la hoja.
        """
        acta = self.get_object()
        datos = self._datos_acta(acta)
        if isinstance(datos, Response):
            return datos
        contenido, huella = generar_acta_pdf(datos)
        nombre = f'acta-{acta.distrito.codigo}-{acta.otb[:40]}-{acta.gestion}.pdf'
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="{nombre.replace(chr(32), "-")}"')
        respuesta['X-Acta-Huella'] = huella
        return respuesta


class MatrizPriorizacionViewSet(viewsets.ViewSet):
    """Matrices acumulativas: lo priorizado, consolidado por distrito."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        gestion = request.query_params.get('gestion')
        actas = ActaPriorizacion.objects.select_related('distrito')
        if gestion:
            actas = actas.filter(gestion=int(gestion))

        # Los alias no pueden llamarse como la relación: `proyectos=Count(...)`
        # pisa el nombre y rompe el Sum('proyectos__monto') de al lado.
        distritos = (actas
                     .values('distrito__id', 'distrito__codigo', 'distrito__nombre')
                     .annotate(cuenta_actas=Count('id', distinct=True),
                               suma_monto=Sum('proyectos__monto'))
                     .order_by('distrito__codigo'))

        filas = []
        for acta in actas.prefetch_related('proyectos').order_by(
                'distrito__codigo', 'otb'):
            for p in acta.proyectos.all():
                filas.append({
                    'distrito': acta.distrito.nombre,
                    'otb': acta.otb,
                    'presidente': acta.presidente,
                    'fecha': acta.fecha.isoformat() if acta.fecha else '',
                    'estado': acta.estado,
                    'orden': p.orden,
                    'proyecto': p.nombre,
                    'sisin': p.sisin,
                    'categoria_programatica': p.categoria_programatica,
                    'monto': float(p.monto or 0),
                })

        return Response({
            'gestion': int(gestion) if gestion else None,
            'resumen': [{
                'distrito': d['distrito__nombre'],
                'codigo': d['distrito__codigo'],
                'actas': d['cuenta_actas'],
                # Contar la relación en el mismo annotate se infla con el join:
                # se recuenta sobre las filas ya armadas.
                'proyectos': sum(1 for f in filas
                                 if f['distrito'] == d['distrito__nombre']),
                'monto': float(d['suma_monto'] or 0),
            } for d in distritos],
            'total_filas': len(filas),
            'total_monto': sum(f['monto'] for f in filas),
            'filas': filas,
        })


class CategoriaProgramaticaViewSet(viewsets.ViewSet):
    """Catálogo de categorías programáticas para elegir en el acta.

    El endpoint de `budget` filtra la gestión por UUID y pagina de a 25; acá
    hace falta la lista completa y filtrada por año para un desplegable.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from apps.budget.models import CategoriaProgramaticaTecho

        qs = CategoriaProgramaticaTecho.objects.all()
        gestion = request.query_params.get('gestion')
        if gestion:
            por_anio = qs.filter(gestion__anio=int(gestion))
            # Una gestión sin catálogo propio usa el vigente.
            qs = por_anio if por_anio.exists() else qs
        nivel = request.query_params.get('nivel', 'ACTIVIDAD')
        if nivel:
            qs = qs.filter(nivel=nivel)
        return Response([
            {'codigo': c.codigo, 'denominacion': c.denominacion, 'nivel': c.nivel}
            for c in qs.order_by('codigo')
        ])
