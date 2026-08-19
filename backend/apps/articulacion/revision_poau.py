"""Circuito de revisión de los registros POAU.

Los tres niveles ejecutables —operación, actividad y tarea— se revisan uno por
uno: las unidades presentan su programación en momentos distintos y una tarea
aprobada no puede quedar rehén de otra que todavía se discute.

    BORRADOR ──validar──▶ VALIDADO ──aprobar──▶ APROBADO
        ▲                     │
        └──────observar───────┘  (vuelve como OBSERVADO, editable)

`validar` lo hace quien formula; `aprobar` y `observar`, la jefatura. Un
registro APROBADO deja de admitir cambios y no se puede borrar.
"""
from django.db import models
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


class EstadosPOAU(models.TextChoices):
    BORRADOR = 'BORRADOR', 'Borrador'
    VALIDADO = 'VALIDADO', 'Validado'
    OBSERVADO = 'OBSERVADO', 'Observado'
    APROBADO = 'APROBADO', 'Aprobado'


class RevisionPOAUMixin:
    """Agrega validar/aprobar/observar y protege lo aprobado."""

    def _denegar(self, mensaje):
        return Response({'error': mensaje}, status=status.HTTP_403_FORBIDDEN)

    def _rechazar(self, mensaje):
        return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)

    def _transicion(self, obj, estado, request, accion, detalle, **extra):
        from .services import registrar_auditoria

        obj.estado = estado
        campos = ['estado']
        if 'observacion' in extra:
            obj.observacion = extra['observacion']
            campos.append('observacion')
        obj.save(update_fields=campos)
        registrar_auditoria(
            usuario=request.user, accion=accion,
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle=detalle,
        )
        return Response({'estado': obj.estado, 'observacion': obj.observacion})

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        """Quien formula da por revisado el registro."""
        obj = self.get_object()
        if obj.estado == EstadosPOAU.APROBADO:
            return self._rechazar('Un registro aprobado ya no admite cambios.')
        if obj.estado == EstadosPOAU.VALIDADO:
            return self._rechazar('El registro ya está validado.')
        return self._transicion(obj, EstadosPOAU.VALIDADO, request, 'validar',
                                'Registro POAU validado', observacion='')

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """La jefatura cierra el registro."""
        from .permissions import es_aprobador
        if not es_aprobador(request.user):
            return self._denegar('Solo la jefatura puede aprobar registros POAU.')
        obj = self.get_object()
        if obj.estado != EstadosPOAU.VALIDADO:
            return self._rechazar(
                'Solo se aprueba un registro validado; este está '
                f'{obj.get_estado_display().lower()}.'
            )
        return self._transicion(obj, EstadosPOAU.APROBADO, request, 'aprobar',
                                'Registro POAU aprobado')

    @action(detail=True, methods=['post'])
    def observar(self, request, pk=None):
        """La jefatura devuelve el registro con el motivo."""
        from .permissions import es_aprobador
        if not es_aprobador(request.user):
            return self._denegar('Solo la jefatura puede observar registros POAU.')
        comentario = str(request.data.get('comentario', '')).strip()
        if not comentario:
            return self._rechazar('Se requiere un comentario para observar.')
        obj = self.get_object()
        if obj.estado == EstadosPOAU.APROBADO:
            return self._rechazar('Un registro aprobado ya no admite cambios.')
        return self._transicion(obj, EstadosPOAU.OBSERVADO, request, 'observar',
                                f'Registro POAU observado: {comentario[:200]}',
                                observacion=comentario)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.estado == EstadosPOAU.APROBADO:
            return self._rechazar(
                'Un registro aprobado no se puede eliminar. Pida a la jefatura '
                'que lo observe primero.'
            )
        from .services import registrar_auditoria
        registrar_auditoria(
            usuario=request.user, accion='eliminar',
            entidad=obj.__class__.__name__, entidad_id=str(obj.id),
            detalle='Registro POAU eliminado',
        )
        return super().destroy(request, *args, **kwargs)
