"""El código de asignación lo asigna el servidor, no el asistente.

El asistente componía `<codigo_accion>.G<indice>` con el índice del
formulario: cada guardado reiniciaba en `.G1` y violaba la unicidad por
gestión. Ahora el serializer asigna el código consecutivo a partir del
último guardado para la acción en esa gestión.
"""
from django.test import TestCase

from apps.articulacion.models import (
    AccionPOA, AsignacionObjetoGasto, OperacionPOAU, ProductoPEI,
    ResultadoPEI,
)
from apps.articulacion.serializers import AsignacionObjetoGastoSerializer


def base_datos():
    resultado_pei = ResultadoPEI.objects.create(
        codigo_resultado='0001.01', denominacion='Resultado PEI',
        cod_entidad='01', entidad='Entidad',
        vigencia_desde=2026, vigencia_hasta=2030,
    )
    producto_pei = ProductoPEI.objects.create(
        codigo_producto='0001.01.01', denominacion='Producto PEI',
        resultado_pei=resultado_pei,
    )
    accion = AccionPOA.objects.create(
        codigo_accion='ACP-01', denominacion='Acción POA',
        producto_pei=producto_pei, gestion=2027,
    )
    operacion = OperacionPOAU.objects.create(
        codigo_operacion='OP-01', denominacion='Operación',
        tipo_operacion='SUSTANTIVA', accion_poa=accion,
    )
    return accion, operacion


def carga(accion, operacion, gestion=2027, actividad=None, **extra):
    datos = {
        'gestion': gestion,
        'accion_poa': accion.pk,
        'operacion': operacion.pk,
        'actividad': actividad,
        'categoria_programatica': '170 0 001', 'da': '1', 'ue': '001',
        'programa': '170', 'cod_objeto_gasto': '25200',
        'descripcion_objeto': 'Estudios e Investigaciones',
        'grupo_gasto': '20000', 'tipo_gasto': 'Funcionamiento',
        'fuente_financiamiento': '20', 'organismo_financiador': '230',
        'monto_programado': '1000', 'monto_vigente': '1000',
    }
    datos.update(extra)
    return datos


class CodigoAsignacionAutomaticoTest(TestCase):
    def setUp(self):
        self.accion, self.operacion = base_datos()

    def _guardar(self, datos):
        serializer = AsignacionObjetoGastoSerializer(data=datos)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_sin_codigo_el_servidor_asigna_el_primero(self):
        asig = self._guardar(carga(self.accion, self.operacion))
        self.assertEqual(asig.codigo_asignacion, 'ACP-01.G1')

    def test_el_segundo_guardado_sigue_al_ultimo(self):
        """Dos guardados seguidos de la misma acción no repiten código."""
        self._guardar(carga(self.accion, self.operacion))
        segunda = self._guardar(carga(self.accion, self.operacion))
        self.assertEqual(segunda.codigo_asignacion, 'ACP-01.G2')

    def test_el_maximo_es_numerico_no_alfabetico(self):
        """`G9` y `G10` guardadas: el siguiente es `G11`, no `G10` otra vez.

        Un máximo de cadenas elegiría `G9` (``'9' > '1'``) y devolvería un
        código que ya existe.
        """
        for codigo in ('ACP-01.G9', 'ACP-01.G10'):
            AsignacionObjetoGasto.objects.create(
                codigo_asignacion=codigo, gestion=2027, accion_poa=self.accion,
                operacion=self.operacion, categoria_programatica='170 0 001',
                da='1', ue='001', programa='170', cod_objeto_gasto='25200',
                descripcion_objeto='Estudios', grupo_gasto='20000',
                tipo_gasto='Funcionamiento', fuente_financiamiento='20',
                organismo_financiador='230', monto_programado=1,
                monto_vigente=1,
            )
        asig = self._guardar(carga(self.accion, self.operacion))
        self.assertEqual(asig.codigo_asignacion, 'ACP-01.G11')

    def test_un_codigo_explicito_se_respeta(self):
        """El importador sigue mandando su propio código: no se pisa."""
        asig = self._guardar(carga(self.accion, self.operacion, codigo_asignacion='IMPORT-7'))
        self.assertEqual(asig.codigo_asignacion, 'IMPORT-7')

    def test_el_consecutivo_es_por_gestion(self):
        """La misma acción en dos gestiones arranca de `.G1` en cada una."""
        self._guardar(carga(self.accion, self.operacion, gestion=2027))
        otra = self._guardar(carga(self.accion, self.operacion, gestion=2028))
        self.assertEqual(otra.codigo_asignacion, 'ACP-01.G1')

    def test_el_consecutivo_es_por_accion(self):
        otra_accion = AccionPOA.objects.create(
            codigo_accion='ACP-02', denominacion='Otra acción',
            producto_pei=self.accion.producto_pei, gestion=2027,
        )
        AsignacionObjetoGasto.objects.create(
            codigo_asignacion='ACP-01.G1', gestion=2027,
            accion_poa=self.accion, operacion=self.operacion,
            categoria_programatica='170 0 001', da='1', ue='001',
            programa='170', cod_objeto_gasto='25200',
            descripcion_objeto='Estudios', grupo_gasto='20000',
            tipo_gasto='Funcionamiento', fuente_financiamiento='20',
            organismo_financiador='230', monto_programado=1,
            monto_vigente=1,
        )
        datos = carga(self.accion, self.operacion)
        datos['accion_poa'] = otra_accion.pk
        asig = self._guardar(datos)
        self.assertEqual(asig.codigo_asignacion, 'ACP-02.G1')
