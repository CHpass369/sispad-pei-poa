from django.test import TestCase
from django.db import IntegrityError
from apps.articulacion.models import (
    CodigoNivel, AcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, TareaPOAU, SeguimientoPresupuesto, AsignacionObjetoGasto,
)


class CodigoNivelModelTest(TestCase):
    def test_create_codigo_nivel(self):
        padre = CodigoNivel.objects.create(
            nivel='Entidad', codigo_nivel='01', segmentos='ENT',
            longitud='4', ejemplo='0001', regla_generacion='Auto',
            vigencia='2026-2030'
        )
        hijo = CodigoNivel.objects.create(
            nivel='Resultado PAD', codigo_nivel='10', segmentos='CGEO.LL.RR',
            longitud='6+2+2', ejemplo='031001.03.01',
            regla_generacion='Manual', editable=True,
            codigo_padre=padre, vigencia='2026-2030'
        )
        self.assertEqual(str(padre), '[01] Entidad')
        self.assertEqual(str(hijo), '[10] Resultado PAD')
        self.assertEqual(hijo.codigo_padre, padre)
        self.assertTrue(hijo.editable)
        self.assertFalse(padre.editable)


class AcuerdoInternacionalModelTest(TestCase):
    def setUp(self):
        self.ods = AcuerdoInternacional.objects.create(
            tipo_acuerdo='ODS', codigo='01',
            denominacion='Fin de la pobreza', activo=True
        )
        self.ndc = AcuerdoInternacional.objects.create(
            tipo_acuerdo='NDC', codigo='01',
            denominacion='Contribución 1', activo=True
        )

    def test_str_representation(self):
        self.assertIn('ODS', str(self.ods))
        self.assertIn('NDC', str(self.ndc))

    def test_tipo_acuerdo_choices(self):
        self.assertEqual(self.ods.tipo_acuerdo, 'ODS')
        self.assertEqual(self.ndc.tipo_acuerdo, 'NDC')

    def test_activo_default(self):
        self.assertTrue(self.ods.activo)

    def test_es_codigo_oficial_default(self):
        self.assertTrue(self.ods.es_codigo_oficial)


class NormativaModelTest(TestCase):
    def setUp(self):
        self.norma = Normativa.objects.create(
            codigo_norma='001', nivel='Nacional',
            tipo_norma='Ley', numero_identificador='123',
            denominacion='Ley de prueba'
        )

    def test_create_normativa(self):
        self.assertEqual(self.norma.estado, 'VALIDAR')
        self.assertEqual(str(self.norma), '[001] Ley de prueba')

    def test_reemplazada_por(self):
        nueva = Normativa.objects.create(
            codigo_norma='002', nivel='Nacional',
            tipo_norma='Ley', numero_identificador='456',
            denominacion='Ley actualizada',
            reemplazada_por=self.norma
        )
        self.assertEqual(nueva.reemplazada_por, self.norma)
        self.assertIn(self.norma, nueva.reemplazada_por.reemplazos.all())

    def test_unique_codigo_norma(self):
        with self.assertRaises(IntegrityError):
            Normativa.objects.create(
                codigo_norma='001', nivel='Nacional',
                tipo_norma='Ley', numero_identificador='789',
                denominacion='Duplicada'
            )


class LineamientoPADModelTest(TestCase):
    def setUp(self):
        self.lineamiento = LineamientoPAD.objects.create(
            codigo='03', denominacion='Lineamiento de prueba',
            gestion_desde=2026, gestion_hasta=2030
        )

    def test_create_lineamiento(self):
        self.assertEqual(str(self.lineamiento), '[03] Lineamiento de prueba')
        self.assertTrue(self.lineamiento.activo)
        self.assertEqual(self.lineamiento.codigo_padre, '')


