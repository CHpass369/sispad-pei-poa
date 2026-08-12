"""
Data-migration 0004 del núcleo de techos (slice S2, design §5).

Ejecuta, dentro de transaction.atomic y en modo fail-loud:

1. **Pre-check 1:1 techo↔gestión (C2)**: COUNT(TechoPresupuestario)
   agrupado por gestion; si alguna gestión tiene más de un techo, aborta
   con RuntimeError + reporte ANTES del AlterField a no-null + unique.
2. **Backfill gestion_fiscal**: get(anio=gestion) o crear con estado
   'preparacion'; luego el AlterField final a OneToOneField no-null
   (unique) como operación separada de esta migración.
3. **monto_total = SUM(RecursoTecho.monto)** (Q1/DD6).
4. **Grupos**: TechoRecursoGrupo por (fuente, organismo) + un
   TechoRecursoDetalle por RecursoTecho; los RecursoTecho NO se borran
   (fuente legacy V1 read-only).
5. **Bolsas**: por (fuente, organismo, tipo_gasto); tipo_gasto = CORRIENTE
   por defecto (D10; la clasificación real llega por API en S4).
   monto_inicial = Σ del grupo si el mapeo es 1:1, 0 si ambiguo; en toda
   creación monto_vigente = monto_inicial + monto_ajustes (C8), nunca
   null ni 0 por omisión.
6. **Plano → jerárquico (DD4)**: categoría sintética 'MIGRACION LEGACY
   0004' (bolsa = única candidata si el techo tiene una sola bolsa, si no
   null) con monto = Σ legacy, y una hoja por fila legacy (padre =
   categoría sintética).
7. **Validación post (fail-loud)**: Σ legacy pre == Σ hojas post;
   Σ recursos == Σ grupos; monto_total == total_recursos; Σ bolsas.vigente
   == Σ grupos 1:1 (la diferencia esperada de bolsas ambiguas se reporta
   explícitamente, nunca en silencio). Cualquier otra diferencia →
   RuntimeError (nada se aplica parcialmente).

Reversión: migrate techos 0003 + drop de objetos nuevos (aditivo).
"""
from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models, transaction
from django.db.models import Count, Sum

NOMBRE_CATEGORIA_SINTETICA = 'MIGRACION LEGACY 0004'


def _resolver_constraints_diferidos():
    """Resuelve los eventos de triggers diferidos pendientes.

    Las FKs del proyecto son DEFERRABLE INITIALLY DEFERRED (PostgreSQL).
    Los INSERTs de la migración encolan eventos de RI que se mantienen
    pendientes hasta el commit; el AlterField a OneToOne no-null que
    cierra esta migración (misma transacción atómica) no puede correr
    con eventos pendientes ("cannot ALTER TABLE ... pending trigger
    events", PG15+). SET CONSTRAINTS ALL IMMEDIATE los dispara sin
    comprometer la transacción (se conserva el rollback total, §5).
    """
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')


def _suma(queryset, campo):
    """Suma Decimal segura (None → 0)."""
    total = queryset.aggregate(t=Sum(campo))['t']
    return total if total is not None else Decimal('0.00')


def _tipo_gasto_de_recurso(recurso):
    """Deriva CORRIENTE/INVERSION por ObjetoGasto cuando sea posible.

    Los recursos legacy (0003) no traen objeto_gasto; CORRIENTE por
    defecto (D10) y queda `sin_clasificar` visible. La clasificación real
    la hace el usuario vía la API de clasificación (S4), no la migración.
    """
    return 'CORRIENTE'


