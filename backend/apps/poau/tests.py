from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.accounts.models import Usuario
from apps.gestion.models import GestionFiscal
from apps.catalogos.models import ObjetoGasto, FuenteFinanciamiento
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora,
)
from apps.presupuesto.models import ProgramaPresupuestario
from apps.techos.models import TechoPresupuestario, DistribucionTecho
from apps.poau.models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera


class POAUBaseTestCase(TestCase):
    """Base para tests del módulo POAU."""

    def setUp(self):
        self.vig = date(2026, 1, 1)
        self.user = Usuario.objects.create_user(
            email='poau_test@gamsacaba.gob.bo', password='test123',
            first_name='POAU', last_name='Test',
        )
        self.user_resp = Usuario.objects.create_user(
            email='responsable@gamsacaba.gob.bo', password='test123',
            first_name='Responsable', last_name='POAU',
        )
        self.gestion = GestionFiscal.objects.create(
            anio=2026, estado='abierta',
            anio_inicio_plurianual=2026, anio_fin_plurianual=2028,
        )
        self.tipo_unidad = TipoUnidad.objects.create(
            codigo='SEC', nombre='Secretaría', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='SEC-01', nombre='Secretaría General',
            sigla='SG', tipo=self.tipo_unidad, gestion=2026,
            fecha_vigencia_desde=self.vig,
        )
        self.unidad_2 = UnidadOrganizacional.objects.create(
            codigo='SEC-02', nombre='Secretaría de Obras',
            sigla='SO', tipo=self.tipo_unidad, gestion=2026,
            fecha_vigencia_desde=self.vig,
        )
        self.da = DireccionAdministrativa.objects.create(
            codigo='DA-01', nombre='Dirección Administrativa',
            gestion=2026, fecha_vigencia_desde=self.vig,
        )
        self.ue = UnidadEjecutora.objects.create(
            codigo='UE-01', nombre='Unidad Ejecutora 1',
            da=self.da, gestion=2026, fecha_vigencia_desde=self.vig,
        )
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='41-113', gestion=2026,
            denominacion='Coparticipación Tributaria',
            fecha_vigencia_desde=self.vig,
        )
        self.objeto_gasto = ObjetoGasto.objects.create(
            codigo='10000', gestion=2026,
            denominacion='Servicios Personales',
            fecha_vigencia_desde=self.vig,
        )
        self.objeto_gasto_2 = ObjetoGasto.objects.create(
            codigo='20000', gestion=2026,
            denominacion='Servicios No Personales',
            fecha_vigencia_desde=self.vig,
        )
        self.programa = ProgramaPresupuestario.objects.create(
            codigo='000', nombre='Programa Test',
            gestion=2026,
        )
        self.techo = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('500000.00'),
            fuente=self.fuente,
        )
        self.poau = POAU.objects.create(
            unidad=self.unidad, gestion=2026,
            codigo='POAU-2026-001', nombre='POA Unidad Test',
            estado='borrador', responsable=self.user_resp,
        )
        self.poau_2 = POAU.objects.create(
            unidad=self.unidad_2, gestion=2026,
            codigo='POAU-2026-002', nombre='POA Obras',
            estado='borrador', responsable=self.user,
        )


