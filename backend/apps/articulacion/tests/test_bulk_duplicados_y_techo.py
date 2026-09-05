"""Los dos candados de la carga masiva de requerimientos.

Ambos salieron de defectos reportados desde producción:

- **Tandas duplicadas.** El asistente deja el formulario cargado tras un
  guardado exitoso y vuelve a habilitar el botón. Un segundo clic manda
  exactamente la misma tanda y, como `codigo_asignacion` lo genera el servidor,
  nada la reconocía como repetida: las unidades terminaron con requerimientos
  duplicados. Una guarda en el navegador no alcanza —no sobrevive a un reintento
  de red ni a dos pestañas—, así que el rechazo va en el servidor.
- **Programación por encima del techo.** El asistente ya avisaba del exceso pero
  **solo contra el formulario abierto**: programar el 100% del saldo, guardar,
  volver a entrar y programar otro 100% pasaba sin queja. Acá se suma lo que ya
  está en la base, que es lo único que refleja el consumo real.
"""
from decimal import Decimal

from rest_framework import status

from apps.articulacion.models import (
    AsignacionObjetoGasto, OperacionPOAU, SaldoUnidadCategoria,
)

from .test_scope_poau_unidad import ScopePOAUUnidadBase

BULK = '/api/v1/articulacion/asignaciones-gasto/bulk/'


class BulkDuplicadosYTechoBase(ScopePOAUUnidadBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.operacion = OperacionPOAU.objects.get(codigo_operacion='OP-PROPIA')
        cls.techo = SaldoUnidadCategoria.objects.create(
            unidad=cls.propia, categoria_programatica='340 0 099',
            denominacion='TECHO DE PRUEBA',
            saldo=Decimal('100000.00'), filas_origen=1,
        )

    def requerimiento(self, enero=50000, descripcion='Estudios'):
        return {
            'gestion': 2027,
            'accion_poa': self.accion_propia.pk,
            'operacion': self.operacion.pk,
            'actividad': None,
            'categoria_programatica': '340 0 099',
            'da': '1', 'ue': '001', 'programa': '340',
            'cod_objeto_gasto': '25200',
            'descripcion_objeto': descripcion,
            'grupo_gasto': '20000', 'tipo_gasto': 'Funcionamiento',
            'fuente_financiamiento': '20', 'organismo_financiador': '230',
            'monto_programado': str(enero), 'monto_vigente': str(enero),
            'programacion_mensual': {'enero': enero},
        }

    def enviar(self, cuerpos, usuario=None):
        return self.cliente(usuario or self.global_).post(
            BULK, cuerpos, format='json')


class TandaRepetidaTests(BulkDuplicadosYTechoBase):
    """A. La misma tanda no entra dos veces."""

    def test_la_segunda_tanda_identica_se_rechaza(self):
        primera = self.enviar([self.requerimiento(enero=10000)])
        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 1)

        segunda = self.enviar([self.requerimiento(enero=10000)])
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)
        detalle = str(segunda.data)
        self.assertIn('ya está registrada', detalle)
        # Lo que importa: no quedó una segunda fila.
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 1)

    def test_un_requerimiento_distinto_si_entra(self):
        """Coincidir en la partida no basta: se compara la fila entera."""
        self.assertEqual(
            self.enviar([self.requerimiento(enero=10000)]).status_code,
            status.HTTP_201_CREATED,
        )
        otro = self.enviar([
            self.requerimiento(enero=10000, descripcion='Consultoría de línea'),
        ])
        self.assertEqual(otro.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 2)

    def test_una_tanda_solo_parcialmente_repetida_entra(self):
        """Una coincidencia parcial puede ser una carga legítima."""
        self.enviar([self.requerimiento(enero=10000)])
        mixta = self.enviar([
            self.requerimiento(enero=10000),
            self.requerimiento(enero=5000, descripcion='Material de escritorio'),
        ])
        self.assertEqual(mixta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 3)


class TechoDeCategoriaTests(BulkDuplicadosYTechoBase):
    """B. No se programa por encima del techo declarado."""

    def test_una_tanda_que_se_pasa_del_techo_se_rechaza(self):
        respuesta = self.enviar([self.requerimiento(enero=150000)])
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('techo', str(respuesta.data))
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 0)

    def test_el_techo_cuenta_lo_YA_guardado_y_no_solo_la_tanda(self):
        """El defecto real: dos tandas que solas caben, juntas no.

        Es el caso que el aviso del navegador no podía ver, porque solo miraba
        el formulario abierto.
        """
        primera = self.enviar([self.requerimiento(enero=60000)])
        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)

        segunda = self.enviar([
            self.requerimiento(enero=60000, descripcion='Segunda carga'),
        ])
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)
        detalle = str(segunda.data)
        self.assertIn('60,000.00', detalle)   # lo ya programado
        self.assertIn('20,000.00', detalle)   # el exceso
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 1)

    def test_justo_hasta_el_techo_entra(self):
        respuesta = self.enviar([self.requerimiento(enero=100000)])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_sin_techo_declarado_no_se_bloquea(self):
        """Saldo ausente significa «no revisado», no «cero disponible»."""
        self.techo.delete()
        respuesta = self.enviar([self.requerimiento(enero=999999)])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
