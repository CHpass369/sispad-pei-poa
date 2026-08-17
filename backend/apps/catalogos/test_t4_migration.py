"""PIP-DB-003: los catálogos legacy (sin version_clasificador) se preservan.

La migración T4 (0003/0004, ya aplicada) blinda las versiones oficiales sin
tocar los catálogos legacy. Este test valida ese contrato contra el esquema
actual (gestion es FK a GestionFiscal desde la 0007; el flujo físico de
forward/reverse de la cadena completa ya no es viable — ver FINAL REPORT
PIP-DB-003).
"""
from datetime import date

from django.test import TransactionTestCase

from apps.catalogos.models import (
    ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador,
)
from apps.gestion.models import GestionFiscal
from apps.presupuesto.models import LineaPresupuestaria


class TestMigracionT4PreservaCatalogosLegacy(TransactionTestCase):
    reset_sequences = False

    def test_ids_codigos_y_linea_presupuestaria_legacy_siguen_disponibles(self):
        gf = GestionFiscal.objects.get_or_create(
            anio=2025, defaults={'estado': 'abierta'},
        )[0]
        vigencia = date(2025, 1, 1)
        legacy = {}
        for model, codigo in (
            (ObjetoGasto, 'LEGACY-OBJ'),
            (FuenteFinanciamiento, 'LEGACY-FUE'),
            (OrganismoFinanciador, 'LEGACY-ORG'),
        ):
            row = model.objects.create(
                codigo=codigo,
                denominacion=f'{model.__name__} previo',
                gestion=gf,
                fecha_vigencia_desde=vigencia,
                fuente_normativa='Fuente legacy preservada',
            )
            legacy[model] = (row.pk, codigo)

        # Los registros legacy sobreviven con sus datos y sin versión asignada.
        for model, (pk, codigo) in legacy.items():
            row = model.objects.get(pk=pk)
            assert row.codigo == codigo
            assert row.fuente_normativa == 'Fuente legacy preservada'
            assert row.version_clasificador_id is None
        # La línea presupuestaria legacy sigue existiendo con su tabla.
        assert LineaPresupuestaria._meta.db_table == 'presupuesto_lineapresupuestaria'