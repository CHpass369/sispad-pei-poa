"""PIP-DB-003: el seed normativo T4 (0003) es aditivo e idempotente.

La migración 0003 (ya aplicada) siembra las versiones oficiales de
clasificadores 2026 sin pisar lo preexistente. Este test valida ese contrato
contra el esquema actual (gestion FK desde la 0007; el flujo físico
forward/reverse de la cadena completa ya no es viable — ver FINAL REPORT
PIP-DB-003).
"""
from datetime import date

from django.test import TestCase

from apps.catalogos.models import (
    VersionClasificador, ClasificadorGeograficoPresupuestario,
)
from apps.gestion.models import GestionFiscal


class TestSeedNormativoClasificadores2026(TestCase):
    # Este test afirma sobre datos que sembraron las migraciones, y un
    # TransactionTestCase hermano los borra: su teardown hace TRUNCATE de
    # toda la base (comprobado: catalogo_version_clasificador queda en 0
    # filas). Con xdist, que eso ocurra o no depende de en que worker caiga
    # cada modulo, asi que el test pasaba o fallaba segun el reparto.
    #
    # serialized_rollback le pide a Django que restaure el estado inicial
    # antes de correr. Es el mecanismo previsto justamente para esto.
    serialized_rollback = True

    def test_seed_0003_aplicado_convive_con_preexistentes_y_conserva_propiedades(self):
        gf = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'abierta'},
        )[0]

        # Preexistente: no se pisa (vigente=False para no colisionar con el
        # seed vigente del mismo tipo+gestión).
        VersionClasificador.objects.create(
            tipo=VersionClasificador.TIPO_FUENTE_FINANCIAMIENTO,
            gestion=gf,
            codigo_fuente='PREEXISTENTE-UNO',
            vigente=False,
            norma='NORMA PREEXISTENTE INTACTA',
            fecha_norma=date(2025, 1, 1),
            procedencia_normativa='PROCEDENCIA PREEXISTENTE INTACTA',
            hash_fuente='9' * 64,
            clasificacion_fuente=VersionClasificador.FUENTE_OFICIAL,
        )

        # Los seeds de la 0003 existen y conservan sus propiedades.
        institucional = VersionClasificador.objects.get(
            codigo_fuente='SEED-T4-RM249-INSTITUCIONAL'
        )
        assert institucional.vigente is True
        assert (
            VersionClasificador.objects.filter(
                codigo_fuente='SEED-T4-RM249-FUENTE_FINANCIAMIENTO', vigente=True
            ).count() == 1
        )
        assert (
            VersionClasificador.objects.filter(
                codigo_fuente='SEED-T4-CATEGORIA-INCIERTA', vigente=False
            ).count() == 1
        )
        assert (
            ClasificadorGeograficoPresupuestario.objects.filter(
                codigo_fuente='3|5|1'
            ).count() == 1
        )

        # Convivencia: el preexistente no fue tocado por el seed.
        preexistente = VersionClasificador.objects.get(
            codigo_fuente='PREEXISTENTE-UNO'
        )
        assert preexistente.norma == 'NORMA PREEXISTENTE INTACTA'
        assert preexistente.clasificacion_fuente == VersionClasificador.FUENTE_OFICIAL

    def test_reejecutar_seed_no_duplica(self):
        """La 0003 usa get_or_create: re-aplicar su lógica no duplica."""
        gf = GestionFiscal.objects.get_or_create(
            anio=2026, defaults={'estado': 'abierta'},
        )[0]
        inicial = VersionClasificador.objects.filter(
            codigo_fuente__startswith='SEED-T4-'
        ).count()
        # Simula una re-aplicación idempotente del seed.
        for codigo, vigente in (
            ('SEED-T4-RM249-INSTITUCIONAL', True),
            ('SEED-T4-CATEGORIA-INCIERTA', False),
        ):
            VersionClasificador.objects.get_or_create(
                codigo_fuente=codigo,
                defaults={'tipo': VersionClasificador.TIPO_INSTITUCIONAL,
                          'gestion': gf, 'vigente': vigente,
                          'hash_fuente': '9' * 64,
                          'clasificacion_fuente': VersionClasificador.FUENTE_OFICIAL},
            )
        assert (
            VersionClasificador.objects.filter(
                codigo_fuente__startswith='SEED-T4-'
            ).count() == inicial
        )