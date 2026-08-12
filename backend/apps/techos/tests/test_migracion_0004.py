"""
Tests de la data-migration 0004 del núcleo de techos (slice S2).

Cubren la migración 0003 → 0004 (esquema + datos):

- Integridad pre/post: grupos y detalles desde RecursoTecho (sin borrar
  los recursos legacy), bolsas con C8 (monto_vigente = inicial + ajustes,
  nunca null/0), jerárquica (categoría sintética + hojas), monto_total
  recalculado = total_recursos, backfill de gestion_fiscal 1:1.
- Pre-check C2 (fail-loud): aborta con RuntimeError si una gestión tiene
  más de un techo, ANTES del AlterField a no-null + unique.

La migración se ejercita con MigrationExecutor (patrón canónico de Django
para data-migrations): la BD de test se revierte a 0003, se crean datos
legacy con los modelos de ese estado y se re-migra a 0004.
"""
from decimal import Decimal

import pytest
from django.db import connection
from django.db.models import Sum as models_Sum
from django.db.migrations.executor import MigrationExecutor
from datetime import date

TECHOS_0003 = '0003_techopresupuestario_concepto_gastoobligatorio_and_more'
TECHOS_0004_DATOS = '0004_nucleo_techo_datos'


@pytest.fixture
def executor():
    return MigrationExecutor(connection)


def _migrar(target):
    """Aplica la migración con un executor NUEVO por llamada.

    Reutilizar un único MigrationExecutor para varios migrate() en el
    mismo test deja el caché interno `loader.applied_migrations`
    desincronizado con la BD (el loader se construye al instanciar): un
    segundo migrate puede computar un plan vacío (no-op) o backwards
    erróneo y el RunPython nunca se ejecuta. Con un executor fresco por
    llamada el plan siempre refleja el estado real de la BD.
    """
    executor = MigrationExecutor(connection)
    executor.migrate([('techos', target)])
    return executor


def _apps_en(target):
    """Modelos históricos de la migración objetivo (loader fresco)."""
    executor = MigrationExecutor(connection)
    return executor.loader.project_state([('techos', target)]).apps


def _crear_escenario_0003():
    """Crea un escenario legacy en el estado 0003 y devuelve los totales.

    - Techo 2026 con 3 recursos (2 de F1/O1 y 1 de F2/sin organismo),
      un gasto obligatorio activo y 2 distribuciones legacy planas.
    - Total recursos: 400 + 200 + 150 = 750.
    - Total legacy asignado (activo): 300 + 150 = 450; reservas: 20.
    """
    _migrar(TECHOS_0003)
    old_apps = _apps_en(TECHOS_0003)

    Fuente = old_apps.get_model('catalogos', 'FuenteFinanciamiento')
    Organismo = old_apps.get_model('catalogos', 'OrganismoFinanciador')
    Techo = old_apps.get_model('techos', 'Techopresupuestario')
    Recurso = old_apps.get_model('techos', 'RecursoTecho')
    Gasto = old_apps.get_model('techos', 'GastoObligatorio')
    Distribucion = old_apps.get_model('techos', 'DistribucionTecho')

    f1 = Fuente.objects.create(
        codigo='41-113', gestion=2026, denominacion='Coparticipación Tributaria',
        fecha_vigencia_desde=date(2026, 1, 1),
    )
    f2 = Fuente.objects.create(
        codigo='20-210', gestion=2026, denominacion='Recursos Específicos',
        fecha_vigencia_desde=date(2026, 1, 1),
    )
    o1 = Organismo.objects.create(
        codigo='GOB-MUN', gestion=2026, denominacion='Gobierno Municipal',
        fecha_vigencia_desde=date(2026, 1, 1),
    )

    techo = Techo.objects.create(
        gestion=2026, monto_total=Decimal('1000.00'),
        fuente=f1, organismo=o1, descripcion='Techo 2026',
    )
    Recurso.objects.create(
        techo=techo, concepto='Recurso 1', fuente=f1, organismo=o1,
        monto=Decimal('400.00'), rubro='1', rubro_descripcion='Coparticipación',
        orden=0,
    )
    Recurso.objects.create(
        techo=techo, concepto='Recurso 2', fuente=f1, organismo=o1,
        monto=Decimal('200.00'), rubro='2', rubro_descripcion='Otra',
        orden=1,
    )
    Recurso.objects.create(
        techo=techo, concepto='Recurso 3', fuente=f2, organismo=None,
        monto=Decimal('150.00'), rubro='3', rubro_descripcion='Específicos',
        orden=2,
    )
    Gasto.objects.create(
        techo=techo, denominacion='Renta Dignidad', fuente=f1, organismo=o1,
        monto=Decimal('100.00'), activo=True, orden=0,
    )
    d1 = Distribucion.objects.create(
        techo=techo, monto_asignado=Decimal('300.00'),
        monto_reserva=Decimal('20.00'), activo=True, version=1,
    )
    Distribucion.objects.create(
        techo=techo, monto_asignado=Decimal('150.00'),
        monto_reserva=Decimal('0.00'), activo=True, version=1,
    )
    return {
        'techo_id': str(techo.id),
        'f1_id': str(f1.id),
        'f2_id': str(f2.id),
        'o1_id': str(o1.id),
        'd1_id': str(d1.id),
    }


