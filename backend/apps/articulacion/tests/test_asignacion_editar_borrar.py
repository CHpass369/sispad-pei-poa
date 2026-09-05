"""Editar y borrar un requerimiento desde la matriz de programación.

La matriz de abajo de `/sis-poa/poaus` era de solo lectura: corregir un monto
obligaba a rehacer el requerimiento desde el asistente. Al abrir la edición y el
borrado por botón, dos cosas tienen que quedar fijadas:

- **el borrado deja un `EventoAuditoria` con la fila entera.** Es físico y no
  hay historial: sin el evento, una fila eliminada no deja ningún rastro de
  haber existido. Ya pasó —una importación se llevó 62 requerimientos por
  cascada el 2026-09-04, irrecuperables—, así que el evento se arma ANTES de
  borrar, cuando todavía hay de dónde leer los datos;
- **la edición estampa `updated_by`.** El alta nunca guardó autor y quedaron
  filas sin saber quién las cargó; en la corrección no se repite.
"""
from decimal import Decimal

from rest_framework import status

from apps.articulacion.models import AsignacionObjetoGasto, OperacionPOAU
from apps.auditoria.models import EventoAuditoria

from .test_scope_poau_unidad import ScopePOAUUnidadBase

RUTA = '/api/v1/articulacion/asignaciones-gasto/'


class EditarYBorrarRequerimientoTests(ScopePOAUUnidadBase):

    def setUp(self):
        super().setUp()
        # El requerimiento cuelga de la operación, no de la actividad: así
        # quedó desde que el asistente dejó de pedir actividad.
        operacion = OperacionPOAU.objects.get(codigo_operacion='OP-PROPIA')
        self.fila = AsignacionObjetoGasto.objects.create(
            codigo_asignacion='REQ-TEST-001',
            gestion=2027,
            accion_poa=self.accion_propia,
            operacion=operacion,
            categoria_programatica='340 0 099',
            cod_objeto_gasto='25200',
            descripcion_objeto='Estudios e investigaciones',
            fuente_financiamiento='20',
            organismo_financiador='230',
            monto_programado=Decimal('10000.00'),
            monto_vigente=Decimal('10000.00'),
            programacion_mensual={'enero': 10000},
        )

    def test_el_borrado_deja_evento_de_auditoria_con_la_fila(self):
        respuesta = self.cliente(self.global_).delete(f'{RUTA}{self.fila.pk}/')
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            AsignacionObjetoGasto.objects.filter(pk=self.fila.pk).exists()
        )

        evento = EventoAuditoria.objects.filter(
            entidad='AsignacionObjetoGasto', entidad_id=str(self.fila.pk),
        ).first()
        self.assertIsNotNone(evento, 'el borrado no dejó rastro')
        self.assertEqual(evento.accion, EventoAuditoria.Accion.ANULAR)
        self.assertIn('REQ-TEST-001', evento.resumen)
        # Lo que importa del evento: que se pueda reconstruir cuánto se borró.
        self.assertEqual(evento.datos_previos['codigo_asignacion'], 'REQ-TEST-001')
        self.assertEqual(evento.datos_previos['monto_programado'], '10000.00')
        self.assertEqual(evento.datos_previos['programacion_mensual'], {'enero': 10000})
        self.assertEqual(evento.datos_previos['unidad'], self.propia.codigo)

    def test_la_edicion_estampa_el_autor(self):
        respuesta = self.cliente(self.global_).patch(
            f'{RUTA}{self.fila.pk}/',
            {'descripcion_objeto': 'Consultoría de línea'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        self.fila.refresh_from_db()
        self.assertEqual(self.fila.descripcion_objeto, 'Consultoría de línea')
        self.assertEqual(self.fila.updated_by_id, self.global_.id)

    def test_sin_capacidad_de_escritura_no_se_borra(self):
        """El botón es nuevo; el candado del endpoint es el de siempre."""
        respuesta = self.cliente(self.sin_alcance).delete(f'{RUTA}{self.fila.pk}/')
        self.assertIn(
            respuesta.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.assertTrue(
            AsignacionObjetoGasto.objects.filter(pk=self.fila.pk).exists()
        )