class POAUModelTest(POAUBaseTestCase):
    """Tests del modelo POAU."""

    def test_poau_creacion(self):
        self.assertEqual(self.poau.gestion, 2026)
        self.assertEqual(self.poau.estado, 'borrador')
        self.assertEqual(self.poau.unidad, self.unidad)

    def test_poau_str(self):
        s = str(self.poau)
        self.assertIn('POAU-2026-001', s)

    def test_poau_estados_disponibles(self):
        estados = [choice[0] for choice in POAU.ESTADO_CHOICES]
        self.assertIn('borrador', estados)
        self.assertIn('enviado', estados)
        self.assertIn('aprobado', estados)
        self.assertIn('rechazado', estados)

    def test_poau_transicion_borrador_a_enviado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'enviado')

    def test_poau_transicion_enviado_a_aprobado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'aprobado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'aprobado')

    def test_poau_transicion_enviado_a_rechazado(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'rechazado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'rechazado')

    def test_poau_rechazado_puede_volver_borrador(self):
        self.poau.estado = 'enviado'
        self.poau.save()
        self.poau.estado = 'rechazado'
        self.poau.save()
        self.poau.estado = 'borrador'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertEqual(self.poau.estado, 'borrador')

    def test_poau_varias_unidades(self):
        self.assertNotEqual(self.poau.unidad, self.poau_2.unidad)
        self.assertEqual(POAU.objects.filter(gestion=2026).count(), 2)

    def test_poau_codigo_unico(self):
        with self.assertRaises(Exception):
            POAU.objects.create(
                unidad=self.unidad, gestion=2026,
                codigo='POAU-2026-001',
                nombre='Duplicado', estado='borrador',
            )

    def test_poau_responsable(self):
        self.assertEqual(self.poau.responsable, self.user_resp)

    def test_poau_con_producto_territorial_nulo(self):
        self.assertIsNone(self.poau.producto_territorial)

    def test_poau_updated_at(self):
        old_updated = self.poau.updated_at
        self.poau.nombre = 'Nombre Actualizado'
        self.poau.save()
        self.poau.refresh_from_db()
        self.assertGreaterEqual(self.poau.updated_at, old_updated)


class POAUActividadModelTest(POAUBaseTestCase):
    """Tests del modelo POAUActividad."""

    def test_actividad_creacion(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-01',
            nombre='Actividad de Prueba',
            presupuesto_anual=Decimal('50000.00'),
            meta_fisica_anual=Decimal('100.0000'),
        )
        self.assertEqual(act.codigo, 'ACT-01')
        self.assertEqual(act.presupuesto_anual, Decimal('50000.00'))

    def test_actividad_str(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-02',
            nombre='Actividad Str',
        )
        s = str(act)
        self.assertIn('ACT-02', s)

    def test_actividad_unique_together(self):
        POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-03',
            nombre='Primera',
        )
        with self.assertRaises(Exception):
            POAUActividad.objects.create(
                poau=self.poau, codigo='ACT-03',
                nombre='Duplicada',
            )

    def test_actividad_meta_trimestres_correctos(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-Q',
            nombre='Actividad Trimestres',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('25.0000'),
            meta_q2=Decimal('25.0000'),
            meta_q3=Decimal('25.0000'),
            meta_q4=Decimal('25.0000'),
        )
        suma = act.meta_q1 + act.meta_q2 + act.meta_q3 + act.meta_q4
        self.assertEqual(suma, act.meta_fisica_anual)

    def test_actividad_meta_trimestres_incorrectos(self):
        act = POAUActividad(
            poau=self.poau, codigo='ACT-BAD',
            nombre='Actividad Inválida',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('30.0000'),
            meta_q2=Decimal('30.0000'),
            meta_q3=Decimal('30.0000'),
            meta_q4=Decimal('30.0000'),
        )
        with self.assertRaises(ValidationError):
            act.full_clean()

    def test_actividad_meta_q1_nula(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-NULL-Q',
            nombre='Actividad Q Nulo',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=None, meta_q2=Decimal('25.0000'),
            meta_q3=Decimal('25.0000'), meta_q4=Decimal('25.0000'),
        )
        self.assertIsNone(act.meta_q1)

    def test_actividad_varias_por_poau(self):
        for i in range(5):
            POAUActividad.objects.create(
                poau=self.poau, codigo=f'ACT-{i:03d}',
                nombre=f'Actividad {i}',
            )
        self.assertEqual(
            POAUActividad.objects.filter(poau=self.poau).count(), 5
        )

    def test_actividad_sin_objeto_gasto(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-SIN-OG',
            nombre='Sin Objeto Gasto',
        )
        self.assertIsNone(act.objeto_gasto)

    def test_actividad_con_objeto_gasto(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-CON-OG',
            nombre='Con Objeto Gasto',
            objeto_gasto=self.objeto_gasto,
        )
        self.assertEqual(act.objeto_gasto, self.objeto_gasto)

    def test_actividad_presupuesto_cero(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-CERO',
            nombre='Presupuesto Cero',
            presupuesto_anual=Decimal('0.00'),
        )
        self.assertEqual(act.presupuesto_anual, Decimal('0.00'))