@pytest.mark.django_db(transaction=True)
def test_data_migration_integridad_pre_post():
    escenario = _crear_escenario_0003()

    _migrar(TECHOS_0004_DATOS)
    new_apps = _apps_en(TECHOS_0004_DATOS)

    Techo = new_apps.get_model('techos', 'Techopresupuestario')
    Recurso = new_apps.get_model('techos', 'RecursoTecho')
    Grupo = new_apps.get_model('techos', 'TechoRecursoGrupo')
    Detalle = new_apps.get_model('techos', 'TechoRecursoDetalle')
    Bolsa = new_apps.get_model('techos', 'BolsaPresupuestaria')
    Distribucion = new_apps.get_model('techos', 'DistribucionTecho')
    Gestion = new_apps.get_model('gestion', 'GestionFiscal')

    techo = Techo.objects.get(pk=escenario['techo_id'])

    # -- Backfill gestion_fiscal 1:1 (creada con estado preparacion) --
    assert techo.gestion_fiscal_id is not None
    gestion = Gestion.objects.get(anio=2026)
    assert gestion.estado == 'preparacion'
    assert techo.gestion_fiscal_id == gestion.id
    assert Techo.objects.filter(gestion=2026).count() == 1

    # -- monto_total = SUM(RecursoTecho.monto) (Q1/DD6) --
    assert techo.monto_total == Decimal('750.00')

    # -- RecursoTecho NO se borra (fuente legacy V1) --
    assert Recurso.objects.filter(techo=techo).count() == 3

    # -- Grupos por (fuente, organismo) + detalle por RecursoTecho --
    assert Grupo.objects.filter(techo=techo).count() == 2
    grupo_f1 = Grupo.objects.get(fuente_id=escenario['f1_id'])
    assert grupo_f1.monto == Decimal('600.00')
    grupo_f2 = Grupo.objects.get(fuente_id=escenario['f2_id'])
    assert grupo_f2.monto == Decimal('150.00')
    assert grupo_f2.organismo_id is None
    total_detalles = Detalle.objects.filter(grupo__techo=techo).aggregate(
        total=models_Sum('monto'),
    )['total']
    assert total_detalles == Decimal('750.00')
    assert Detalle.objects.filter(grupo__techo=techo).count() == 3

    # -- Bolsas por (fuente, organismo, tipo_gasto) con C8 --
    bolsas = Bolsa.objects.filter(techo=techo)
    assert bolsas.count() == 2
    for bolsa in bolsas:
        # C8: monto_vigente siempre = inicial + ajustes; nunca null ni 0
        # por omisión cuando hay monto.
        assert bolsa.monto_vigente is not None
        assert bolsa.monto_vigente == bolsa.monto_inicial + bolsa.monto_ajustes
    assert bolsas.aggregate(total=models_Sum('monto_vigente'))['total'] == Decimal('750.00')
    bolsa_f1 = bolsas.get(fuente_id=escenario['f1_id'])
    assert bolsa_f1.monto_inicial == Decimal('600.00')
    assert bolsa_f1.monto_vigente == Decimal('600.00')

    # -- Jerárquica: categoría sintética + una hoja por fila legacy --
    # La sintética es la única fila raíz SIN categoría programática QUE
    # TIENE hijos (las 2 filas legacy planas quedan inactivas, DD4: la
    # jerarquía es la única representación del saldo).
    categorias = Distribucion.objects.filter(
        techo=techo, padre__isnull=True, categoria_programatica__isnull=True,
        hijos__isnull=False,
    ).distinct()
    assert categorias.count() == 1
    categoria = categorias.first()
    assert categoria.monto_asignado == Decimal('450.00')
    assert categoria.monto_reserva == Decimal('20.00')
    hojas = Distribucion.objects.filter(techo=techo, padre=categoria, activo=True)
    assert hojas.count() == 2
    assert hojas.aggregate(total=models_Sum('monto_asignado'))['total'] == Decimal('450.00')
    # Σ legacy pre == Σ hojas post
    assert hojas.aggregate(total=models_Sum('monto_asignado'))['total'] == Decimal('450.00')
    # Las filas legacy planas quedaron inactivas (sin doble conteo C3)
    legacy_inactivas = Distribucion.objects.filter(
        techo=techo, padre__isnull=True, categoria_programatica__isnull=True,
        hijos__isnull=True, activo=False,
    )
    assert legacy_inactivas.count() == 2
    # Única representación activa: sintética + 2 hojas = 3 filas activas
    assert Distribucion.objects.filter(techo=techo, activo=True).count() == 3


@pytest.mark.django_db(transaction=True)
def test_precheck_c2_aborta_con_dos_techos_misma_gestion():
    _migrar(TECHOS_0003)
    old_apps = _apps_en(TECHOS_0003)

    Fuente = old_apps.get_model('catalogos', 'FuenteFinanciamiento')
    Techo = old_apps.get_model('techos', 'Techopresupuestario')

    f1 = Fuente.objects.create(
        codigo='41-113', gestion=2026, denominacion='Coparticipación Tributaria',
        fecha_vigencia_desde=date(2026, 1, 1),
    )
    f2 = Fuente.objects.create(
        codigo='20-210', gestion=2026, denominacion='Recursos Específicos',
        fecha_vigencia_desde=date(2026, 1, 1),
    )
    Techo.objects.create(
        gestion=2026, monto_total=Decimal('500.00'), fuente=f1,
    )
    Techo.objects.create(
        gestion=2026, monto_total=Decimal('300.00'), fuente=f2,
    )

    with pytest.raises(RuntimeError) as excinfo:
        _migrar(TECHOS_0004_DATOS)
    mensaje = str(excinfo.value)
    assert '2026' in mensaje
    assert '2' in mensaje  # reporta el conteo de techos por gestión

    # Restaurar el esquema 0004 completo (el abort deja la BD en el estado
    # 0004_nucleo_techo, sin el AlterField OneToOne de 0004_nucleo_techo_datos)
    # para no contaminar el resto de la suite: se eliminan los techos que
    # provocaron el abort y se re-migra hasta el estado final.
    Techo.objects.all().delete()
    _migrar(TECHOS_0004_DATOS)
    assert Techo.objects.count() == 0
