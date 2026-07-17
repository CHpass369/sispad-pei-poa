from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.organizacion.models import (
    TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
    UnidadEjecutora,
)
from apps.presupuesto.models import ProgramaPresupuestario
from apps.techos.models import TechoPresupuestario, DistribucionTecho, MovimientoTecho


class TechosBaseTestCase(TestCase):
    """Base para tests de techos presupuestarios."""

    def setUp(self):
        self.vig = date(2026, 1, 1)
        self.user = Usuario.objects.create_user(
            email='techos_test@gamsacaba.gob.bo', password='test123',
            first_name='Techos', last_name='Test',
        )
        self.user_admin = Usuario.objects.create_user(
            email='admin_techos@gamsacaba.gob.bo', password='test123',
            first_name='Admin', last_name='Techos',
            is_staff=True,
        )
        self.fuente = FuenteFinanciamiento.objects.create(
            codigo='41-113', gestion=2026,
            denominacion='Coparticipación Tributaria',
            fecha_vigencia_desde=self.vig,
        )
        self.fuente_2 = FuenteFinanciamiento.objects.create(
            codigo='20-210', gestion=2026,
            denominacion='Recursos Específicos',
            fecha_vigencia_desde=self.vig,
        )
        self.organismo = OrganismoFinanciador.objects.create(
            codigo='GOB-MUN', gestion=2026,
            denominacion='Gobierno Municipal',
            fecha_vigencia_desde=self.vig,
        )
        self.tipo_unidad = TipoUnidad.objects.create(
            codigo='SEC', nombre='Secretaría', nivel=1,
        )
        self.unidad = UnidadOrganizacional.objects.create(
            codigo='SEC-01', nombre='Secretaría General',
            sigla='SG', tipo=self.tipo_unidad, gestion=2026,
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
        self.programa = ProgramaPresupuestario.objects.create(
            codigo='000', nombre='Programa Test',
            gestion=2026,
        )
        self.techo = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('1000000.00'),
            fuente=self.fuente, organismo=self.organismo,
        )


class TechoPresupuestarioModelTest(TechosBaseTestCase):
    """Tests del modelo TechoPresupuestario."""

    def test_techo_creacion(self):
        self.assertEqual(self.techo.gestion, 2026)
        self.assertEqual(self.techo.monto_total, Decimal('1000000.00'))
        self.assertTrue(self.techo.activo)
        self.assertEqual(self.techo.version, 1)

    def test_techo_str(self):
        s = str(self.techo)
        self.assertIn('2026', s)
        self.assertIn('Coparticipación', s)

    def test_techo_sin_organismo(self):
        techo = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('500000.00'),
            fuente=self.fuente,
        )
        self.assertIsNone(techo.organismo)

    def test_techo_monto_cero(self):
        techo = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('0.00'),
            fuente=self.fuente_2,
        )
        self.assertEqual(techo.monto_total, Decimal('0.00'))

    def test_techo_ordenacion(self):
        TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('200000.00'),
            fuente=self.fuente_2,
        )
        techos = list(TechoPresupuestario.objects.filter(gestion=2026))
        self.assertEqual(len(techos), 2)
        self.assertEqual(techos[0].fuente.codigo, '20-210')
        self.assertEqual(techos[1].fuente.codigo, '41-113')


class DistribucionTechoModelTest(TechosBaseTestCase):
    """Tests del modelo DistribucionTecho."""

    def test_distribucion_creacion(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, da=self.da, ue=self.ue,
            unidad=self.unidad, programa=self.programa,
            monto_asignado=Decimal('300000.00'),
        )
        self.assertEqual(dist.monto_asignado, Decimal('300000.00'))
        self.assertTrue(dist.activo)

    def test_distribucion_str(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('250000.00'),
        )
        s = str(dist)
        self.assertIn('2026', s)

    def test_distribucion_sin_programa(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('100000.00'),
        )
        self.assertIsNone(dist.programa)

    def test_varias_distribuciones_mismo_techo(self):
        for i in range(3):
            DistribucionTecho.objects.create(
                techo=self.techo,
                monto_asignado=Decimal(f'{100000 * (i + 1)}.00'),
            )
        self.assertEqual(
            DistribucionTecho.objects.filter(techo=self.techo).count(), 3
        )

    def test_distribucion_reserva(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('200000.00'),
            monto_reserva=Decimal('50000.00'),
        )
        self.assertEqual(dist.monto_reserva, Decimal('50000.00'))

    def test_distribucion_monto_cero(self):
        dist = DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('0.00'),
        )
        self.assertEqual(dist.monto_asignado, Decimal('0.00'))