class ResultadoPADModelTest(TestCase):
    def setUp(self):
        self.resultado = ResultadoPAD.objects.create(
            id_cadena='0000000001', codigo_resultado='031001.03.01',
            denominacion='Resultado de prueba',
            lineamiento_pad='03', vigencia_desde=2026, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA01'
        )

    def test_create_resultado_pad(self):
        self.assertEqual(
            str(self.resultado),
            '[031001.03.01] Resultado de prueba'
        )
        self.assertEqual(self.resultado.estado, 'REFERENCIAL')

    def test_unique_id_cadena(self):
        with self.assertRaises(IntegrityError):
            ResultadoPAD.objects.create(
                id_cadena='0000000001', codigo_resultado='999999.99.99',
                denominacion='Duplicado',
                lineamiento_pad='03', vigencia_desde=2027, vigencia_hasta=2030,
                cod_geografico='00', eta='ETA02'
            )


class ProductoPADModelTest(TestCase):
    def setUp(self):
        self.resultado = ResultadoPAD.objects.create(
            id_cadena='0000000001', codigo_resultado='031001.03.01',
            denominacion='Resultado PAD',
            lineamiento_pad='03', vigencia_desde=2026, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA01'
        )

    def test_create_producto_pad(self):
        producto = ProductoPAD.objects.create(
            codigo_producto='031001.03.01.01',
            denominacion='Producto PAD de prueba',
            resultado_pad=self.resultado
        )
        self.assertEqual(
            str(producto),
            '[031001.03.01.01] Producto PAD de prueba'
        )
        self.assertIn(producto, self.resultado.productos.all())


class AccionPOAModelTest(TestCase):
    def setUp(self):
        self.resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad de prueba',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=self.resultado_pei
        )

    def test_create_accion_poa(self):
        accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA de prueba',
            producto_pei=self.producto_pei,
            gestion=2026
        )
        self.assertEqual(str(accion), '[0001.01.01.01] Acción POA de prueba')
        self.assertEqual(accion.estado, 'REFERENCIAL')
        self.assertIn(accion, self.producto_pei.acciones_poa.all())

    def test_unique_codigo_accion(self):
        AccionPOA.objects.create(
            codigo_accion='UNICO', denominacion='Primera',
            producto_pei=self.producto_pei, gestion=2026
        )
        with self.assertRaises(IntegrityError):
            AccionPOA.objects.create(
                codigo_accion='UNICO', denominacion='Segunda',
                producto_pei=self.producto_pei, gestion=2026
            )


class ArticulacionPADPEIModelTest(TestCase):
    def setUp(self):
        resultado_pad = ResultadoPAD.objects.create(
            id_cadena='0000000001', codigo_resultado='031001.03.01',
            denominacion='Resultado PAD',
            lineamiento_pad='03', vigencia_desde=2026, vigencia_hasta=2030,
            cod_geografico='00', eta='ETA01'
        )
        self.producto_pad = ProductoPAD.objects.create(
            codigo_producto='031001.03.01.01',
            denominacion='Producto PAD',
            resultado_pad=resultado_pad
        )
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        self.producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )

    def test_create_articulacion(self):
        art = ArticulacionPADPEI.objects.create(
            producto_pad=self.producto_pad,
            producto_pei=self.producto_pei,
            tipo_contribucion='Directa', ponderacion=50.00,
            justificacion='Articulación estratégica'
        )
        self.assertIn(
            self.producto_pad.codigo_producto,
            str(art)
        )
        self.assertIn(
            self.producto_pei.codigo_producto,
            str(art)
        )
        self.assertEqual(art.estado, 'REFERENCIAL')

    def test_unique_articulacion(self):
        ArticulacionPADPEI.objects.create(
            producto_pad=self.producto_pad,
            producto_pei=self.producto_pei,
        )
        with self.assertRaises(IntegrityError):
            ArticulacionPADPEI.objects.create(
                producto_pad=self.producto_pad,
                producto_pei=self.producto_pei,
            )


class OperacionPOAUTest(TestCase):
    def setUp(self):
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA',
            producto_pei=producto_pei,
            gestion=2026
        )

    def test_create_operacion(self):
        operacion = OperacionPOAU.objects.create(
            codigo_operacion='0001.01.01.01.01',
            denominacion='Operación de prueba',
            tipo_operacion='Mantenimiento',
            accion_poa=self.accion,
            total_programado=100.0000
        )
        self.assertEqual(
            str(operacion),
            '[0001.01.01.01.01] Operación de prueba'
        )
        self.assertIn(operacion, self.accion.operaciones.all())