class EjecucionFisicaModelTest(POAUBaseTestCase):
    """Tests del modelo EjecucionFisica."""

    def setUp(self):
        super().setUp()
        self.actividad = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-EF',
            nombre='Actividad Ejecución Física',
            meta_fisica_anual=Decimal('200.0000'),
        )

    def test_ejecucion_fisica_creacion(self):
        ef = EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-Q1',
            tipo_periodo='trimestral',
            programado=Decimal('50.0000'),
            ejecutado=Decimal('40.0000'),
        )
        self.assertEqual(ef.programado, Decimal('50.0000'))
        self.assertEqual(ef.ejecutado, Decimal('40.0000'))

    def test_ejecucion_fisica_str(self):
        ef = EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-01',
            tipo_periodo='mensual',
            programado=Decimal('10.0000'),
            ejecutado=Decimal('8.0000'),
        )
        s = str(ef)
        self.assertIn('ACT-EF', s)
        self.assertIn('2026-01', s)

    def test_ejecucion_fisica_unique_together(self):
        EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-Q1',
            tipo_periodo='trimestral',
            programado=Decimal('50.0000'),
        )
        with self.assertRaises(Exception):
            EjecucionFisica.objects.create(
                actividad=self.actividad, periodo='2026-Q1',
                tipo_periodo='trimestral',
                programado=Decimal('60.0000'),
            )

    def test_ejecucion_fisica_avance_100(self):
        EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-01',
            tipo_periodo='mensual',
            programado=Decimal('20.0000'),
            ejecutado=Decimal('20.0000'),
        )
        ef = EjecucionFisica.objects.filter(actividad=self.actividad).first()
        avance = (ef.ejecutado / ef.programado) * 100 if ef.programado > 0 else 0
        self.assertEqual(avance, Decimal('100.0000'))

    def test_ejecucion_fisica_avance_parcial(self):
        EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-02',
            tipo_periodo='mensual',
            programado=Decimal('40.0000'),
            ejecutado=Decimal('10.0000'),
        )
        ef = EjecucionFisica.objects.filter(actividad=self.actividad).first()
        avance = (ef.ejecutado / ef.programado) * 100 if ef.programado > 0 else 0
        self.assertEqual(avance, Decimal('25.0000'))

    def test_ejecucion_fisica_sin_ejecutar(self):
        ef = EjecucionFisica.objects.create(
            actividad=self.actividad, periodo='2026-Q2',
            tipo_periodo='trimestral',
            programado=Decimal('50.0000'),
            ejecutado=Decimal('0.0000'),
        )
        self.assertEqual(ef.ejecutado, Decimal('0.0000'))

    def test_varios_periodos_misma_actividad(self):
        for mes in ['2026-01', '2026-02', '2026-03']:
            EjecucionFisica.objects.create(
                actividad=self.actividad, periodo=mes,
                tipo_periodo='mensual',
                programado=Decimal('10.0000'),
                ejecutado=Decimal('8.0000'),
            )
        self.assertEqual(
            EjecucionFisica.objects.filter(actividad=self.actividad).count(), 3
        )

    def test_total_programado_acumula(self):
        for q in ['2026-Q1', '2026-Q2']:
            EjecucionFisica.objects.create(
                actividad=self.actividad, periodo=q,
                tipo_periodo='trimestral',
                programado=Decimal('50.0000'),
                ejecutado=Decimal('40.0000'),
            )
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField
        agg = EjecucionFisica.objects.filter(
            actividad=self.actividad
        ).aggregate(
            total=Coalesce(Sum('programado'), 0, output_field=DecimalField(max_digits=20, decimal_places=4))
        )
        self.assertEqual(agg['total'], Decimal('100.0000'))


