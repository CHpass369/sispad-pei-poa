"""Dos técnicos validando a la vez no pueden perder plata.

El volcado al gasto lee el monto de la fila FF/OF, le suma lo del proyecto y lo
vuelve a escribir. Bajo `read committed` —el nivel por defecto de PostgreSQL—
dos transacciones simultáneas leen el mismo valor y la segunda pisa a la
primera: uno de los dos montos desaparece sin error y sin rastro.

`@transaction.atomic` no protege de esto: da atomicidad, no aislamiento contra
lecturas obsoletas. Lo que serializa a la priorización consigo misma es el
candado que `_apertura_de` toma sobre la categoría programática, aguas arriba
de la fila de monto.

Hay una carrera más, y es peor que perder un monto: `Apertura` no tiene índice
único, así que sin ese candado los dos hilos no encuentran nada, los dos crean,
y la categoría termina duplicada en el Presupuesto General de Gastos con la
plata partida en dos filas. El índice no se puede agregar porque una misma
categoría admite varias aperturas a propósito.

El test corre sobre `TransactionTestCase` porque necesita commits reales: los
hilos tienen que ver lo que el otro escribió, y `TestCase` envuelve todo en una
transacción que nadie más puede leer.
"""
import threading
import time
from datetime import date
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase

from apps.budget.models import (
    Apertura, AperturaFuente, CategoriaProgramaticaTecho, RangoProgramaDirectriz,
)
from apps.catalogos.models import FuenteFinanciamiento, OrganismoFinanciador
from apps.gestion.models import GestionFiscal
from apps.priorizacion import materializacion
from apps.priorizacion.models import ActaPriorizacion, ProyectoPriorizado
from apps.territorio.models import Distrito

CODIGO = '180 08620281200000 000'


class VolcadoConcurrenteTests(TransactionTestCase):
    """La suma de dos actas simultáneas sobre la misma fila tiene que cerrar."""

    def setUp(self):
        self.gestion, _ = GestionFiscal.objects.get_or_create(
            anio=2027, defaults={'estado': 'HABILITADA'})
        RangoProgramaDirectriz.objects.get_or_create(
            gestion=2027, desde=180, hasta=189,
            defaults={'denominacion': 'GESTIÓN DE CAMINOS VECINALES',
                      'finalidad_funcion': '1.1.1', 'sector_economico': '14'})
        catalogo = dict(gestion=self.gestion, fecha_vigencia_desde=date(2027, 1, 1))
        self.ff = FuenteFinanciamiento.objects.create(
            codigo='41', denominacion='Transferencias T.G.N.', **catalogo)
        self.of = OrganismoFinanciador.objects.create(
            codigo='113', denominacion='TGN - Coparticipación', **catalogo)
        CategoriaProgramaticaTecho.objects.create(
            gestion=self.gestion, codigo=CODIGO, nivel='PROYECTO',
            denominacion='IMPLEM. PAVIMENTO FLEXIBLE')
        self.distrito = Distrito.objects.create(codigo='D2', nombre='DISTRITO 2')

    def _acta(self, otb, monto):
        acta = ActaPriorizacion.objects.create(
            gestion=2027, distrito=self.distrito, otb=otb,
            presidente='JUAN', responsable_registro='ANA', fecha=date(2026, 9, 3))
        ProyectoPriorizado.objects.create(
            acta=acta, orden=1, nombre='IMPLEM. PAVIMENTO FLEXIBLE',
            sisin='08620281200000', categoria_programatica=CODIGO,
            monto=Decimal(monto), fuente=self.ff, organismo=self.of)
        return acta

    def _validar_en_paralelo(self, actas):
        """Cada hilo materializa un acta; ambos apuntan a la misma fila FF/OF."""
        errores = []
        listo = threading.Barrier(len(actas))

        def trabajar(acta):
            try:
                listo.wait(timeout=10)          # arrancan juntos
                materializacion.materializar_acta(acta)
            except Exception as exc:            # se reporta, no se traga
                errores.append(exc)
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=trabajar, args=(a,)) for a in actas]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=30)
        self.assertEqual(errores, [], f'los hilos fallaron: {errores}')
        self.assertFalse(any(h.is_alive() for h in hilos), 'un hilo quedó colgado')

    def test_dos_actas_simultaneas_suman_las_dos(self):
        """Sin el candado de la categoría este test cae con dos filas de gasto."""
        original = materializacion._fila_bloqueada

        def con_pausa(*args, **kwargs):
            # Ensancha a propósito la ventana entre leer y escribir. Con el
            # candado tomado aguas arriba, el segundo hilo ni llega hasta acá.
            fila = original(*args, **kwargs)
            time.sleep(0.6)
            return fila

        materializacion._fila_bloqueada = con_pausa
        try:
            self._validar_en_paralelo([self._acta('OTB UNO', '50000'),
                                       self._acta('OTB DOS', '30000')])
        finally:
            materializacion._fila_bloqueada = original

        filas = AperturaFuente.objects.filter(
            allocation__categoria__codigo=CODIGO, fuente=self.ff, organismo=self.of)
        self.assertEqual(filas.count(), 1, 'debe haber una sola fila para el par FF/OF')
        self.assertEqual(filas.first().monto, Decimal('80000'))

    def test_cada_proyecto_recuerda_lo_que_puso(self):
        """El rastro tiene que quedar en los dos, no solo en el que ganó."""
        self._validar_en_paralelo([self._acta('OTB UNO', '50000'),
                                   self._acta('OTB DOS', '30000')])

        puestos = sorted(
            p.monto_materializado
            for p in ProyectoPriorizado.objects.select_related('acta'))
        self.assertEqual(puestos, [Decimal('30000'), Decimal('50000')])
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation__categoria__codigo=CODIGO).monto, Decimal('80000'))

    def test_desvalidar_concurrente_no_deja_monto_de_mas(self):
        """Revertir las dos a la vez tiene que dejar la fila en cero, o borrada."""
        actas = [self._acta('OTB UNO', '50000'), self._acta('OTB DOS', '30000')]
        for a in actas:
            materializacion.materializar_acta(a)
        self.assertEqual(
            AperturaFuente.objects.get(
                allocation__categoria__codigo=CODIGO).monto, Decimal('80000'))

        errores = []
        listo = threading.Barrier(2)

        def revertir(acta):
            try:
                listo.wait(timeout=10)
                materializacion.desmaterializar_acta(acta)
            except Exception as exc:
                errores.append(exc)
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=revertir, args=(a,)) for a in actas]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=30)
        self.assertEqual(errores, [], f'los hilos fallaron: {errores}')

        restante = AperturaFuente.objects.filter(
            allocation__categoria__codigo=CODIGO).first()
        self.assertIsNone(restante, 'la fila debía suprimirse al quedar en cero')
        self.assertFalse(Apertura.objects.filter(categoria__codigo=CODIGO).exists())