def migrar_nucleo_techo(apps, schema_editor):
    Techo = apps.get_model('techos', 'Techopresupuestario')
    Recurso = apps.get_model('techos', 'RecursoTecho')
    Grupo = apps.get_model('techos', 'TechoRecursoGrupo')
    Detalle = apps.get_model('techos', 'TechoRecursoDetalle')
    Bolsa = apps.get_model('techos', 'BolsaPresupuestaria')
    Distribucion = apps.get_model('techos', 'DistribucionTecho')
    Gestion = apps.get_model('gestion', 'GestionFiscal')

    reporte = []
    errores = []

    with transaction.atomic():
        # ------------------------------------------------------------------
        # 1) Pre-check 1:1 techo ↔ gestión (C2) — fail-loud con reporte
        # ------------------------------------------------------------------
        techos_por_gestion = (
            Techo.objects.values('gestion')
            .annotate(n=Count('id'))
            .filter(n__gt=1)
            .order_by('gestion')
        )
        if techos_por_gestion.exists():
            detalle = []
            for fila in techos_por_gestion:
                ids = list(
                    Techo.objects.filter(gestion=fila['gestion'])
                    .values_list('id', flat=True)
                )
                detalle.append(
                    f"gestion {fila['gestion']}: {fila['n']} techos ({ids})"
                )
            raise RuntimeError(
                'ABORTA migración 0004 (pre-check C2): la relación '
                'techo↔gestión debe ser 1:1 (V1 permitía varios techos por '
                'gestión). No se fusiona ni selecciona un techo '
                'silenciosamente. Reporte: ' + '; '.join(detalle)
            )

        # ------------------------------------------------------------------
        # 2) Backfill gestion_fiscal (get por anio o crear en preparacion)
        # ------------------------------------------------------------------
        for techo in Techo.objects.all().order_by('id'):
            gestion, _ = Gestion.objects.get_or_create(
                anio=techo.gestion,
                defaults={'estado': 'preparacion'},
            )
            if techo.gestion_fiscal_id != gestion.id:
                techo.gestion_fiscal = gestion
                techo.save(update_fields=['gestion_fiscal', 'updated_at'])

        # ------------------------------------------------------------------
        # 3)-5) monto_total, grupos+detalles y bolsas, por techo
        # ------------------------------------------------------------------
        totales_legacy_pre = {}   # techo_id -> Σ monto_asignado legacy activo
        montos_grupos_ambiguos = {}  # techo_id -> Decimal

        for techo in Techo.objects.all().order_by('id'):
            tid = str(techo.id)

            # 3) monto_total = SUM(RecursoTecho.monto) (Q1/DD6)
            total_recursos = _suma(Recurso.objects.filter(techo=techo), 'monto')
            if techo.monto_total != total_recursos:
                reporte.append(
                    f'techo {tid}: monto_total {techo.monto_total} normalizado '
                    f'→ {total_recursos} (= total_recursos, Q1/DD6)'
                )
                techo.monto_total = total_recursos
                techo.save(update_fields=['monto_total', 'updated_at'])

            # 4) Grupos por (fuente, organismo) + detalle por RecursoTecho
            recursos = list(
                Recurso.objects.filter(techo=techo).order_by('orden', 'id')
            )
            grupos = {}  # (fuente_id, organismo_id) -> grupo
            for recurso in recursos:
                clave = (str(recurso.fuente_id), str(recurso.organismo_id or ''))
                if clave not in grupos:
                    grupos[clave] = Grupo.objects.create(
                        techo=techo,
                        fuente_id=recurso.fuente_id,
                        organismo_id=recurso.organismo_id,
                        monto=Decimal('0.00'),
                    )
                grupos[clave].monto += recurso.monto
                Detalle.objects.create(
                    grupo=grupos[clave],
                    rubro=recurso.rubro,
                    concepto=recurso.concepto,
                    monto=recurso.monto,
                )
            for grupo in grupos.values():
                grupo.save(update_fields=['monto', 'updated_at'])

            # 5) Bolsas por (fuente, organismo, tipo_gasto) con C8
            tipos_por_clave = {}
            for recurso in recursos:
                clave = (str(recurso.fuente_id), str(recurso.organismo_id or ''))
                tipos_por_clave.setdefault(clave, set()).add(
                    _tipo_gasto_de_recurso(recurso),
                )
            bolsa_por_clave = {}
            montos_ambiguos = Decimal('0.00')
            for clave, tipos in tipos_por_clave.items():
                fuente_id, organismo_id = clave
                organismo_db = None if organismo_id == '' else organismo_id
                if len(tipos) == 1:
                    # 1:1 grupo → bolsa: monto_inicial = Σ del grupo
                    monto_inicial = grupos[clave].monto
                    tipo_gasto = tipos.pop()
                else:
                    # Mapeo ambiguo: bolsa 0; el fixture/comando dev ajusta
                    # después; la integridad se preserva porque
                    # techo_distribuible no depende de bolsas.
                    monto_inicial = Decimal('0.00')
                    tipo_gasto = 'CORRIENTE'
                    montos_ambiguos += grupos[clave].monto
                    reporte.append(
                        f'techo {tid}: grupo (fuente {fuente_id}, organismo '
                        f'{organismo_id}) con tipos {sorted(tipos)} → bolsa '
                        f'ambiguo con monto_inicial 0 (diferencia esperada '
                        f'Bs {montos_ambiguos} se reporta en la validación)'
                    )
                bolsa = Bolsa.objects.create(
                    techo=techo,
                    fuente_id=fuente_id,
                    organismo_id=organismo_db,
                    tipo_gasto=tipo_gasto,
                    monto_inicial=monto_inicial,
                    monto_ajustes=Decimal('0.00'),
                    # C8: monto_vigente = monto_inicial + monto_ajustes
                    # SIEMPRE; nunca null ni 0 por omisión.
                    monto_vigente=monto_inicial + Decimal('0.00'),
                    monto_reservado=Decimal('0.00'),
                )
                bolsa_por_clave[clave] = bolsa
            montos_grupos_ambiguos[tid] = montos_ambiguos

            # 6) Plano → jerárquico (DD4): categoría sintética + hojas
            legacy = list(
                Distribucion.objects.filter(techo=techo, activo=True)
                .order_by('id')
            )
            totales_legacy_pre[tid] = _suma(
                Distribucion.objects.filter(techo=techo, activo=True),
                'monto_asignado',
            )
            if not legacy:
                continue
            bolsa_candidata = None
            bolsas_techo = Bolsa.objects.filter(techo=techo)
            if bolsas_techo.count() == 1:
                bolsa_candidata = bolsas_techo.first()
            categoria = Distribucion.objects.create(
                techo=techo,
                bolsa=bolsa_candidata,
                categoria_programatica=None,
                monto_asignado=_suma(
                    Distribucion.objects.filter(techo=techo, activo=True),
                    'monto_asignado',
                ),
                monto_reserva=_suma(
                    Distribucion.objects.filter(techo=techo, activo=True),
                    'monto_reserva',
                ),
                activo=True,
                version=1,
            )
            reporte.append(
                f'techo {tid}: categoría sintética "{NOMBRE_CATEGORIA_SINTETICA}" '
                f'Bs {categoria.monto_asignado} '
                f'({"bolsa " + str(bolsa_candidata.id) if bolsa_candidata else "sin bolsa"})'
            )
            for fila in legacy:
                Distribucion.objects.create(
                    techo=techo,
                    padre=categoria,
                    bolsa=bolsa_candidata,
                    da_id=fila.da_id,
                    ue_id=fila.ue_id,
                    unidad_id=fila.unidad_id,
                    programa_id=fila.programa_id,
                    monto_asignado=fila.monto_asignado,
                    monto_reserva=fila.monto_reserva,
                    activo=fila.activo,
                    version=fila.version,
                )
            # Las filas legacy planas pasan a inactivas: la jerarquía
            # sintética + hojas es la ÚNICA representación del saldo (DD4
            # "preserva saldos exactos"). Si quedaran activas, el guard C3
            # y los agregados del motor (Σ hojas activas) contarían el
            # mismo peso dos veces (una vía fila legacy y otra vía hoja).
            Distribucion.objects.filter(
                techo=techo, pk__in=[fila.pk for fila in legacy],
            ).update(activo=False)

        # ------------------------------------------------------------------
        # 7) Validación post (fail-loud)
        # ------------------------------------------------------------------
        for techo in Techo.objects.all().order_by('id'):
            tid = str(techo.id)

            recursos = _suma(Recurso.objects.filter(techo=techo), 'monto')
            grupos_total = _suma(Grupo.objects.filter(techo=techo), 'monto')
            if recursos != grupos_total:
                errores.append(
                    f'techo {tid}: Σ recursos {recursos} != Σ grupos '
                    f'{grupos_total}'
                )
            if techo.monto_total != recursos:
                errores.append(
                    f'techo {tid}: monto_total {techo.monto_total} != '
                    f'total_recursos {recursos}'
                )

            hojas = _suma(
                Distribucion.objects.filter(
                    techo=techo, activo=True, padre__isnull=False,
                ),
                'monto_asignado',
            )
            if hojas != totales_legacy_pre[tid]:
                errores.append(
                    f'techo {tid}: Σ hojas {hojas} != Σ legacy pre '
                    f'{totales_legacy_pre[tid]}'
                )

            bolsas = Bolsa.objects.filter(techo=techo)
            if bolsas.exists():
                suma_vigente = _suma(bolsas, 'monto_vigente')
                esperado = grupos_total - montos_grupos_ambiguos[tid]
                if suma_vigente != esperado:
                    errores.append(
                        f'techo {tid}: Σ bolsas.monto_vigente {suma_vigente} '
                        f'!= Σ grupos 1:1 {esperado} (grupos ambiguos '
                        f'{montos_grupos_ambiguos[tid]})'
                    )
                elif montos_grupos_ambiguos[tid] > 0:
                    reporte.append(
                        f'techo {tid}: diferencia esperada de bolsas '
                        f'ambiguas Bs {montos_grupos_ambiguos[tid]} '
                        f'(grupos sin mapeo 1:1 a bolsa)'
                    )

        if errores:
            raise RuntimeError(
                'ABORTA validación post de la migración 0004: '
                + '; '.join(errores)
            )

        # Los INSERTs encolaron eventos de triggers diferidos (FKs
        # DEFERRABLE INITIALLY DEFERRED); el AlterField a OneToOne que
        # cierra la migración no puede correr con eventos pendientes.
        _resolver_constraints_diferidos()

        if reporte:
            print('[migración 0004 núcleo techo] reporte:')
            for linea in reporte:
                print(f'  - {linea}')


class Migration(migrations.Migration):

    dependencies = [
        ('techos', '0004_nucleo_techo'),
    ]

    operations = [
        migrations.RunPython(migrar_nucleo_techo, migrations.RunPython.noop),
        # Estado final R2.1: FK → OneToOne no-null (unique). Solo se llega
        # aquí si el pre-check C2 (1:1) pasó y el backfill completó.
        migrations.AlterField(
            model_name='techopresupuestario',
            name='gestion_fiscal',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='techo',
                to='gestion.gestionfiscal',
                verbose_name='Gestión fiscal',
            ),
        ),
    ]