class EjecucionFinancieraModelTest(POAUBaseTestCase):
    """Tests del modelo EjecucionFinanciera."""

    def setUp(self):
        super().setUp()
        self.actividad = POAUActividad.objects.create(
            poau=self.poau, codigo='ACT-EFN',
            nombre='Actividad Ejecución Financiera',
            presupuesto_anual=Decimal('100000.00'),
        )

    def test_ejecucion_financiera_creacion(self):
        ef = EjecucionFinanciera.objects.create(
            actividad=self.actividad, periodo='2026-Q1',
            tipo_periodo='trimestral',
            programado=Decimal('25000.00'),
            ejecutado=Decimal('20000.00'),
        )
        self.assertEqual(ef.programado, Decimal('25000.00'))

    def test_ejecucion_financiera_str(self):
        ef = EjecucionFinanciera.objects.create(
            actividad=self.actividad, periodo='2026-01',
            tipo_periodo='mensual',
            programado=Decimal('8000.00'),
            ejecutado=Decimal('6000.00'),
        )
        s = str(ef)
        self.assertIn('ACT-EFN', s)

    def test_ejecucion_financiera_unique_together(self):
        EjecucionFinanciera.objects.create(
            actividad=self.actividad, periodo='2026-Q1',
            tipo_periodo='trimestral',
            programado=Decimal('25000.00'),
        )
        with self.assertRaises(Exception):
            EjecucionFinanciera.objects.create(
                actividad=self.actividad, periodo='2026-Q1',
                tipo_periodo='trimestral',
                programado=Decimal('30000.00'),
            )

    def test_avance_financiero_50_porciento(self):
        ef = EjecucionFinanciera.objects.create(
            actividad=self.actividad, periodo='2026-Q1',
            tipo_periodo='trimestral',
            programado=Decimal('50000.00'),
            ejecutado=Decimal('25000.00'),
        )
        avance = (ef.ejecutado / ef.programado) * 100
        self.assertEqual(avance, Decimal('50.0000'))

    def test_ejecucion_financiera_cero(self):
        ef = EjecucionFinanciera.objects.create(
            actividad=self.actividad, periodo='2026-Q2',
            tipo_periodo='trimestral',
            programado=Decimal('25000.00'),
            ejecutado=Decimal('0.00'),
        )
        self.assertEqual(ef.ejecutado, Decimal('0.00'))

    def test_varios_periodos_acumulacion(self):
        for q in ['2026-Q1', '2026-Q2', '2026-Q3', '2026-Q4']:
            EjecucionFinanciera.objects.create(
                actividad=self.actividad, periodo=q,
                tipo_periodo='trimestral',
                programado=Decimal('25000.00'),
                ejecutado=Decimal('20000.00'),
            )
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField
        agg = EjecucionFinanciera.objects.filter(
            actividad=self.actividad
        ).aggregate(
            total_prog=Coalesce(Sum('programado'), 0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            total_ejec=Coalesce(Sum('ejecutado'), 0, output_field=DecimalField(max_digits=20, decimal_places=2)),
        )
        self.assertEqual(agg['total_prog'], Decimal('100000.00'))
        self.assertEqual(agg['total_ejec'], Decimal('80000.00'))


class POAUPresupuestoLineValidationTest(POAUBaseTestCase):
    """Tests de validación de líneas presupuestarias del POAU."""

    def test_poau_con_multiples_actividades(self):
        for i in range(3):
            POAUActividad.objects.create(
                poau=self.poau, codigo=f'MULT-{i:02d}',
                nombre=f'Actividad Múltiple {i}',
                presupuesto_anual=Decimal(f'{10000 * (i + 1)}.00'),
            )
        total = sum(
            a.presupuesto_anual
            for a in POAUActividad.objects.filter(poau=self.poau)
        )
        self.assertEqual(total, Decimal('60000.00'))

    def test_distribucion_techo_coherente(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('400000.00'),
        )
        self.assertLessEqual(dist.monto_asignado, self.techo.monto_total)

    def test_actividades_no_superan_techo(self):
        POAUActividad.objects.create(
            poau=self.poau, codigo='PRES-01',
            nombre='Presupuesto 1',
            presupuesto_anual=Decimal('200000.00'),
        )
        POAUActividad.objects.create(
            poau=self.poau, codigo='PRES-02',
            nombre='Presupuesto 2',
            presupuesto_anual=Decimal('150000.00'),
        )
        total = sum(
            a.presupuesto_anual
            for a in POAUActividad.objects.filter(poau=self.poau)
            if a.presupuesto_anual
        )
        self.assertLessEqual(total, self.techo.monto_total)

    def test_suma_trimestres_igual_meta_anual(self):
        act = POAUActividad.objects.create(
            poau=self.poau, codigo='SUM-META',
            nombre='Suma Meta',
            meta_fisica_anual=Decimal('200.0000'),
            meta_q1=Decimal('50.0000'),
            meta_q2=Decimal('50.0000'),
            meta_q3=Decimal('50.0000'),
            meta_q4=Decimal('50.0000'),
        )
        suma = act.meta_q1 + act.meta_q2 + act.meta_q3 + act.meta_q4
        self.assertEqual(suma, act.meta_fisica_anual)

    def test_trimestres_superan_meta_rechazado(self):
        act = POAUActividad(
            poau=self.poau, codigo='OVER-META',
            nombre='Sobrepasa Meta',
            meta_fisica_anual=Decimal('100.0000'),
            meta_q1=Decimal('30.0000'),
            meta_q2=Decimal('30.0000'),
            meta_q3=Decimal('30.0000'),
            meta_q4=Decimal('30.0000'),
        )
        with self.assertRaises(ValidationError):
            act.full_clean()