class ActividadPOAUTest(TestCase):
    def setUp(self):
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )
        accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA',
            producto_pei=producto_pei, gestion=2026
        )
        self.operacion = OperacionPOAU.objects.create(
            codigo_operacion='0001.01.01.01.01',
            denominacion='Operación',
            tipo_operacion='Mantenimiento',
            accion_poa=accion
        )

    def test_create_actividad(self):
        actividad = ActividadPOAU.objects.create(
            codigo_actividad='0001.01.01.01.01.01',
            denominacion='Actividad de prueba',
            operacion=self.operacion
        )
        self.assertEqual(
            str(actividad),
            '[0001.01.01.01.01.01] Actividad de prueba'
        )
        self.assertIn(actividad, self.operacion.actividades.all())


class TareaPOAUTest(TestCase):
    def setUp(self):
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )
        accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA',
            producto_pei=producto_pei, gestion=2026
        )
        operacion = OperacionPOAU.objects.create(
            codigo_operacion='0001.01.01.01.01',
            denominacion='Operación',
            tipo_operacion='Mantenimiento',
            accion_poa=accion
        )
        self.actividad = ActividadPOAU.objects.create(
            codigo_actividad='0001.01.01.01.01.01',
            denominacion='Actividad',
            operacion=operacion
        )

    def test_create_tarea(self):
        tarea = TareaPOAU.objects.create(
            codigo_tarea='0001.01.01.01.01.01.01',
            denominacion='Tarea de prueba',
            actividad=self.actividad
        )
        self.assertEqual(
            str(tarea),
            '[0001.01.01.01.01.01.01] Tarea de prueba'
        )
        self.assertIn(tarea, self.actividad.tareas.all())


class SeguimientoPresupuestoModelTest(TestCase):
    def setUp(self):
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA',
            producto_pei=producto_pei, gestion=2026
        )
        self.operacion = OperacionPOAU.objects.create(
            codigo_operacion='0001.01.01.01.01',
            denominacion='Operación',
            tipo_operacion='Mantenimiento',
            accion_poa=self.accion
        )
        self.actividad = ActividadPOAU.objects.create(
            codigo_actividad='0001.01.01.01.01.01',
            denominacion='Actividad',
            operacion=self.operacion
        )

    def test_create_seguimiento(self):
        seg = SeguimientoPresupuesto.objects.create(
            id_cadena='SP0001', gestion=2026,
            accion_poa=self.accion,
            operacion=self.operacion,
            actividad=self.actividad,
            categoria_programatica='CP001', da='DA01',
            ue='UE01', programa='Programa 1',
            tipo_gasto='Corriente',
            presupuesto_inicial=100000.00,
            presupuesto_vigente=100000.00
        )

        self.assertEqual(
            str(seg),
            'SP SP0001 - G2026'
        )


class AsignacionObjetoGastoModelTest(TestCase):
    def setUp(self):
        resultado_pei = ResultadoPEI.objects.create(
            codigo_resultado='0001.01', denominacion='Resultado PEI',
            cod_entidad='01', entidad='Entidad',
            vigencia_desde=2026, vigencia_hasta=2030
        )
        producto_pei = ProductoPEI.objects.create(
            codigo_producto='0001.01.01', denominacion='Producto PEI',
            resultado_pei=resultado_pei
        )
        self.accion = AccionPOA.objects.create(
            codigo_accion='0001.01.01.01',
            denominacion='Acción POA',
            producto_pei=producto_pei, gestion=2026
        )

    def test_create_asignacion(self):
        asig = AsignacionObjetoGasto.objects.create(
            codigo_asignacion='00000001', gestion=2026,
            accion_poa=self.accion,
            categoria_programatica='CP001', da='DA01',
            ue='UE01', programa='Programa 1',
            cod_objeto_gasto='21000',
            descripcion_objeto='Servicios básicos',
            grupo_gasto='20000', tipo_gasto='Corriente',
            fuente_financiamiento='FF01',
            organismo_financiador='OF01',
            monto_programado=50000.00,
            monto_vigente=50000.00
        )
        self.assertIn('00000001', str(asig))
        self.assertEqual(asig.estado, 'REFERENCIAL')