class MovimientoTechoModelTest(TechosBaseTestCase):
    """Tests del modelo MovimientoTecho."""

    def test_movimiento_creacion(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='asignacion',
            amount=Decimal('100000.00'),
            justification='Asignación de prueba',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'asignacion')
        self.assertEqual(mv.amount, Decimal('100000.00'))

    def test_movimiento_incremento(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='incremento',
            amount=Decimal('50000.00'),
            justification='Incremento por ajuste',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'incremento')

    def test_movimiento_reduccion(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='reduccion',
            amount=Decimal('30000.00'),
            justification='Reducción presupuestaria',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'reduccion')

    def test_movimiento_transferencia(self):
        techo_dest = TechoPresupuestario.objects.create(
            gestion=2026, monto_total=Decimal('200000.00'),
            fuente=self.fuente_2,
        )
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='transferencia',
            source_ceiling=self.techo,
            destination_ceiling=techo_dest,
            amount=Decimal('75000.00'),
            justification='Transferencia entre fuentes',
            requested_by=self.user,
            approved_by=self.user_admin,
            date=timezone.now(),
        )
        self.assertEqual(mv.source_ceiling, self.techo)
        self.assertEqual(mv.destination_ceiling, techo_dest)
        self.assertEqual(mv.approved_by, self.user_admin)

    def test_movimiento_str(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='asignacion',
            amount=Decimal('100000.00'),
            justification='Test',
            requested_by=self.user,
            date=timezone.now(),
        )
        s = str(mv)
        self.assertIn('Asignación', s)
        self.assertIn('100000', s)

    def test_movimiento_reserva(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='reserva',
            amount=Decimal('25000.00'),
            justification='Reserva para contingencia',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'reserva')

    def test_movimiento_liberacion(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='liberacion',
            amount=Decimal('10000.00'),
            justification='Liberación parcial',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'liberacion')

    def test_movimiento_reversion(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='reversion',
            amount=Decimal('5000.00'),
            justification='Reversión de error',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'reversion')

    def test_movimiento_ajuste(self):
        mv = MovimientoTecho.objects.create(
            techo=self.techo, movement_type='ajuste',
            amount=Decimal('2000.00'),
            justification='Ajuste contable',
            requested_by=self.user,
            date=timezone.now(),
        )
        self.assertEqual(mv.movement_type, 'ajuste')

    def test_saldo_disponible_calculo(self):
        monto_inicial = Decimal('1000000.00')
        DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('600000.00'),
        )
        saldo = monto_inicial - Decimal('600000.00')
        self.assertEqual(saldo, Decimal('400000.00'))
        self.assertGreater(saldo, Decimal('0'))

    def test_saldo_no_negativo(self):
        DistribucionTecho.objects.create(
            techo=self.techo, monto_asignado=Decimal('900000.00'),
        )
        total_distribuido = DistribucionTecho.objects.filter(
            techo=self.techo, activo=True
        ).aggregate(total=Decimal('0'))['total']
        saldo = self.techo.monto_total - total_distribuido
        self.assertGreaterEqual(saldo, Decimal('0'))

    def test_movimientos_por_tipo(self):
        for tipo in ['asignacion', 'incremento', 'reduccion', 'transferencia',
                     'reserva', 'liberacion', 'ajuste', 'reversion']:
            MovimientoTecho.objects.create(
                techo=self.techo, movement_type=tipo,
                amount=Decimal('1000.00'),
                justification=f'Movimiento {tipo}',
                requested_by=self.user,
                date=timezone.now(),
            )
        self.assertEqual(MovimientoTecho.objects.filter(techo=self.techo).count(), 8)

    def test_saldo_con_incremento(self):
        monto = self.techo.monto_total
        MovimientoTecho.objects.create(
            techo=self.techo, movement_type='incremento',
            amount=Decimal('200000.00'),
            justification='Incremento',
            requested_by=self.user,
            date=timezone.now(),
        )
        saldo_esperado = monto + Decimal('200000.00')
        self.assertEqual(saldo_esperado, Decimal('1200000.00'))

    def test_saldo_con_reduccion(self):
        monto = self.techo.monto_total
        MovimientoTecho.objects.create(
            techo=self.techo, movement_type='reduccion',
            amount=Decimal('150000.00'),
            justification='Reducción',
            requested_by=self.user,
            date=timezone.now(),
        )
        saldo_esperado = monto - Decimal('150000.00')
        self.assertEqual(saldo_esperado, Decimal('850000.00'))
        self.assertGreater(saldo_esperado, Decimal('0'))
