"""dry-run por defecto, --aplicar para borrar de verdad, por código exacto."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.articulacion.models import AccionPOA, AsignacionObjetoGasto, OperacionPOAU, ProductoPEI, ResultadoPEI
from apps.gestion.testing import habilitar_gestion_para_tests


class BorrarAsignacionesGastoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        habilitar_gestion_para_tests(2027)
        resultado = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030,
        )
        producto = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado,
        )
        cls.accion = AccionPOA.objects.create(
            codigo_accion='ACP-BORRAR', denominacion='Acción de prueba',
            producto_pei=producto, gestion=2027,
        )
        cls.operacion = OperacionPOAU.objects.create(
            codigo_operacion='OP-BORRAR', denominacion='Operación',
            tipo_operacion='SUSTANTIVA', accion_poa=cls.accion,
        )

    def _crear(self, codigo, **overrides):
        datos = dict(
            codigo_asignacion=codigo, gestion=2027,
            accion_poa=self.accion, operacion=self.operacion,
            categoria_programatica='170 0 001', da='1', ue='001',
            programa='170', cod_objeto_gasto='25200',
            descripcion_objeto='Estudios', grupo_gasto='20000',
            tipo_gasto='Funcionamiento', fuente_financiamiento='20',
            organismo_financiador='230', monto_programado=1000,
            monto_vigente=1000,
        )
        datos.update(overrides)
        return AsignacionObjetoGasto.objects.create(**datos)

    def test_dry_run_no_borra_nada(self):
        self._crear('ACP-BORRAR.G1')
        out = StringIO()
        call_command(
            'borrar_asignaciones_gasto', '--codigo=ACP-BORRAR.G1', stdout=out,
        )
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 1)
        self.assertIn('Dry-run', out.getvalue())

    def test_aplicar_borra_solo_los_codigos_pedidos(self):
        self._crear('ACP-BORRAR.G1')
        conservar = self._crear('ACP-BORRAR.G2')
        out = StringIO()
        call_command(
            'borrar_asignaciones_gasto', '--codigo=ACP-BORRAR.G1',
            '--aplicar', stdout=out,
        )
        self.assertEqual(
            list(AsignacionObjetoGasto.objects.values_list('pk', flat=True)),
            [conservar.pk],
        )
        self.assertIn('Borradas 1', out.getvalue())

    def test_codigo_inexistente_no_rompe_el_resto(self):
        self._crear('ACP-BORRAR.G1')
        out = StringIO()
        call_command(
            'borrar_asignaciones_gasto',
            '--codigo=ACP-BORRAR.G1', '--codigo=NO-EXISTE.G9',
            '--aplicar', stdout=out,
        )
        self.assertEqual(AsignacionObjetoGasto.objects.count(), 0)
        self.assertIn('NO-EXISTE.G9', out.getvalue())

    def test_ningun_codigo_encontrado_no_falla(self):
        out = StringIO()
        call_command(
            'borrar_asignaciones_gasto', '--codigo=NO-EXISTE.G9',
            '--aplicar', stdout=out,
        )
        self.assertIn('Ningún código', out.getvalue())
